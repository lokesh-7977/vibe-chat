import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.activity import Activity
from app.db.models.channel import Channel
from app.db.models.channel_member import ChannelMember
from app.db.models.user import User
from app.db.schemas.channel import ChannelCreate, ChannelResponse, ChannelUpdate
from app.db.schemas.channel_member import ChannelMemberCreate, ChannelMemberResponse
from app.db.schemas.common import ApiResponse
from app.repositories.channel_member_repository import ChannelMemberRepository
from app.repositories.channel_repository import ChannelRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.repositories.workspace_repository import WorkspaceRepository


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\\s-]", "", value)
    value = re.sub(r"[\\s_-]+", "-", value)
    return value.strip("-") or "channel"


class ChannelService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.workspace_repository = WorkspaceRepository(db)
        self.channel_repository = ChannelRepository(db)
        self.channel_member_repository = ChannelMemberRepository(db)
        self.workspace_member_repository = WorkspaceMemberRepository(db)

    def _require_workspace_member(self, current_user: User, workspace_id) -> None:
        workspaces = self.workspace_repository.list_for_user(current_user.id)
        if not any(ws.id == workspace_id for ws in workspaces):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this workspace",
            )

    def list_channels(
        self,
        current_user: User,
        workspace_id,
    ) -> ApiResponse[list[ChannelResponse]]:
        self._require_workspace_member(current_user=current_user, workspace_id=workspace_id)
        channels = self.channel_repository.list_for_workspace(workspace_id)
        return ApiResponse(
            success=True,
            message="Channels retrieved successfully",
            data=[ChannelResponse.model_validate(ch) for ch in channels],
        )

    def create_channel(
        self,
        current_user: User,
        payload: ChannelCreate,
    ) -> ApiResponse[ChannelResponse]:
        self._require_workspace_member(current_user=current_user, workspace_id=payload.workspace_id)

        slug = payload.slug or _slugify(payload.name)
        channel = Channel(
            workspace_id=payload.workspace_id,
            name=payload.name,
            slug=slug,
            description=payload.description,
            channel_type=payload.channel_type,
            created_by_id=current_user.id,
        )
        self.channel_repository.create(channel)
        self.db.flush()

        # Ensure creator is a member of the channel (useful for private channels later).
        member = ChannelMember(
            channel_id=channel.id,
            user_id=current_user.id,
            role="owner",
        )
        self.channel_member_repository.create(member)

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to create channel",
            ) from exc

        self.db.refresh(channel)
        # broadcast to all existing channels in the workspace so users see the new channel
        channels = self.channel_repository.list_for_workspace(payload.workspace_id)
        for ch in channels:
            if ch.id != channel.id:
                try:
                    import anyio
                    from app.realtime.connection_manager import realtime_manager

                    anyio.from_thread.run(
                        realtime_manager.broadcast_to_channel,
                        ch.id,
                        {"type": "channel_created", "workspace_id": str(payload.workspace_id)},
                    )
                except Exception:
                    pass
        return ApiResponse(
            success=True,
            message="Channel created successfully",
            data=ChannelResponse.model_validate(channel),
        )

    def get_channel(
        self,
        current_user: User,
        channel_id,
    ) -> ApiResponse[ChannelResponse]:
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )
        self._require_workspace_member(current_user=current_user, workspace_id=channel.workspace_id)
        return ApiResponse(
            success=True,
            message="Channel retrieved successfully",
            data=ChannelResponse.model_validate(channel),
        )

    def update_channel(
        self,
        current_user: User,
        channel_id,
        payload: ChannelUpdate,
    ) -> ApiResponse[ChannelResponse]:
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )
        self._require_workspace_member(current_user=current_user, workspace_id=channel.workspace_id)

        if payload.name is not None:
            channel.name = payload.name
        if payload.slug is not None:
            channel.slug = payload.slug
        if payload.description is not None:
            channel.description = payload.description
        if payload.channel_type is not None:
            channel.channel_type = payload.channel_type

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to update channel",
            ) from exc

        self.db.refresh(channel)
        return ApiResponse(
            success=True,
            message="Channel updated successfully",
            data=ChannelResponse.model_validate(channel),
        )

    def delete_channel_messages(
        self,
        current_user: User,
        channel_id,
    ) -> ApiResponse[None]:
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        self._require_workspace_member(current_user=current_user, workspace_id=channel.workspace_id)

        from sqlalchemy import delete

        stmt = delete(Activity).where(Activity.channel_id == channel_id)
        try:
            self.db.execute(stmt)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to delete channel messages",
            ) from exc

        try:
            import anyio
            from app.realtime.connection_manager import realtime_manager

            anyio.from_thread.run(
                realtime_manager.broadcast_to_channel,
                channel_id,
                {"type": "channel_messages_deleted", "channel_id": str(channel_id)},
            )
        except Exception:
            pass

        return ApiResponse(success=True, message="All channel messages deleted", data=None)

    def delete_channel(
        self,
        current_user: User,
        channel_id,
    ) -> ApiResponse[None]:
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found",
            )
        self._require_workspace_member(current_user=current_user, workspace_id=channel.workspace_id)
        self.channel_repository.delete(channel)
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to delete channel",
            ) from exc

        return ApiResponse(success=True, message="Channel deleted successfully", data=None)

    def list_channel_members(
        self,
        current_user: User,
        channel_id,
    ) -> ApiResponse[list[ChannelMemberResponse]]:
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        self._require_workspace_member(current_user=current_user, workspace_id=channel.workspace_id)
        members = self.channel_member_repository.list_for_channel(channel_id)
        workspace_member_ids = {
            m.user_id
            for m in self.workspace_member_repository.list_for_workspace(channel.workspace_id)
        }
        filtered = [m for m in members if m.user_id in workspace_member_ids]
        return ApiResponse(
            success=True,
            message="Channel members retrieved successfully",
            data=[ChannelMemberResponse.model_validate(m) for m in filtered],
        )

    def add_channel_member(
        self,
        current_user: User,
        payload: ChannelMemberCreate,
    ) -> ApiResponse[ChannelMemberResponse]:
        channel = self.channel_repository.get_by_id(payload.channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        self._require_workspace_member(current_user=current_user, workspace_id=channel.workspace_id)

        existing = self.channel_member_repository.get(payload.channel_id, payload.user_id)
        if existing:
            raise HTTPException(status_code=400, detail="User is already a channel member")

        member = ChannelMember(
            channel_id=payload.channel_id,
            user_id=payload.user_id,
            role=payload.role,
        )
        self.channel_member_repository.create(member)
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Unable to add channel member") from exc

        self.db.refresh(member)
        try:
            import anyio
            from app.realtime.connection_manager import realtime_manager

            anyio.from_thread.run(
                realtime_manager.broadcast_to_channel,
                payload.channel_id,
                {"type": "channel_member_added", "channel_id": str(payload.channel_id)},
            )
        except Exception:
            pass
        return ApiResponse(
            success=True,
            message="Channel member added successfully",
            data=ChannelMemberResponse.model_validate(member),
        )

    def remove_channel_member(
        self,
        current_user: User,
        channel_id,
        user_id,
    ) -> ApiResponse[None]:
        channel = self.channel_repository.get_by_id(channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        self._require_workspace_member(current_user=current_user, workspace_id=channel.workspace_id)

        member = self.channel_member_repository.get(channel_id, user_id)
        if not member:
            raise HTTPException(status_code=404, detail="Channel member not found")

        if channel.created_by_id and member.user_id == channel.created_by_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove the channel owner",
            )

        if member.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove yourself from the channel",
            )

        self.channel_member_repository.delete(member)
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Unable to remove channel member") from exc

        try:
            import anyio
            from app.realtime.connection_manager import realtime_manager

            anyio.from_thread.run(
                realtime_manager.broadcast_to_channel,
                channel_id,
                {"type": "channel_member_removed", "channel_id": str(channel_id)},
            )
        except Exception:
            pass
        return ApiResponse(success=True, message="Channel member removed successfully", data=None)
