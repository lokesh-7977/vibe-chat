from fastapi import Request

from app.db.schemas.auth import AuthTokensResponse, RefreshTokenResponse
from app.db.schemas.common import ApiResponse
from app.db.schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate
from app.services.auth_service import AuthService


class AuthController:
    def __init__(self, auth_service: AuthService) -> None:
        self.auth_service = auth_service

    def register_user(
        self,
        user: UserCreate,
        request: Request,
    ) -> ApiResponse[AuthTokensResponse]:
        return self.auth_service.register_user(user=user, request=request)

    def login_user(
        self,
        user: UserLogin,
        request: Request,
    ) -> ApiResponse[AuthTokensResponse]:
        return self.auth_service.login_user(user=user, request=request)

    def refresh_token(self, request: Request) -> ApiResponse[RefreshTokenResponse]:
        return self.auth_service.refresh_token(request=request)

    def get_profile(self, request: Request) -> ApiResponse[UserResponse]:
        return self.auth_service.get_profile(request=request)

    def update_profile(
        self,
        payload: UserUpdate,
        request: Request,
    ) -> ApiResponse[UserResponse]:
        return self.auth_service.update_profile(payload=payload, request=request)

    def delete_account(self, request: Request) -> ApiResponse[None]:
        return self.auth_service.delete_account(request=request)

    def logout_user(self, request: Request) -> ApiResponse[None]:
        return self.auth_service.logout_user(request=request)
