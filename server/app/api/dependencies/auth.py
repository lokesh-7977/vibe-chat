from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.controllers.auth_controller import AuthController
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


def get_auth_controller(db: Session = Depends(get_db)) -> AuthController:
    user_repository = UserRepository(db)
    auth_service = AuthService(user_repository)
    return AuthController(auth_service)


AuthControllerDep = Annotated[AuthController, Depends(get_auth_controller)]
