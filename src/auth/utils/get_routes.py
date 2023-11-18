from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
    Response,
    BackgroundTasks,
)
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import UserRead, UserCreate, OnLoginResponse
from src.auth.service import user_service
from src.auth.utils.TokenType import TokenType
from src.auth.utils.email import send_email_verification
from src.database.sql.postgres import database
import src.auth.repository as repo


class AuthRoutes:
    user_service = user_service

    def generate_register_route(self):
        router = APIRouter()

        @router.post(
            "/register", response_model=UserRead, status_code=status.HTTP_201_CREATED
        )
        async def register_route(
            request: Request,
            user_create: UserCreate,
            db: AsyncSession = Depends(database),
        ):
            try:
                user = await self.user_service.au.register_user(
                    user_create, db=db, request=request
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
                )
            # print(user)
            return user

        return router

    def generate_login_route(self):
        router = APIRouter()

        @router.post(
            "/jwt/login", status_code=status.HTTP_200_OK, response_model=OnLoginResponse
        )
        async def login_route(
            response: Response,
            body: OAuth2PasswordRequestForm = Depends(),
            db: AsyncSession = Depends(database),
        ):
            user = await repo.get_user_by_email(body.username, db)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                )
            if not user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email is not verified. Please varify your email: "
                    + user.email,
                )
            if not self.user_service.verify_password(
                body.password, user.hashed_password
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                )
            access_token = await self.user_service.generate_token(
                TokenType.ACCESS, user.id, ttl_in_minutes=30
            )
            refresh_token = await self.user_service.generate_token(
                TokenType.REFRESH, user.id, ttl_in_minutes=60
            )
            print(access_token)
            print(refresh_token)
            await repo.update_refresh_token(user, refresh_token, db)

            response.set_cookie(
                "refresh_token", refresh_token, httponly=True, max_age=7200
            )
            return OnLoginResponse(
                user=UserRead(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    avatar=user.avatar,
                ),
                access_token=access_token,
            )

        return router

    def generate_refresh_route(self):
        router = APIRouter()

        @router.post("/jwt/refresh", status_code=status.HTTP_200_OK)
        async def refresh_route(
            response: Response,
            refresh_token: str,
            db: AsyncSession = Depends(database),
        ):
            user = await self.user_service.decode_token(
                refresh_token, TokenType.REFRESH, db
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            access_token = await self.user_service.generate_token(
                TokenType.ACCESS, user.id, ttl_in_minutes=30
            )
            print(access_token)

            # response.set_cookie("refresh_token", refresh_token, httponly=True, max_age=7200)
            return OnLoginResponse(
                user=UserRead(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    avatar=user.avatar,
                ),
                access_token=access_token,
            )

        return router

    def verify_email_route(self):
        router = APIRouter()

        @router.post("/request-verify", status_code=status.HTTP_200_OK)
        async def request_verify(
            user_email: str,
            request: Request,
            # bg_tasks: BackgroundTasks,
            db: AsyncSession = Depends(database),
        ):
            user = await repo.get_user_by_email(user_email, db)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            verify_token = await self.user_service.generate_token(
                TokenType.VERIFY, user.id, ttl_in_minutes=60
            )
            await send_email_verification(
                user.email, user.username, verify_token, request.headers["Origin"]
            )
            return {"detail": f"Email instructions to verify was sent to {user.email}."}

        @router.get("/verify/{verify_token}", status_code=status.HTTP_200_OK)
        async def verify(
            verify_token: str,
            db: AsyncSession = Depends(database),
        ):
            user = await self.user_service.decode_token(
                verify_token, TokenType.VERIFY, db
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )

            return {"detail": "Email verified"}

        return router


auth_routes = AuthRoutes()
