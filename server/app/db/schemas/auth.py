from pydantic import BaseModel

from app.db.schemas.user import UserResponse


class AuthTokensResponse(BaseModel):
    access_token: str
    user: UserResponse


class RefreshTokenResponse(BaseModel):
    access_token: str
