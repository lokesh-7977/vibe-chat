from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    full_name: str
    username: str
    email: EmailStr
    is_active: bool
    is_verified: bool