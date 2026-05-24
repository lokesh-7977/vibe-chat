from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies.user import CurrentUserDep
from app.db.schemas.common import ApiResponse
from app.db.schemas.user import UserResponse
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=ApiResponse[list[UserResponse]],
    status_code=status.HTTP_200_OK,
)
def list_users(
    _request: Request,
    _current_user: CurrentUserDep,
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    users = repo.list_active()
    return ApiResponse(
        success=True,
        message="Users retrieved successfully",
        data=[UserResponse.model_validate(u) for u in users],
    )
