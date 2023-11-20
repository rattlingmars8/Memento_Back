from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import UserPage, UserRead
from src.auth.utils.JWTContext import JWTContext
from src.auth.utils.authutils import authutils
from src.comment.schemas import CommentSchemaResponse
from src.database.sql.models import User
from src.database.sql.postgres import database
import src.auth.repository as repo
from src.image.schemas import ImageSchemaResponse, OwnerInfo


class UserService:
    jwt_settings = JWTContext()
    au = authutils

    async def current_active_user(
        self,
        token: str = Depends(jwt_settings.oauth2_scheme),
        db: AsyncSession = Depends(database),
    ) -> str:
        return await self.au.get_current_active_user(token=token, db=db)

    async def get_user_page(self, user_id: str, user: User, db: AsyncSession):
        existing_user, list_images = await repo.get_user_page(user_id, user, db)
        owner = await repo.id_user_auth(existing_user.id, db)
        owner = OwnerInfo(
            id=owner.id, email=owner.email, username=owner.username, avatar=owner.avatar
        )
        images = [
            ImageSchemaResponse(
                id=image.id,
                title=image.title,
                owner=owner,
                cloudinary_url=image.cloudinary_url,
                rating=image.rating,
                likes=len(image.likes),
                tags=[tag.name for tag in image.tags],
                comments=[CommentSchemaResponse(
                    id=comment.id,
                    owner_id=comment.owner_id,
                    image_id=comment.image_id,
                    text=comment.text,
                    created_at=comment.created_at,
                    updated_at=comment.updated_at,
                ) for comment in image.comments],
                edited_cloudinary_url=image.edited_cloudinary_url,
                created_at=image.created_at,
                updated_at=image.updated_at,
            )
            for image in list_images
        ]
        return UserPage(
            user=UserRead(
                id=existing_user.id,
                username=existing_user.username,
                email=existing_user.email,
                avatar=existing_user.avatar,
            ),
            images=images,
        )


user_service = UserService()

current_active_user = user_service.current_active_user
