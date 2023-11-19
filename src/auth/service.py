from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, status

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import UserRead, UserCreate
from src.auth.utils.JWTContext import JWTContext
from src.auth.utils.TokenType import TokenType
from src.auth.utils.authutils import authutils
from src.database.sql.postgres import database


class UserService:
    jwt_settings = JWTContext()
    au = authutils

    async def current_active_user(
        self,
        token: str = Depends(jwt_settings.oauth2_scheme),
        db: AsyncSession = Depends(database),
    ) -> str:
        return await self.au.get_current_active_user(token=token, db=db)


user_service = UserService()

current_active_user = user_service.current_active_user
