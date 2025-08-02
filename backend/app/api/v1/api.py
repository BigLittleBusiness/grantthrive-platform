"""
GrantThrive API v1 Router
Main router that includes all API endpoints
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .grants import router as grants_router
from .applications import router as applications_router
from .forums import router as forums_router
from .resources import router as resources_router
from .networking import router as networking_router
from .success_stories import router as success_stories_router
from .marketplace import router as marketplace_router
from .gamification import router as gamification_router
from .notifications import router as notifications_router
from .feature_toggles import router as feature_toggles_router


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

# Include community forum routes
api_router.include_router(
    forums_router,
    prefix="/forums",
    tags=["forums"]
)

# Include resource library routes
api_router.include_router(
    resources_router,
    prefix="/resources",
    tags=["resources"]
)

# Include networking routes
api_router.include_router(
    networking_router,
    prefix="/networking",
    tags=["networking"]
)

# Include success stories routes
api_router.include_router(
    success_stories_router,
    prefix="/success-stories",
    tags=["success-stories"]
)

# Include professional marketplace routes
api_router.include_router(
    marketplace_router,
    prefix="/marketplace",
    tags=["marketplace"]
)

# Include gamification routes
api_router.include_router(
    gamification_router,
    prefix="/gamification",
    tags=["gamification"]
)

# Include notifications routes
api_router.include_router(
    notifications_router,
    prefix="/notifications",
    tags=["notifications"]
)

# Include feature toggles routes
api_router.include_router(
    feature_toggles_router,
    prefix="/features",
    tags=["feature-toggles"]
)

