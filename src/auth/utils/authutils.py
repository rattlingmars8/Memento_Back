from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import UserCreate
from src.auth.utils.TokenType import TokenType
from src.auth.utils.JWTContext import JWTContext
import src.auth.repository as repo
from src.auth.utils.email import send_email_verification, send_email_for_reset_pswd
from src.config import settings


class Auth:
    jwt_settings = JWTContext()

    async def get_current_active_user(
        self,
        db: AsyncSession,
        token: str = Depends(jwt_settings.oauth2_scheme),
    ):
        return await self.jwt_settings.decode_token(token, TokenType.ACCESS, db=db)

    async def register_user(
        self,
        user_create: UserCreate,
        db: AsyncSession,
        request: Optional[Request] = None,
    ):
        await self._check_existing_user(user_create, db)
        hashed_password = self.jwt_settings.pwd_context.hash(user_create.password)
        user_info = self._prepare_user_info(user_create, hashed_password)
        created_user = await repo.create_user(user_info, db=db)
        return created_user

    async def login_user(
        self, response: Response, body: OAuth2PasswordRequestForm, db: AsyncSession
    ):
        user = await self._get_user_by_email(body.username, db)
        await self._validate_login(user, body.password)
        access_token, refresh_token = await self._create_tokens(user)
        await repo.update_refresh_token(user, refresh_token, db)
        self._set_tokens_in_response(response, refresh_token)
        return user, access_token

    async def on_request_verify(
        self, user_email: str, request: Request, db: AsyncSession
    ):
        user = await repo.get_user_by_email(user_email, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        verify_token = await self.jwt_settings.create_token(
            TokenType.VERIFY, user.id, ttl_in_minutes=settings.ttl_verify_token
        )
        return await send_email_verification(
            user.email, user.username, verify_token, request.headers["Origin"]
        )

    async def verify_user(self, verify_token: str, db: AsyncSession):
        user = await self.jwt_settings.decode_token(verify_token, TokenType.VERIFY, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return {"detail": "Email verified"}

    async def access_refresh(
        self, response: Response, refresh_token: str, db: AsyncSession
    ):
        user = await self.jwt_settings.decode_token(
            refresh_token, TokenType.REFRESH, db
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        if user.refresh_token != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        access_token = await self.jwt_settings.create_token(
            TokenType.ACCESS, user.id, ttl_in_minutes=settings.ttl_access_token
        )
        return user, access_token

    async def forget_password(self, email: str, request: Request, db: AsyncSession):
        user = await repo.get_user_by_email(email, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        forget_token = await self.jwt_settings.create_token(
            TokenType.FORGOT, user.id, ttl_in_minutes=settings.ttl_forget_password_token
        )
        print(forget_token)
        return await send_email_for_reset_pswd(
            user.email, user.username, forget_token, request.headers["Origin"]
        )

    async def set_new_password(
        self, reset_token: str, new_password: str, db: AsyncSession
    ):
        user = await self.jwt_settings.decode_token(reset_token, TokenType.FORGOT, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        new_hashed_password = self.jwt_settings.pwd_context.hash(new_password)
        user.hashed_password = new_hashed_password
        await db.commit()
        await db.refresh(user)
        return {"detail": "Password changed"}

    async def _get_user_by_email(self, email: str, db: AsyncSession):
        user = await repo.get_user_by_email(email, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        return user

    async def _validate_login(self, user, password: str):
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Email is not verified. Please verify your email: {user.email}",
            )

        if not await self.jwt_settings.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

    async def _create_tokens(self, user):
        access_token = await self.jwt_settings.create_token(
            TokenType.ACCESS, user.id, ttl_in_minutes=settings.ttl_access_token
        )
        refresh_token = await self.jwt_settings.create_token(
            TokenType.REFRESH, user.id, ttl_in_minutes=settings.ttl_refresh_token
        )
        return access_token, refresh_token

    def _set_tokens_in_response(self, response: Response, refresh_token: str):
        response.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            expires=60 * settings.ttl_refresh_token,
            samesite="lax",
            secure=True,
        )

    async def _check_existing_user(self, user_create: UserCreate, db: AsyncSession):
        is_exists_email = await repo.get_user_by_email(user_create.email, db)
        is_exists_username = await repo.get_user_by_username(user_create.username, db)

        if is_exists_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
            )
        elif is_exists_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
            )

    def _prepare_user_info(self, user_create: UserCreate, hashed_password: str):
        return UserCreate(
            email=user_create.email,
            password=hashed_password,
            username=user_create.username,
        )


authutils = Auth()
