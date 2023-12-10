from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.database.sql.models import User
from src.database.sql.postgres import database
import src.auth.repository as repo
from src.auth.utils.TokenType import TokenType


class JWTContext:
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    DEFAULT_TTL_MINUTES = 15

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/jwt/login")

    async def generate_hashed_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(password, hashed_password)

    async def create_token(
        self, token_type: TokenType, user_id: str, ttl_in_minutes: int | None
    ) -> str:
        to_encode = {"uid": str(user_id)}
        expire = self._calculate_expiry(ttl_in_minutes)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "ttype": token_type.value}
        )
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    async def decode_token(
        self, token: str, token_type: TokenType, db: AsyncSession
    ) -> dict | User | bool:
        payload = await self._verify_token(token, token_type)
        # print(payload)
        user = await repo.id_user_auth(payload["uid"], db=db)
        # print(user)

        if token_type == TokenType.VERIFY:
            if user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already verified",
                )
            user.is_verified = True
            await db.commit()
            await db.refresh(user)

        return await self._token_response(user, token, token_type)

    async def _verify_token(self, token: str, token_type: TokenType) -> dict:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            # print(payload)
            if payload["ttype"] != token_type.value:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

    async def _token_response(self, user: User, token: str, token_type: TokenType):
        if token_type == TokenType.ACCESS or token_type == TokenType.VERIFY:
            # print(user.email)
            return user
        elif token_type == TokenType.REFRESH:
            if user.refresh_token != token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )
            return user
        elif token_type == TokenType.FORGOT:
            return user if user else False

    def _calculate_expiry(self, ttl: int = None) -> datetime:
        return datetime.utcnow() + timedelta(
            minutes=ttl if ttl is not None else self.DEFAULT_TTL_MINUTES
        )
