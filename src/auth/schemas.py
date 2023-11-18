import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    avatar: str

    class Config:
        from_attributes: True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str

    class Config:
        from_attributes: True


class OnLoginResponse(BaseModel):
    user: UserRead
    access_token: str
    # refresh_token: str
