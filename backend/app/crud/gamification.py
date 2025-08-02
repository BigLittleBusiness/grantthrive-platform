"""
GrantThrive Gamification CRUD Operations
Database operations for user levels, achievements, points, and activities
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.gamification import (
    UserLevel, Achievement, UserAchievement, PointTransaction, 
    ActivityFeed, ActivityLike, ActivityComment
)
from ..schemas.gamification import (
    UserLevelResponse, UserAchievementResponse, ActivityResponse,
    LeaderboardResponse, GamificationStatsResponse, AchievementResponse
)


# User Level and Points
def get_user_level(db: Session, user_id: int) -> UserLevelResponse:
    """Get user's current level and points"""
    user_level = db.query(UserLevel).filter(UserLevel.user_id == user_id).first()
    
    if not user_level:
        # Create initial user level
        user_level = UserLevel(
            user_id=user_id,
            total_points=0,
            level=1,
            current_streak=0,
            longest_streak=0
        )
        db.add(user_level)
        db.commit()
        db.refresh(user_level)
    
    # Calculate points by category
    category_points = db.query(
        PointTransaction.category,
        func.sum(PointTransaction.points).label('total')
    ).filter(
        PointTransaction.user_id == user_id
    ).group_by(PointTransaction.category).all()
    
    points_by_category = {cat: total for cat, total in category_points}
    
    return UserLevelResponse(
        user_id=user_level.user_id,
        total_points=user_level.total_points,
        level=user_level.level,
        points_to_next_level=_calculate_points_to_next_level(user_level.level, user_level.total_points),
        current_streak=user_level.current_streak,
        longest_streak=user_level.longest_streak,
        points_by_category=points_by_category,
        last_activity=user_level.last_activity_date
    )

def award_points(
    db: Session, 
    user_id: int, 
    category: str, 
    points: int, 
    description: str,
    reference_id: Optional[int] = None,
    reference_type: Optional[str] = None
) -> PointTransaction:
    """Award points to user and update level"""
    # Create point transaction
    transaction = PointTransaction(
        user_id=user_id,
        category=category,
        points=points,
        description=description,
        reference_id=reference_id,
        reference_type=reference_type
    )
    db.add(transaction)
    
    # Update user level
    user_level = db.query(UserLevel).filter(UserLevel.user_id == user_id).first()
    if not user_level:
        user_level = UserLevel(user_id=user_id, total_points=0, level=1)
        db.add(user_level)
    
    user_level.total_points += points
    user_level.last_activity_date = datetime.utcnow()
    
    # Calculate new level
    new_level = _calculate_level_from_points(user_level.total_points)
    if new_level > user_level.level:
        user_level.level = new_level
        # Could trigger level-up achievement here
    
    # Update streak if daily activity
    if category == "daily_login":
        _update_daily_streak(db, user_level)
    
    db.commit()
    db.refresh(transaction)
    return transaction

def _calculate_level_from_points(total_points: int) -> int:
    """Calculate user level based on total points"""
    # Level formula: Level = floor(sqrt(total_points / 100)) + 1
    import math
    return int(math.sqrt(total_points / 100)) + 1

def _calculate_points_to_next_level(current_level: int, current_points: int) -> int:
    """Calculate points needed for next level"""
    next_level_points = (current_level ** 2) * 100
    return max(0, next_level_points - current_points)

def _update_daily_streak(db: Session, user_level: UserLevel):
    """Update user's daily activity streak"""
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    if user_level.last_activity_date and user_level.last_activity_date.date() == yesterday:
        user_level.current_streak += 1
    elif user_level.last_activity_date and user_level.last_activity_date.date() != today:
        user_level.current_streak = 1
    else:
        user_level.current_streak = 1
    
    if user_level.current_streak > user_level.longest_streak:
        user_level.longest_streak = user_level.current_streak

# Achievements
def get_user_achievements(
    db: Session, 
    user_id: int, 
    category: Optional[str] = None,
    unlocked_only: bool = False
) -> List[UserAchievementResponse]:
    """Get user's achievements"""
    query = db.query(UserAchievement, Achievement).join(Achievement).filter(
        UserAchievement.user_id == user_id
    )
    
    if category:
        query = query.filter(Achievement.category == category)
    
    if unlocked_only:
        query = query.filter(UserAchievement.unlocked_at.isnot(None))
    
    results = query.order_by(desc(UserAchievement.unlocked_at)).all()
    
    return [
        UserAchievementResponse(
            id=user_ach.id,
            achievement_id=user_ach.achievement_id,
            user_id=user_ach.user_id,
            unlocked_at=user_ach.unlocked_at,
            progress=user_ach.progress,
            achievement=AchievementResponse(
                id=ach.id,
                name=ach.name,
                description=ach.description,
                category=ach.category,
                rarity=ach.rarity,
                points_reward=ach.points_reward,
                icon=ach.icon,
                color=ach.color,
                criteria=ach.criteria,
                is_hidden=ach.is_hidden,
                is_repeatable=ach.is_repeatable
            )
        )
        for user_ach, ach in results
    ]

def get_available_achievements(
    db: Session,
    organization_id: int,
    category: Optional[str] = None,
    rarity: Optional[str] = None
) -> List[AchievementResponse]:
    """Get available achievements catalog"""
    query = db.query(Achievement).filter(
        or_(
            Achievement.organization_id == organization_id,
            Achievement.organization_id.is_(None)  # Global achievements
        )
    )
    
    if category:
        query = query.filter(Achievement.category == category)
    
    if rarity:
        query = query.filter(Achievement.rarity == rarity)
    
    achievements = query.order_by(Achievement.category, Achievement.rarity).all()
    
    return [
        AchievementResponse(
            id=ach.id,
            name=ach.name,
            description=ach.description,
            category=ach.category,
            rarity=ach.rarity,
            points_reward=ach.points_reward,
            icon=ach.icon,
            color=ach.color,
            criteria=ach.criteria,
            is_hidden=ach.is_hidden,
            is_repeatable=ach.is_repeatable
        )
        for ach in achievements
    ]

def unlock_achievement(
    db: Session, 
    user_id: int, 
    achievement_id: int
) -> Optional[UserAchievementResponse]:
    """Unlock achievement for user"""
    # Check if already unlocked
    existing = db.query(UserAchievement).filter(
        and_(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id,
            UserAchievement.unlocked_at.isnot(None)
        )
    ).first()
    
    if existing:
        return None  # Already unlocked
    
    # Get or create user achievement
    user_achievement = db.query(UserAchievement).filter(
        and_(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id
        )
    ).first()
    
    if not user_achievement:
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_id,
            progress=100
        )
        db.add(user_achievement)
    
    user_achievement.unlocked_at = datetime.utcnow()
    user_achievement.progress = 100
    
    # Award points
    achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()
    if achievement and achievement.points_reward > 0:
        award_points(
            db=db, user_id=user_id, category="achievements",
            points=achievement.points_reward,
            description=f"Achievement unlocked: {achievement.name}",
            reference_id=achievement_id, reference_type="achievement"
        )
    
    db.commit()
    db.refresh(user_achievement)
    
    return get_user_achievements(db, user_id)[0]  # Return the unlocked achievement

# Activities
def create_activity(
    db: Session,
    user_id: int,
    activity_type: str,
    title: str,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
    is_public: bool = True
) -> ActivityFeed:
    """Create user activity"""
    activity = ActivityFeed(
        user_id=user_id,
        activity_type=activity_type,
        title=title,
        description=description,
        metadata=metadata or {},
        is_public=is_public
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity

def get_user_activities(
    db: Session,
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    activity_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50
) -> List[ActivityResponse]:
    """Get user activities or community feed"""
    from ..models.user import User
    
    query = db.query(ActivityFeed, User).join(User)
    
    if user_id:
        query = query.filter(ActivityFeed.user_id == user_id)
    elif organization_id:
        query = query.filter(User.organization_id == organization_id)
    
    if activity_type:
        query = query.filter(ActivityFeed.activity_type == activity_type)
    
    if is_public is not None:
        query = query.filter(ActivityFeed.is_public == is_public)
    
    results = query.order_by(desc(ActivityFeed.created_at)).offset(skip).limit(limit).all()
    
    return [
        ActivityResponse(
            id=activity.id,
            user_id=activity.user_id,
            activity_type=activity.activity_type,
            title=activity.title,
            description=activity.description,
            metadata=activity.metadata,
            is_public=activity.is_public,
            like_count=activity.like_count,
            comment_count=activity.comment_count,
            created_at=activity.created_at,
            user_name=f"{user.first_name} {user.last_name}",
            user_avatar=getattr(user, 'avatar_url', None)
        )
        for activity, user in results
    ]

# Leaderboards
def get_leaderboard(
    db: Session,
    organization_id: int,
    category: Optional[str] = None,
    timeframe: str = "all_time",
    limit: int = 50
) -> List[LeaderboardResponse]:
    """Get points leaderboard"""
    from ..models.user import User
    
    # Base query
    query = db.query(
        User.id.label('user_id'),
        User.first_name,
        User.last_name,
        func.sum(PointTransaction.points).label('total_points')
    ).join(PointTransaction).filter(
        User.organization_id == organization_id
    )
    
    # Filter by category
    if category:
        query = query.filter(PointTransaction.category == category)
    
    # Filter by timeframe
    if timeframe == "weekly":
        week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(PointTransaction.created_at >= week_ago)
    elif timeframe == "monthly":
        month_ago = datetime.utcnow() - timedelta(days=30)
        query = query.filter(PointTransaction.created_at >= month_ago)
    
    results = query.group_by(
        User.id, User.first_name, User.last_name
    ).order_by(desc('total_points')).limit(limit).all()
    
    return [
        LeaderboardResponse(
            user_id=result.user_id,
            user_name=f"{result.first_name} {result.last_name}",
            total_points=result.total_points,
            rank=rank
        )
        for rank, result in enumerate(results, 1)
    ]

# Statistics
def get_gamification_stats(db: Session, user_id: int) -> GamificationStatsResponse:
    """Get user's gamification statistics"""
    # Total achievements
    total_achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == user_id,
        UserAchievement.unlocked_at.isnot(None)
    ).count()
    
    # Total activities
    total_activities = db.query(ActivityFeed).filter(ActivityFeed.user_id == user_id).count()
    
    # Total likes received
    total_likes = db.query(func.sum(ActivityFeed.like_count)).filter(
        ActivityFeed.user_id == user_id
    ).scalar() or 0
    
    # Recent achievements (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == user_id,
        UserAchievement.unlocked_at >= thirty_days_ago
    ).count()
    
    return GamificationStatsResponse(
        total_points=get_user_level(db, user_id).total_points,
        current_level=get_user_level(db, user_id).level,
        total_achievements=total_achievements,
        recent_achievements=recent_achievements,
        total_activities=total_activities,
        total_likes_received=total_likes,
        current_streak=get_user_level(db, user_id).current_streak,
        longest_streak=get_user_level(db, user_id).longest_streak
    )

def get_organization_gamification_stats(db: Session, organization_id: int) -> Dict[str, Any]:
    """Get organization-wide gamification statistics"""
    from ..models.user import User
    
    # Active users (users with points)
    active_users = db.query(func.count(func.distinct(PointTransaction.user_id))).join(User).filter(
        User.organization_id == organization_id
    ).scalar()
    
    # Total points awarded
    total_points = db.query(func.sum(PointTransaction.points)).join(User).filter(
        User.organization_id == organization_id
    ).scalar() or 0
    
    # Total achievements unlocked
    total_achievements = db.query(func.count(UserAchievement.id)).join(User).filter(
        User.organization_id == organization_id,
        UserAchievement.unlocked_at.isnot(None)
    ).scalar()
    
    # Total activities
    total_activities = db.query(func.count(ActivityFeed.id)).join(User).filter(
        User.organization_id == organization_id
    ).scalar()
    
    return {
        "active_users": active_users,
        "total_points_awarded": total_points,
        "total_achievements_unlocked": total_achievements,
        "total_activities": total_activities,
        "average_points_per_user": total_points / active_users if active_users > 0 else 0
    }

