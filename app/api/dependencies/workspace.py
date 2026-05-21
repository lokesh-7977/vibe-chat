from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.controllers.workspace_controller import WorkspaceController
from app.db.session import get_db
from app.services.workspace_service import WorkspaceService


def get_workspace_controller(db: Session = Depends(get_db)) -> WorkspaceController:
    workspace_service = WorkspaceService(db)
    return WorkspaceController(workspace_service)


WorkspaceControllerDep = Annotated[WorkspaceController, Depends(get_workspace_controller)]

