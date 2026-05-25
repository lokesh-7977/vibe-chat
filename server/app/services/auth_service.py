from uuid import UUID as PyUUID

from fastapi import HTTPException, Request, status

from app.core.security import hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.db.schemas.auth import AuthTokensResponse, RefreshTokenResponse
from app.db.schemas.common import ApiResponse
from app.db.schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate
from app.utils.create_access_token import create_access_token
from app.utils.create_refresh_token import create_refresh_token
from app.utils.generate_username import generate_username
from app.utils.verify_access_token import verify_access_token
from app.utils.verify_refresh_token import verify_refresh_token


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register_user(
        self,
        user: UserCreate,
        request: Request,
    ) -> ApiResponse[AuthTokensResponse]:
        existing_user = self.user_repository.get_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        username = generate_username(user.full_name, self.user_repository.db)
        db_user = self.user_repository.create(
            full_name=user.full_name,
            username=username,
            email=user.email,
            password=hash_password(user.password),
            is_active=True,
            is_verified=False,
            is_deleted=False,
        )

        access_token = create_access_token({"sub": str(db_user.id)})
        refresh_token = create_refresh_token(str(db_user.id))
        self._store_session(request, str(db_user.id), refresh_token)

        return ApiResponse(
            success=True,
            message="User registered successfully",
            data=AuthTokensResponse(
                access_token=access_token,
                user=UserResponse.model_validate(db_user),
            ),
        )

    def login_user(
        self,
        user: UserLogin,
        request: Request,
    ) -> ApiResponse[AuthTokensResponse]:
        db_user = self.user_repository.get_active_by_email(user.email)
        if not db_user or not verify_password(user.password, db_user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token({"sub": str(db_user.id)})
        refresh_token = create_refresh_token(str(db_user.id))
        self._store_session(request, str(db_user.id), refresh_token)

        return ApiResponse(
            success=True,
            message="Login successful",
            data=AuthTokensResponse(
                access_token=access_token,
                user=UserResponse.model_validate(db_user),
            ),
        )

    def refresh_token(self, request: Request) -> ApiResponse[RefreshTokenResponse]:
        session_refresh_token = request.session.get("refresh_token")
        if not session_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing",
            )

        try:
            user_id = verify_refresh_token(session_refresh_token)
            user_uuid = PyUUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from None

        db_user = self._get_authenticated_user(request)
        if db_user.id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        access_token = create_access_token({"sub": str(db_user.id)})
        new_refresh_token = create_refresh_token(str(db_user.id))
        request.session["refresh_token"] = new_refresh_token

        return ApiResponse(
            success=True,
            message="Token refreshed successfully",
            data=RefreshTokenResponse(access_token=access_token),
        )

    def get_profile(self, request: Request) -> ApiResponse[UserResponse]:
        db_user = self._get_authenticated_user(request)
        return ApiResponse(
            success=True,
            message="Profile retrieved successfully",
            data=UserResponse.model_validate(db_user),
        )

    def update_profile(
        self,
        payload: UserUpdate,
        request: Request,
    ) -> ApiResponse[UserResponse]:
        db_user = self._get_authenticated_user(request)

        if payload.email is not None and payload.email != db_user.email:
            existing = self.user_repository.get_by_email(payload.email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use",
                )
            db_user.email = payload.email

        if payload.full_name is not None:
            db_user.full_name = payload.full_name

        if payload.username is not None:
            db_user.username = payload.username

        self.user_repository.save()
        self.user_repository.db.refresh(db_user)

        return ApiResponse(
            success=True,
            message="Profile updated successfully",
            data=UserResponse.model_validate(db_user),
        )

    def delete_account(self, request: Request) -> ApiResponse[None]:
        db_user = self._get_authenticated_user(request)

        db_user.is_deleted = True
        db_user.is_active = False
        self.user_repository.save()

        request.session.clear()
        return ApiResponse(
            success=True,
            message="Account deleted successfully",
            data=None,
        )

    def logout_user(self, request: Request) -> ApiResponse[None]:
        self._get_authenticated_user(request)
        request.session.clear()
        return ApiResponse(
            success=True,
            message="Logout successful",
            data=None,
        )

    @staticmethod
    def _store_session(request: Request, user_id: str, refresh_token: str) -> None:
        request.session["user_id"] = user_id
        request.session["refresh_token"] = refresh_token

    def _get_authenticated_user(self, request: Request):
        user_id: str | None = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
            try:
                user_id = verify_access_token(token)
            except Exception:
                pass

        if not user_id:
            user_id = request.session.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        try:
            user_uuid = PyUUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            ) from None

        db_user = self.user_repository.get_active_by_id(user_uuid)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )

        return db_user
