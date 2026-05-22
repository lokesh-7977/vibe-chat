from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.controllers.channel_controller import ChannelController
from app.db.session import get_db
from app.services.channel_service import ChannelService


def get_channel_controller(db: Session = Depends(get_db)) -> ChannelController:
    channel_service = ChannelService(db)
    return ChannelController(channel_service)


ChannelControllerDep = Annotated[ChannelController, Depends(get_channel_controller)]

