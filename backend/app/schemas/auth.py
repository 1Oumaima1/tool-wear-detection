from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    role: str | None = None


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    password: str
    role: UserRole = UserRole.operator


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str | None = None
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True
