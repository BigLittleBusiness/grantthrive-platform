"""
GrantThrive API v1 Router
Main router that includes all API endpoints
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router


api_router = APIRouter()

# Include authentication routes
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

# Include user management routes
api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)

