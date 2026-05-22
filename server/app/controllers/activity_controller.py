from app.db.models.user import User
from app.db.schemas.activity import ActivityCreateRequest, ActivityResponse, ActivityUpdate
from app.db.schemas.common import ApiResponse
from app.services.activity_service import ActivityService


class ActivityController:
    def __init__(self, activity_service: ActivityService) -> None:
        self.activity_service = activity_service

    def create_activity(
        self,
        current_user: User,
        channel_id,
        payload: ActivityCreateRequest,
    ) -> ApiResponse[ActivityResponse]:
        return self.activity_service.create_activity(
            current_user=current_user,
            channel_id=channel_id,
            payload=payload,
        )

    def list_channel_activities(
        self,
        current_user: User,
        channel_id,
        limit: int,
        offset: int,
    ) -> ApiResponse[list[ActivityResponse]]:
        return self.activity_service.list_channel_activities(
            current_user=current_user,
            channel_id=channel_id,
            limit=limit,
            offset=offset,
        )

    def get_activity(self, current_user: User, activity_id) -> ApiResponse[ActivityResponse]:
        return self.activity_service.get_activity(current_user=current_user, activity_id=activity_id)

    def update_activity(
        self,
        current_user: User,
        activity_id,
        payload: ActivityUpdate,
    ) -> ApiResponse[ActivityResponse]:
        return self.activity_service.update_activity(
            current_user=current_user,
            activity_id=activity_id,
            payload=payload,
        )

    def delete_activity(self, current_user: User, activity_id) -> ApiResponse[None]:
        return self.activity_service.delete_activity(current_user=current_user, activity_id=activity_id)

