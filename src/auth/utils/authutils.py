from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import UserCreate
from src.auth.utils.TokenType import TokenType
from src.database.sql.postgres import database
from src.auth.utils.JWTContext import JWTContext
import src.auth.repository as repo


class Auth:
    jwt_settings = JWTContext()

    # def __init__(
    #     # self, db_session: AsyncSession = Depends(database)
    # ):
    #     self.db = db_session

    async def get_current_active_user(
        self,
        db: AsyncSession,
        token: str = Depends(jwt_settings.oauth2_scheme),
    ):
        # credentials_exception = HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED,
        #     detail="Could not validate credentials",
        #     headers={"WWW-Authenticate": "Bearer"},
        # )
        return await self.jwt_settings.decode_token(token, TokenType.ACCESS, db=db)

    async def register_user(
        self, user_create: UserCreate, db: AsyncSession, request: Optional[Request] = None
    ):
        is_exists = await repo.get_user_by_email(user_create.email, db)
        if is_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )
        else:
            hashed_password = self.jwt_settings.pwd_context.hash(
                user_create.password
            )
            user_info = UserCreate(
                    email=user_create.email,
                    password=hashed_password,
                    username=user_create.username,
                )
            create_user = await repo.create_user(
                user_info, db=db
            )
            return create_user

    def _create_credentials_exception(self):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


authutils = Auth()

