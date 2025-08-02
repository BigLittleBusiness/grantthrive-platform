"""
GrantThrive Notifications Schemas
Pydantic schemas for notifications API endpoints
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from enum import Enum


class NotificationTypeEnum(str, Enum):
    """Notification type enumeration"""
    GRANT_PUBLISHED = "grant_published"
    APPLICATION_RECEIVED = "application_received"
    APPLICATION_STATUS = "application_status"
    FORUM_REPLY = "forum_reply"
    CONNECTION_REQUEST = "connection_request"
    EVENT_REMINDER = "event_reminder"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    MARKETPLACE_BOOKING = "marketplace_booking"
    REVIEW_RECEIVED = "review_received"


class NotificationChannelEnum(str, Enum):
    """Notification delivery channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationPriorityEnum(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# Notification Schemas
class NotificationBase(BaseModel):
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=1000)
    notification_type: NotificationTypeEnum
    priority: NotificationPriorityEnum = NotificationPriorityEnum.NORMAL
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    action_url: Optional[str] = Field(None, max_length=500)
    expires_at: Optional[datetime] = None


class NotificationCreate(NotificationBase):
    user_id: int
    channels: List[NotificationChannelEnum] = Field(default=[NotificationChannelEnum.IN_APP])


class NotificationResponse(NotificationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# Notification Preferences Schemas
class NotificationPreferencesBase(BaseModel):
    email_enabled: bool = Field(default=True)
    sms_enabled: bool = Field(default=False)
    push_enabled: bool = Field(default=True)
    in_app_enabled: bool = Field(default=True)
    quiet_hours_start: Optional[time] = Field(default=time(22, 0))
    quiet_hours_end: Optional[time] = Field(default=time(8, 0))
    timezone: str = Field(default="UTC", max_length=50)


class NotificationPreferencesCreate(NotificationPreferencesBase):
    pass


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    timezone: Optional[str] = Field(None, max_length=50)


class NotificationPreferencesResponse(NotificationPreferencesBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# Notification Category Preferences
class CategoryPreferencesBase(BaseModel):
    category: str = Field(..., max_length=50)
    email_enabled: bool = Field(default=True)
    sms_enabled: bool = Field(default=False)
    push_enabled: bool = Field(default=True)
    in_app_enabled: bool = Field(default=True)


class CategoryPreferencesCreate(CategoryPreferencesBase):
    pass


class CategoryPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None


class CategoryPreferencesResponse(CategoryPreferencesBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# Notification Statistics
class NotificationStatsResponse(BaseModel):
    total_notifications: int
    unread_count: int
    read_count: int
    notifications_this_week: int
    most_common_type: Optional[str] = None

