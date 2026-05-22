from fastapi import APIRouter, Request, status
from app.api.dependencies.auth import AuthControllerDep
from app.db.schemas.auth import AuthTokensResponse, RefreshTokenResponse
from app.db.schemas.common import ApiResponse
from app.db.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=ApiResponse[AuthTokensResponse],
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user: UserCreate,
    request: Request,
    controller: AuthControllerDep,
):
    return controller.register_user(user=user, request=request)


@router.post(
    "/login",
    response_model=ApiResponse[AuthTokensResponse],
    status_code=status.HTTP_200_OK,
)
def login(
    user: UserLogin,
    request: Request,
    controller: AuthControllerDep,
):
    return controller.login_user(user=user, request=request)


@router.post(
    "/refresh",
    response_model=ApiResponse[RefreshTokenResponse],
    status_code=status.HTTP_200_OK,
)
def refresh_token(
    request: Request,
    controller: AuthControllerDep,
):
    return controller.refresh_token(request=request)


@router.get(
    "/get-profile",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
)
def get_profile(
    request: Request,
    controller: AuthControllerDep,
):
    return controller.get_profile(request=request)


@router.delete(
    "/delete-account",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
def delete_account(
    request: Request,
    controller: AuthControllerDep,
):
    return controller.delete_account(request=request)


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
def logout(
    request: Request,
    controller: AuthControllerDep,
):
    return controller.logout_user(request=request)
