from fastapi import APIRouter
from .user_routes import user_router
from .auth_routes import auth_router
router = APIRouter()
router.include_router(user_router)
router.include_router(auth_router)