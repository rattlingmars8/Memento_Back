import typing
import uuid
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

from src.comment.schemas import CommentSchemaResponse
from src.database.sql.models import Tag, Comment
from src.tag.schemas import TagSchemaResponse


class ImageSchemaRequest(BaseModel):
    title: str = Field()


class ImageSchemaUpdateRequest(ImageSchemaRequest):
    title: str = Field(default=None)


class ImageAIReplaceTransformation(BaseModel):
    Object_to_detect: str = Field(default="")
    Replace_with: str = Field(default="")

    class Config:
        from_attributes: True


class ImageScaleTransformation(BaseModel):
    Width: int = Field(default=0)
    Height: int = Field(default=0)

    class Config:
        from_attributes: True


class ImageBlackAndWhiteTransformation(BaseModel):
    black_and_white: bool = Field(default=False)

    class Config:
        from_attributes: True


class ImageRotationTransformation(BaseModel):
    angle: int = Field(default=0, le=360, ge=-360)

    class Config:
        from_attributes: True


class EditFormData(BaseModel):
    ai_replace: typing.Optional[ImageAIReplaceTransformation] = Field(default=None)
    scale: typing.Optional[ImageScaleTransformation] = Field(default=None)
    black_and_white: typing.Optional[ImageBlackAndWhiteTransformation] = Field(
        default=None
    )
    rotation: typing.Optional[ImageRotationTransformation] = Field(default=None)


class OwnerInfo(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    avatar: str


# class ImageSchemaResponse(ImageSchemaRequest):
#     id: int
#     title: str
#     owner: OwnerInfo
#     cloudinary_url: str
#     rating: float
#     likes: int
#     tags: list[str]
#     comments: list[CommentSchemaResponse]
#     edited_cloudinary_url: str | None
#     created_at: datetime
#     updated_at: datetime | None
#
#     class Config:
#         from_attributes: True


class ImageSchemaResponse(BaseModel):
    owner: OwnerInfo
    id: int
    title: str
    cloudinary_url: str
    edited_cloudinary_url: str | None
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes: True
        extra = "allow"
