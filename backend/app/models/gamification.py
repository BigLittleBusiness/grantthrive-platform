"""
GrantThrive Gamification and Notification Models
Database models for gamification system and notifications
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, TEXT
from datetime import datetime
from enum import Enum
import json

from ..db.database import Base


# Custom JSON type for SQLite compatibility
class JSONType(TypeDecorator):
    """JSON type that works with SQLite"""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class AchievementType(str, Enum):
    """Achievement type enumeration"""
    GRANT_APPLICATION = "grant_application"
    GRANT_SUCCESS = "grant_success"
    COMMUNITY_PARTICIPATION = "community_participation"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    NETWORKING = "networking"
    PROFESSIONAL_SERVICES = "professional_services"
    MILESTONE = "milestone"


class NotificationType(str, Enum):
    """Notification type enumeration"""
    GRANT_UPDATE = "grant_update"
    APPLICATION_STATUS = "application_status"
    COMMUNITY_ACTIVITY = "community_activity"
    PROFESSIONAL_SERVICE = "professional_service"
    ACHIEVEMENT = "achievement"
    SYSTEM = "system"
    REMINDER = "reminder"


class UserLevel(Base):
    """User experience levels and progression"""
    __tablename__ = "user_levels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Experience Points
    total_points = Column(Integer, default=0, index=True)
    current_level = Column(Integer, default=1, index=True)
    points_to_next_level = Column(Integer, default=100)
    
    # Category-specific Points
    grant_points = Column(Integer, default=0)
    community_points = Column(Integer, default=0)
    knowledge_points = Column(Integer, default=0)
    networking_points = Column(Integer, default=0)
    professional_points = Column(Integer, default=0)
    
    # Streaks
    daily_login_streak = Column(Integer, default=0)
    max_login_streak = Column(Integer, default=0)
    last_login_date = Column(DateTime)
    
    # Activity Metrics
    grants_applied = Column(Integer, default=0)
    grants_won = Column(Integer, default=0)
    forum_posts = Column(Integer, default=0)
    resources_shared = Column(Integer, default=0)
    connections_made = Column(Integer, default=0)
    events_attended = Column(Integer, default=0)
    
    # Achievements
    total_achievements = Column(Integer, default=0)
    rare_achievements = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    achievements = relationship("UserAchievement", back_populates="user_level")


class Achievement(Base):
    """Available achievements and badges"""
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    
    # Visual
    icon = Column(String(100))  # Icon name or URL
    badge_color = Column(String(7), default="#3B82F6")  # Hex color
    
    # Requirements
    requirements = Column(JSONType)  # Achievement requirements
    points_required = Column(Integer)
    level_required = Column(Integer)
    
    # Rewards
    points_reward = Column(Integer, default=0)
    badge_title = Column(String(100))  # Title user can display
    
    # Rarity and Difficulty
    rarity = Column(String(20), default="common")  # common, uncommon, rare, epic, legendary
    difficulty = Column(String(20), default="easy")  # easy, medium, hard, expert
    
    # Availability
    is_active = Column(Boolean, default=True)
    is_hidden = Column(Boolean, default=False)  # Hidden until unlocked
    is_repeatable = Column(Boolean, default=False)
    
    # Statistics
    total_earned = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    """User earned achievements"""
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False, index=True)
    user_level_id = Column(Integer, ForeignKey("user_levels.id"), nullable=False, index=True)
    
    # Achievement Details
    earned_at = Column(DateTime, default=datetime.utcnow, index=True)
    points_earned = Column(Integer, default=0)
    
    # Progress (for repeatable achievements)
    progress_count = Column(Integer, default=1)
    
    # Display
    is_displayed = Column(Boolean, default=True)  # Show on profile
    is_featured = Column(Boolean, default=False)  # Featured achievement
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    achievement = relationship("Achievement", back_populates="user_achievements")
    user_level = relationship("UserLevel", back_populates="achievements")


class PointTransaction(Base):
    """Point earning and spending transactions"""
    __tablename__ = "point_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Transaction Details
    points = Column(Integer, nullable=False)  # Positive for earning, negative for spending
    transaction_type = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    
    # Source/Reason
    source_type = Column(String(50))  # grant_application, forum_post, resource_share, etc.
    source_id = Column(Integer)  # ID of the source object
    description = Column(Text)
    
    # Multipliers
    base_points = Column(Integer)
    multiplier = Column(Numeric(3, 2), default=1.0)
    bonus_points = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User")


class Leaderboard(Base):
    """Leaderboard entries for different categories and time periods"""
    __tablename__ = "leaderboards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Leaderboard Details
    category = Column(String(50), nullable=False, index=True)  # overall, grants, community, etc.
    time_period = Column(String(20), nullable=False, index=True)  # all_time, yearly, monthly, weekly
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    
    # Rankings
    rank = Column(Integer, nullable=False, index=True)
    points = Column(Integer, nullable=False)
    previous_rank = Column(Integer)
    rank_change = Column(Integer, default=0)
    
    # Additional Metrics
    metric_value = Column(Integer)  # Category-specific metric
    metric_description = Column(String(255))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")


class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    
    # Source Information
    source_type = Column(String(50))  # grant, application, forum_post, etc.
    source_id = Column(Integer)
    source_url = Column(String(500))  # Deep link to relevant page
    
    # Visual
    icon = Column(String(100))
    color = Column(String(7))  # Hex color
    
    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False)
    
    # Delivery
    delivery_method = Column(String(20), default="in_app")  # in_app, email, sms, push
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime)
    
    # Priority and Scheduling
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    scheduled_for = Column(DateTime)  # For scheduled notifications
    expires_at = Column(DateTime)  # Auto-archive after this date
    
    # Grouping
    group_key = Column(String(100))  # For grouping related notifications
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # General Preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    
    # Category Preferences
    grant_updates = Column(Boolean, default=True)
    application_status = Column(Boolean, default=True)
    community_activity = Column(Boolean, default=True)
    professional_services = Column(Boolean, default=True)
    achievements = Column(Boolean, default=True)
    system_updates = Column(Boolean, default=True)
    marketing = Column(Boolean, default=False)
    
    # Frequency Settings
    digest_frequency = Column(String(20), default="daily")  # immediate, daily, weekly, never
    quiet_hours_start = Column(String(5), default="22:00")  # HH:MM format
    quiet_hours_end = Column(String(5), default="08:00")
    timezone = Column(String(50), default="Australia/Sydney")
    
    # Advanced Settings
    notification_sound = Column(Boolean, default=True)
    desktop_notifications = Column(Boolean, default=True)
    mobile_notifications = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")


class ActivityFeed(Base):
    """User activity feed for social features"""
    __tablename__ = "activity_feeds"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Activity Details
    activity_type = Column(String(50), nullable=False, index=True)
    activity_description = Column(Text, nullable=False)
    
    # Source Information
    source_type = Column(String(50))  # grant, forum_post, resource, achievement, etc.
    source_id = Column(Integer)
    source_url = Column(String(500))
    
    # Visibility
    is_public = Column(Boolean, default=True)
    visibility_level = Column(String(20), default="public")  # public, connections, private
    
    # Engagement
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # Metadata
    activity_metadata = Column(JSONType)  # Additional activity-specific data
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User")
    likes = relationship("ActivityLike", back_populates="activity")
    comments = relationship("ActivityComment", back_populates="activity")


class ActivityLike(Base):
    """Activity feed likes"""
    __tablename__ = "activity_likes"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activity_feeds.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    activity = relationship("ActivityFeed", back_populates="likes")
    user = relationship("User")


class ActivityComment(Base):
    """Activity feed comments"""
    __tablename__ = "activity_comments"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activity_feeds.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    
    # Threading
    parent_comment_id = Column(Integer, ForeignKey("activity_comments.id"), nullable=True)
    
    # Engagement
    like_count = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    activity = relationship("ActivityFeed", back_populates="comments")
    user = relationship("User")
    parent_comment = relationship("ActivityComment", remote_side=[id])
    replies = relationship("ActivityComment", back_populates="parent_comment")

