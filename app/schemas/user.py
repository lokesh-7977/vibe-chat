from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    username: str
    email: EmailStr
    is_active: bool
    is_verified: bool
    is_deleted: bool


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
