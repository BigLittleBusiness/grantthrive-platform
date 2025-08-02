"""
GrantThrive Gamification Schemas
Pydantic schemas for gamification API endpoints
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AchievementRarityEnum(str, Enum):
    """Achievement rarity levels"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class ActivityTypeEnum(str, Enum):
    """Activity type enumeration"""
    GRANT_APPLIED = "grant_applied"
    GRANT_AWARDED = "grant_awarded"
    FORUM_POST = "forum_post"
    RESOURCE_SHARED = "resource_shared"
    PROFILE_COMPLETED = "profile_completed"
    CONNECTION_MADE = "connection_made"
    EVENT_ATTENDED = "event_attended"
    REVIEW_GIVEN = "review_given"
    STORY_SHARED = "story_shared"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"


# User Level Schemas
class UserLevelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    category: str
    level: int
    total_points: int
    points_to_next_level: int
    current_streak: int
    longest_streak: int
    last_activity: Optional[datetime] = None


# Achievement Schemas
class AchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: str
    category: str
    rarity: str
    points_value: int
    icon: Optional[str] = None
    color: Optional[str] = None
    is_hidden: bool = False
    is_repeatable: bool = False


class UserAchievementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    achievement_id: int
    unlocked_at: datetime
    progress: Optional[Dict[str, Any]] = None
    achievement: Optional[AchievementResponse] = None


# Activity Schemas
class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    activity_type: str
    points_earned: int
    description: str
    metadata: Optional[Dict[str, Any]] = None
    is_public: bool = True
    created_at: datetime


# Leaderboard Schemas
class LeaderboardResponse(BaseModel):
    user_id: int
    username: str
    total_points: int
    level: int
    rank: int
    avatar_url: Optional[str] = None


# Statistics Schemas
class GamificationStatsResponse(BaseModel):
    total_points: int
    current_level: int
    achievements_unlocked: int
    total_achievements: int
    current_streak: int
    longest_streak: int
    rank: Optional[int] = None
    activities_this_week: int
    points_this_week: int

