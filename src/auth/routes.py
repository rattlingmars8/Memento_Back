from fastapi import APIRouter
from src.auth.utils.get_routes import auth_routes


router = APIRouter(tags=["auth"])
router.include_router(auth_routes.generate_register_route(), prefix="/auth")
router.include_router(auth_routes.generate_login_route(), prefix="/auth")
router.include_router(auth_routes.generate_logout_route(), prefix="/auth")
router.include_router(auth_routes.generate_refresh_route(), prefix="/auth")
router.include_router(auth_routes.verify_email_route(), prefix="/auth")
router.include_router(auth_routes.get_forget_routes(), prefix="/forgot")

router.include_router(auth_routes.get_user_page(), prefix="/users")

