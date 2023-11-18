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

    async def generate_hashed_password(self, password: str) -> str:
        return self.jwt_settings.pwd_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.jwt_settings.pwd_context.verify(password, hashed_password)

    async def generate_token(
        self,
        token_type: TokenType,
        user_id: str,
        ttl_in_minutes: int | None,
    ) -> str:
        return self.jwt_settings.create_token(
            token_type, {"uid": str(user_id)}, ttl=ttl_in_minutes
        )

    async def decode_token(
        self, token: str, token_type: TokenType, db: AsyncSession
    ) -> str:
        return await self.jwt_settings.decode_token(token, token_type, db)

    async def current_active_user(
        self,
        token: str = Depends(jwt_settings.oauth2_scheme),
        db: AsyncSession = Depends(database),
    ) -> str:
        return await self.au.get_current_active_user(token=token, db=db)


user_service = UserService()

current_active_user = user_service.current_active_user
