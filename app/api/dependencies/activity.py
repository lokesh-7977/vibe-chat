from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.controllers.activity_controller import ActivityController
from app.db.session import get_db
from app.services.activity_service import ActivityService


def get_activity_controller(db: Session = Depends(get_db)) -> ActivityController:
    return ActivityController(ActivityService(db))


ActivityControllerDep = Annotated[ActivityController, Depends(get_activity_controller)]

