from app.db.models.user import User
from app.db.schemas.channel import ChannelCreate, ChannelResponse, ChannelUpdate
from app.db.schemas.channel_member import ChannelMemberCreate, ChannelMemberResponse
from app.db.schemas.common import ApiResponse
from app.services.channel_service import ChannelService


class ChannelController:
    def __init__(self, channel_service: ChannelService) -> None:
        self.channel_service = channel_service

    def list_channels(self, current_user: User, workspace_id) -> ApiResponse[list[ChannelResponse]]:
        return self.channel_service.list_channels(current_user=current_user, workspace_id=workspace_id)

    def create_channel(self, current_user: User, payload: ChannelCreate) -> ApiResponse[ChannelResponse]:
        return self.channel_service.create_channel(current_user=current_user, payload=payload)

    def get_channel(self, current_user: User, channel_id) -> ApiResponse[ChannelResponse]:
        return self.channel_service.get_channel(current_user=current_user, channel_id=channel_id)

    def update_channel(self, current_user: User, channel_id, payload: ChannelUpdate) -> ApiResponse[ChannelResponse]:
        return self.channel_service.update_channel(current_user=current_user, channel_id=channel_id, payload=payload)

    def delete_channel(self, current_user: User, channel_id) -> ApiResponse[None]:
        return self.channel_service.delete_channel(current_user=current_user, channel_id=channel_id)

    def delete_channel_messages(self, current_user: User, channel_id) -> ApiResponse[None]:
        return self.channel_service.delete_channel_messages(current_user=current_user, channel_id=channel_id)

    def list_channel_members(self, current_user: User, channel_id) -> ApiResponse[list[ChannelMemberResponse]]:
        return self.channel_service.list_channel_members(current_user=current_user, channel_id=channel_id)

    def add_channel_member(self, current_user: User, payload: ChannelMemberCreate) -> ApiResponse[ChannelMemberResponse]:
        return self.channel_service.add_channel_member(current_user=current_user, payload=payload)

    def remove_channel_member(self, current_user: User, channel_id, user_id) -> ApiResponse[None]:
        return self.channel_service.remove_channel_member(
            current_user=current_user,
            channel_id=channel_id,
            user_id=user_id,
        )
