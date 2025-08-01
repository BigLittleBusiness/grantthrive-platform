"""
GrantThrive API v1 Router
Main router that includes all API endpoints
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .grants import router as grants_router
from .applications import router as applications_router


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

# Include grant management routes
api_router.include_router(
    grants_router,
    prefix="/grants",
    tags=["grants"]
)

# Include application management routes
api_router.include_router(
    applications_router,
    prefix="/applications",
    tags=["applications"]
)

