"""
GrantThrive Gamification API Endpoints
Handles user levels, achievements, points, and activity tracking
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud.gamification import (
    get_user_level, award_points, get_user_achievements, unlock_achievement,
    create_activity, get_user_activities, get_leaderboard,
    get_gamification_stats, get_available_achievements
)
from app.models.user import User
from app.schemas.gamification import (
    UserLevelResponse, UserAchievementResponse, ActivityResponse,
    LeaderboardResponse, GamificationStatsResponse, AchievementResponse
)

router = APIRouter()

# User Level and Points
@router.get("/level", response_model=UserLevelResponse)
def get_my_level(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's level and points"""
    return get_user_level(db=db, user_id=current_user.id)

@router.post("/points")
def award_user_points(
    category: str,
    points: int,
    description: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Award points to user (internal use)"""
    return award_points(
        db=db, user_id=current_user.id, 
        category=category, points=points, description=description
    )

# Achievements
@router.get("/achievements", response_model=List[UserAchievementResponse])
def get_my_achievements(
    category: Optional[str] = Query(None, description="Filter by achievement category"),
    unlocked_only: bool = Query(False, description="Show only unlocked achievements"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's achievements"""
    return get_user_achievements(
        db=db, user_id=current_user.id, 
        category=category, unlocked_only=unlocked_only
    )

@router.get("/achievements/available", response_model=List[AchievementResponse])
def get_achievements_catalog(
    category: Optional[str] = Query(None, description="Filter by category"),
    rarity: Optional[str] = Query(None, description="Filter by rarity"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get available achievements catalog"""
    return get_available_achievements(
        db=db, organization_id=current_user.organization_id,
        category=category, rarity=rarity
    )

@router.post("/achievements/{achievement_id}/unlock")
def unlock_user_achievement(
    achievement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unlock achievement for user (internal use)"""
    result = unlock_achievement(db=db, user_id=current_user.id, achievement_id=achievement_id)
    if not result:
        raise HTTPException(status_code=400, detail="Achievement already unlocked or not available")
    return {"message": "Achievement unlocked!", "achievement": result}

# Activity Feed
@router.get("/activities", response_model=List[ActivityResponse])
def get_my_activities(
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    is_public: Optional[bool] = Query(None, description="Filter by visibility"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's activity feed"""
    return get_user_activities(
        db=db, user_id=current_user.id,
        activity_type=activity_type, is_public=is_public,
        skip=skip, limit=limit
    )

@router.post("/activities")
def create_user_activity(
    activity_type: str,
    title: str,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
    is_public: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create user activity (internal use)"""
    return create_activity(
        db=db, user_id=current_user.id,
        activity_type=activity_type, title=title,
        description=description, metadata=metadata, is_public=is_public
    )

# Leaderboards
@router.get("/leaderboard", response_model=List[LeaderboardResponse])
def get_points_leaderboard(
    category: Optional[str] = Query(None, description="Filter by points category"),
    timeframe: str = Query("all_time", description="Timeframe: all_time, monthly, weekly"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get points leaderboard"""
    return get_leaderboard(
        db=db, organization_id=current_user.organization_id,
        category=category, timeframe=timeframe, limit=limit
    )

@router.get("/leaderboard/my-rank")
def get_my_leaderboard_rank(
    category: Optional[str] = Query(None, description="Points category"),
    timeframe: str = Query("all_time", description="Timeframe: all_time, monthly, weekly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's leaderboard rank"""
    leaderboard = get_leaderboard(
        db=db, organization_id=current_user.organization_id,
        category=category, timeframe=timeframe, limit=1000
    )
    
    for rank, entry in enumerate(leaderboard, 1):
        if entry.user_id == current_user.id:
            return {
                "rank": rank,
                "total_points": entry.total_points,
                "total_users": len(leaderboard)
            }
    
    return {
        "rank": None,
        "total_points": 0,
        "total_users": len(leaderboard)
    }

# Statistics
@router.get("/stats", response_model=GamificationStatsResponse)
def get_my_gamification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's gamification statistics"""
    return get_gamification_stats(db=db, user_id=current_user.id)

# Community Feed (Public Activities)
@router.get("/community-feed", response_model=List[ActivityResponse])
def get_community_activity_feed(
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get community activity feed (public activities)"""
    return get_user_activities(
        db=db, user_id=None,  # All users
        organization_id=current_user.organization_id,
        activity_type=activity_type, is_public=True,
        skip=skip, limit=limit
    )

# Admin endpoints
@router.get("/admin/stats")
def get_organization_gamification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organization-wide gamification statistics"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get organization stats
    from app.crud.gamification import get_organization_gamification_stats
    return get_organization_gamification_stats(db=db, organization_id=current_user.organization_id)

