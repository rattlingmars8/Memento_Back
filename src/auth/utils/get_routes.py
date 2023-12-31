from fastapi import (
    APIRouter,
    Depends,
    Request,
    status,
    Response,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import (
    UserRead,
    UserCreate,
    OnLoginResponse,
    RequestVerifyEmailOrForgetPassword,
)
from src.auth.service import user_service, current_active_user
from src.database.sql.models import User
from src.database.sql.postgres import database


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
            user = await self.user_service.au.register_user(
                user_create, db=db, request=request
            )
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
            user, access_token = await self.user_service.au.login_user(
                response=response, body=body, db=db
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

    def generate_logout_route(self):
        router = APIRouter()

        @router.get("/logout", status_code=status.HTTP_204_NO_CONTENT)
        async def logout_route(response: Response):
            return await self.user_service.au.logout_user(response)

        return router

    def generate_refresh_route(self):
        router = APIRouter()

        @router.get(
            "/jwt/refresh",
            status_code=status.HTTP_200_OK,
            responses={
                status.HTTP_200_OK: {"model": OnLoginResponse},
                status.HTTP_401_UNAUTHORIZED: {"detail": "Invalid refresh token"},
            },
        )
        async def refresh_route(
            request: Request,
            db: AsyncSession = Depends(database),
        ):
            user, access_token = await self.user_service.au.access_refresh(request, db)
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
            user_email: RequestVerifyEmailOrForgetPassword,
            request: Request,
            # bg_tasks: BackgroundTasks,
            db: AsyncSession = Depends(database),
        ):
            return await self.user_service.au.on_request_verify(
                user_email=user_email.email, request=request, db=db
            )

        @router.get("/verify/{verify_token}", status_code=status.HTTP_200_OK)
        async def verify(
            verify_token: str,
            db: AsyncSession = Depends(database),
        ):
            return await self.user_service.au.verify_user(verify_token, db)

        return router

    def get_forget_routes(self):
        router = APIRouter()

        @router.post("/forgot-password", status_code=status.HTTP_200_OK)
        async def forget_password(
            user_email: RequestVerifyEmailOrForgetPassword,
            request: Request,
            db: AsyncSession = Depends(database),
        ):
            return await self.user_service.au.forget_password(
                email=user_email.email, request=request, db=db
            )

        @router.post("/set_new_password", status_code=status.HTTP_200_OK)
        async def set_new_password(
            token: str,
            new_password: str,
            db: AsyncSession = Depends(database),
        ):
            return await self.user_service.au.set_new_password(
                reset_token=token, new_password=new_password, db=db
            )

        return router

    def get_user_page(self):
        router = APIRouter()

        @router.get("/user/{user_id}", status_code=status.HTTP_200_OK)
        async def get_user_page(
            user_id: str,
            user: User = Depends(current_active_user),
            db: AsyncSession = Depends(database),
        ):
            return await self.user_service.get_user_page(user_id, user, db)

        @router.get("/me", status_code=status.HTTP_200_OK, response_model=UserRead)
        async def get_me(
            user: User = Depends(current_active_user),
            db: AsyncSession = Depends(database),
        ):
            return UserRead(
                id=user.id,
                username=user.username,
                email=user.email,
                avatar=user.avatar,
            )

        return router


auth_routes = AuthRoutes()
