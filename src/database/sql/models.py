import uuid
from datetime import datetime
from pydantic import EmailStr

from fastapi_users_db_sqlalchemy import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyBaseOAuthAccountTableUUID,
)
from sqlalchemy import String, Integer, DateTime, Boolean, func, Uuid, Numeric

from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(
        String(length=320), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(length=50), unique=True, nullable=False
    )
    avatar: Mapped[str] = mapped_column(String(length=1024), nullable=True, default="https://static.vecteezy.com/system/resources/previews/021/548/095/non_2x/default-profile-picture-avatar-user-avatar-icon-person-icon-head-icon-profile-picture-icons-default-anonymous-user-male-and-female-businessman-photo-placeholder-social-network-avatar-portrait-free-vector.jpg")
    hashed_password: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    refresh_token: Mapped[str] = mapped_column(
        String(length=1024), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, default=func.now(), nullable=True
    )
    access_level: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.id"), default=1
    )
    permission: Mapped["Permission"] = relationship(
        "Permission", back_populates="users", lazy="joined"
    )
    images: Mapped[list["Image"]] = relationship(
        "Image", back_populates="owner", lazy="joined"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="owner", lazy="noload"
    )
    ratings: Mapped[list["Rating"]] = relationship(
        "Rating", back_populates="owner", lazy="joined"
    )
    likes: Mapped[list["Like"]] = relationship(
        "Like", back_populates="owner", lazy="joined"
    )


class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    can_add_image: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_update_image: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    can_delete_image: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    can_add_tag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_update_tag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    can_delete_tag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    can_add_comment: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    can_update_comment: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    can_delete_comment: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    users: Mapped[list[User]] = relationship(
        "User", back_populates="permission", lazy="noload"
    )


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("user.id"))
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"))
    text: Mapped[str] = mapped_column(String(200))

    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, default=func.now(), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, default=None, onupdate=func.now(), nullable=True
    )

    owner: Mapped[User] = relationship("User", back_populates="comments")
    image: Mapped["Image"] = relationship("Image", back_populates="comments")


class Image(Base):
    __tablename__ = "images"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("user.id"))
    title: Mapped[str] = mapped_column(String(30), nullable=True, default=None)

    cloudinary_url: Mapped[str] = mapped_column(
        String(300), nullable=False, default="placeholder"
    )
    rating: Mapped[Numeric(3, 2)] = mapped_column(Numeric(3, 2), default=0.00)
    edited_cloudinary_url: Mapped[str] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=None, onupdate=func.now(), nullable=True
    )
    owner: Mapped[User] = relationship("User", back_populates="images", lazy="noload")
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="image_tags",
        back_populates="images",
        lazy="joined",
        cascade="all, delete",
    )
    comments: Mapped[list[Comment]] = relationship(
        "Comment", back_populates="image", lazy="joined", cascade="all, delete"
    )
    likes: Mapped[list["Like"]] = relationship(
        "Like", back_populates="image", lazy="joined"
    )


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    images: Mapped[list[Image]] = relationship(
        "Image", secondary="image_tags", back_populates="tags"
    )


class ImageTag(Base):
    __tablename__ = "image_tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"))
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("tags.id"))


class Rating(Base):
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("user.id"))
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"))
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    owner: Mapped[User] = relationship("User", back_populates="ratings")


class Like(Base):
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("user.id"))
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"))
    owner: Mapped[User] = relationship("User", back_populates="likes")
    image: Mapped[Image] = relationship("Image", back_populates="likes")
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, default=func.now(), nullable=True
    )
