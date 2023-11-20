import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from src.image.schemas import ImageSchemaResponse


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


class UserPage(BaseModel):
    user: UserRead
    images: list[ImageSchemaResponse]


class RequestVerifyEmail(BaseModel):
    email: EmailStr

    class Config:
        from_attributes: True
