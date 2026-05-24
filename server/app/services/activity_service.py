from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.activity import Activity
from app.db.models.user import User
from app.db.schemas.activity import (
    ActivityCreateRequest,
    ActivityResponse,
    ActivityUpdate,
)
from app.db.schemas.common import ApiResponse
from app.repositories.activity_repository import ActivityRepository
from app.repositories.channel_repository import ChannelRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.realtime.connection_manager import realtime_manager


def _enrich_activity(activity: Activity) -> ActivityResponse:
    resp = ActivityResponse.model_validate(activity)
    resp.actor_name = activity.actor.full_name if activity.actor else None
    return resp


class ActivityService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.activity_repository = ActivityRepository(db)
        self.channel_repository = ChannelRepository(db)
        self.workspace_repository = WorkspaceRepository(db)

    def _require_workspace_member(self, current_user: User, channel_id) -> None:
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        workspaces = self.workspace_repository.list_for_user(current_user.id)
        if not any(ws.id == channel.workspace_id for ws in workspaces):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this workspace",
            )

    def create_activity(
        self,
        current_user: User,
        channel_id,
        payload: ActivityCreateRequest,
    ) -> ApiResponse[ActivityResponse]:
        self._require_workspace_member(current_user=current_user, channel_id=channel_id)
        channel = self.channel_repository.get_by_id(channel_id)
        assert channel is not None

        if payload.activity_type != "chat_message":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only chat_message is supported for now",
            )

        activity = Activity(
            workspace_id=channel.workspace_id,
            channel_id=channel_id,
            actor_id=current_user.id,
            activity_type=payload.activity_type,
            content=payload.content,
            meta_data=payload.meta_data,
            parent_activity_id=payload.parent_activity_id,
        )
        self.activity_repository.create(activity)

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to create activity",
            ) from exc

        self.db.refresh(activity)
        enriched = _enrich_activity(activity)
        # Broadcast only after persistence.
        event = {
            "type": "activity_created",
            "channel_id": str(channel_id),
            "workspace_id": str(activity.workspace_id),
            "activity": enriched.model_dump(),
        }
        # ActivityService is sync (runs in threadpool); broadcast best-effort.
        try:
            import anyio

            anyio.from_thread.run(realtime_manager.broadcast_to_channel, channel_id, event)
        except Exception:
            pass
        return ApiResponse(
            success=True,
            message="Activity created successfully",
            data=enriched,
        )

    def list_channel_activities(
        self,
        current_user: User,
        channel_id,
        limit: int,
        offset: int,
    ) -> ApiResponse[list[ActivityResponse]]:
        self._require_workspace_member(current_user=current_user, channel_id=channel_id)
        activities = self.activity_repository.list_for_channel(
            channel_id=channel_id,
            limit=limit,
            offset=offset,
        )
        return ApiResponse(
            success=True,
            message="Activities retrieved successfully",
            data=[_enrich_activity(a) for a in activities],
        )

    def get_activity(
        self,
        current_user: User,
        activity_id,
    ) -> ApiResponse[ActivityResponse]:
        activity = self.activity_repository.get_by_id(activity_id)
        if not activity or activity.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Activity not found")
        self._require_workspace_member(current_user=current_user, channel_id=activity.channel_id)
        return ApiResponse(
            success=True,
            message="Activity retrieved successfully",
            data=_enrich_activity(activity),
        )

    def update_activity(
        self,
        current_user: User,
        activity_id,
        payload: ActivityUpdate,
    ) -> ApiResponse[ActivityResponse]:
        activity = self.activity_repository.get_by_id(activity_id)
        if not activity or activity.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Activity not found")
        self._require_workspace_member(current_user=current_user, channel_id=activity.channel_id)

        if activity.actor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the activity author can update this activity",
            )

        if payload.content is not None:
            activity.content = payload.content
        if payload.meta_data is not None:
            activity.meta_data = payload.meta_data

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Unable to update activity") from exc

        self.db.refresh(activity)
        return ApiResponse(
            success=True,
            message="Activity updated successfully",
            data=_enrich_activity(activity),
        )

    def delete_activity(
        self,
        current_user: User,
        activity_id,
    ) -> ApiResponse[None]:
        activity = self.activity_repository.get_by_id(activity_id)
        if not activity or activity.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Activity not found")
        self._require_workspace_member(current_user=current_user, channel_id=activity.channel_id)

        if activity.actor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the activity author can delete this activity",
            )

        ActivityRepository.soft_delete(activity, deleted_at=datetime.now(timezone.utc))
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Unable to delete activity") from exc

        return ApiResponse(success=True, message="Activity deleted successfully", data=None)
