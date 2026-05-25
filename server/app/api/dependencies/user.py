from typing import Annotated
from uuid import UUID as PyUUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.verify_access_token import verify_access_token


def _resolve_user(
    user_id: str,
    db: Session,
) -> User:
    try:
        user_uuid = PyUUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        ) from None

    user_repository = UserRepository(db)
    db_user = user_repository.get_active_by_id(user_uuid)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )
    return db_user


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        try:
            user_id = verify_access_token(token)
            return _resolve_user(user_id, db)
        except (ValueError, Exception):
            pass

    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )

    return _resolve_user(user_id, db)


CurrentUserDep = Annotated[User, Depends(get_current_user)]
