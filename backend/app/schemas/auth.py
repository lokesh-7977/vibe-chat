from pydantic import BaseModel

from app.schemas.user import UserResponse


class AuthTokensResponse(BaseModel):
    access_token: str
    user: UserResponse


class RefreshTokenResponse(BaseModel):
    access_token: str
