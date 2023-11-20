from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError

from src.auth.schemas import UserCreate
from src.database.sql.models import User, Image
from src.database.sql.postgres import database


async def id_user_auth(_id: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == _id))
    existing_user = result.scalar()
    return existing_user


async def update_refresh_token(
    user: User, refresh_token: str, db: AsyncSession
) -> User:
    user.refresh_token = refresh_token
    await db.commit()


async def get_user_by_email(email: str, db: AsyncSession) -> User:
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    existing_user = result.scalar()
    return existing_user


async def create_user(user_info: UserCreate, db: AsyncSession):
    try:
        user = User(
            **user_info.model_dump(exclude={"password"}),
            hashed_password=user_info.password
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError:
        await db.rollback()
        return None


async def get_user_by_username(username: str, db: AsyncSession) -> User:
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    existing_user = result.scalar()
    return existing_user


async def get_user_page(user_id: str, user: User, db: AsyncSession):
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    existing_user = result.scalar()
    images = existing_user.images
    return existing_user, images
