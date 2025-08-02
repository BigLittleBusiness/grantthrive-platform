"""
GrantThrive Community Schemas
Pydantic schemas for community API endpoints
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ResourceTypeEnum(str, Enum):
    """Resource type enumeration"""
    TEMPLATE = "template"
    GUIDE = "guide"
    CHECKLIST = "checklist"
    EXAMPLE = "example"
    TOOL = "tool"
    VIDEO = "video"
    WEBINAR = "webinar"
    DOCUMENT = "document"
    LINK = "link"


# Forum Category Schemas
class ForumCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    slug: str = Field(..., max_length=100)
    color: str = Field(default="#3B82F6", max_length=7)
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    organization_id: Optional[int] = None
    is_global: bool = Field(default=True)
    requires_approval: bool = Field(default=False)
    moderator_only: bool = Field(default=False)


class ForumCategoryCreate(ForumCategoryBase):
    pass


class ForumCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    requires_approval: Optional[bool] = None
    moderator_only: Optional[bool] = None


class ForumCategory(ForumCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    topic_count: int
    post_count: int
    created_at: datetime
    created_by: Optional[int] = None


# Forum Topic Schemas
class ForumTopicBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    category_id: int
    organization_id: Optional[int] = None
    tags: Optional[List[str]] = None


class ForumTopicCreate(ForumTopicBase):
    pass


class ForumTopicUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    is_locked: Optional[bool] = None


class ForumTopicSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    slug: str
    category_id: int
    author_id: int
    is_pinned: bool
    is_locked: bool
    is_featured: bool
    view_count: int
    reply_count: int
    like_count: int
    last_post_at: datetime
    created_at: datetime


class ForumTopic(ForumTopicBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    author_id: int
    is_pinned: bool
    is_locked: bool
    is_approved: bool
    is_featured: bool
    view_count: int
    reply_count: int
    like_count: int
    last_post_at: datetime
    last_post_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Forum Post Schemas
class ForumPostBase(BaseModel):
    content: str
    topic_id: int
    parent_post_id: Optional[int] = None


class ForumPostCreate(ForumPostBase):
    pass


class ForumPostUpdate(BaseModel):
    content: Optional[str] = None
    is_solution: Optional[bool] = None


class ForumPost(ForumPostBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    author_id: int
    is_approved: bool
    is_solution: bool
    like_count: int
    created_at: datetime
    updated_at: datetime
    edited_at: Optional[datetime] = None
    edited_by: Optional[int] = None


# Resource Category Schemas
class ResourceCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    slug: str = Field(..., max_length=100)
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    organization_id: Optional[int] = None
    is_global: bool = Field(default=True)


class ResourceCategoryCreate(ResourceCategoryBase):
    pass


class ResourceCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ResourceCategory(ResourceCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    resource_count: int
    created_at: datetime
    created_by: Optional[int] = None


# Resource Schemas
class ResourceBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    resource_type: ResourceTypeEnum
    category_id: int
    file_url: Optional[str] = Field(None, max_length=500)
    external_url: Optional[str] = Field(None, max_length=500)
    organization_id: Optional[int] = None
    is_public: bool = Field(default=True)
    tags: Optional[List[str]] = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    resource_type: Optional[ResourceTypeEnum] = None
    category_id: Optional[int] = None
    file_url: Optional[str] = Field(None, max_length=500)
    external_url: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None
    is_featured: Optional[bool] = None
    tags: Optional[List[str]] = None


class ResourceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    slug: str
    description: str
    resource_type: str
    category_id: int
    author_id: int
    is_featured: bool
    download_count: int
    view_count: int
    like_count: int
    rating_average: float
    rating_count: int
    created_at: datetime


class Resource(ResourceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    author_id: int
    is_approved: bool
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    is_featured: bool
    download_count: int
    view_count: int
    like_count: int
    rating_average: float
    rating_count: int
    created_at: datetime
    updated_at: datetime


# Resource Rating Schemas
class ResourceRatingBase(BaseModel):
    resource_id: int
    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = None


class ResourceRatingCreate(ResourceRatingBase):
    pass


class ResourceRatingUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = None


class ResourceRating(ResourceRatingBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# User Follow Schemas
class UserFollowCreate(BaseModel):
    following_id: int


class UserFollow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    follower_id: int
    following_id: int
    created_at: datetime


# Like Schemas
class LikeCreate(BaseModel):
    pass


class TopicLike(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    topic_id: int
    user_id: int
    created_at: datetime


class PostLike(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    post_id: int
    user_id: int
    created_at: datetime


class ResourceLike(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    resource_id: int
    user_id: int
    created_at: datetime


# Statistics Schemas
class ForumStats(BaseModel):
    total_categories: int
    total_topics: int
    total_posts: int
    active_users: int
    recent_topics: int


class ResourceStats(BaseModel):
    total_categories: int
    total_resources: int
    total_downloads: int
    featured_resources: int
    recent_resources: int


class CommunityStats(BaseModel):
    forum_stats: ForumStats
    resource_stats: ResourceStats
    total_users: int
    active_users: int



# ===== NETWORKING SCHEMAS =====

class ConnectionStatusEnum(str, Enum):
    """Connection status enumeration"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


# User Connection Schemas
class UserConnectionBase(BaseModel):
    message: Optional[str] = Field(None, max_length=500)


class UserConnectionCreate(UserConnectionBase):
    requested_id: int


class UserConnectionUpdate(BaseModel):
    status: ConnectionStatusEnum


class UserConnectionResponse(UserConnectionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    requester_id: int
    requested_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# Networking Event Schemas
class NetworkingEventBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    event_type: str = Field(..., max_length=50)  # workshop, webinar, meetup, conference
    event_date: datetime
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    location: Optional[str] = Field(None, max_length=200)
    is_virtual: bool = Field(default=False)
    meeting_link: Optional[str] = Field(None, max_length=500)
    max_participants: Optional[int] = Field(None, ge=1)
    registration_deadline: Optional[datetime] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    organization_id: Optional[int] = None
    is_active: bool = Field(default=True)


class NetworkingEventCreate(NetworkingEventBase):
    pass


class NetworkingEventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    event_type: Optional[str] = Field(None, max_length=50)
    event_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    location: Optional[str] = Field(None, max_length=200)
    is_virtual: Optional[bool] = None
    meeting_link: Optional[str] = Field(None, max_length=500)
    max_participants: Optional[int] = Field(None, ge=1)
    registration_deadline: Optional[datetime] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class NetworkingEventResponse(NetworkingEventBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    organizer_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    registration_count: Optional[int] = 0


# Event Registration Schemas
class EventRegistrationBase(BaseModel):
    registration_notes: Optional[str] = Field(None, max_length=500)


class EventRegistrationCreate(EventRegistrationBase):
    event_id: int


class EventRegistrationResponse(EventRegistrationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_id: int
    user_id: int
    created_at: datetime


# User Interest Schemas
class UserInterestBase(BaseModel):
    interest_name: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, max_length=50)


class UserInterestCreate(UserInterestBase):
    pass


class UserInterestResponse(UserInterestBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime



# ===== SUCCESS STORY SCHEMAS =====

class StoryStatusEnum(str, Enum):
    """Success story status enumeration"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    FEATURED = "featured"


# Success Story Schemas
class SuccessStoryBase(BaseModel):
    title: str = Field(..., max_length=200)
    summary: str = Field(..., max_length=500)
    full_story: str
    project_name: Optional[str] = Field(None, max_length=200)
    grant_amount: Optional[float] = Field(None, ge=0)
    project_duration: Optional[str] = Field(None, max_length=100)
    impact_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    outcomes_achieved: Optional[str] = None
    lessons_learned: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    location: Optional[str] = Field(None, max_length=200)
    organization_name: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[str] = Field(None, max_length=255)
    media_urls: Optional[List[str]] = Field(default_factory=list)
    is_featured: bool = Field(default=False)
    allow_contact: bool = Field(default=True)
    organization_id: Optional[int] = None


class SuccessStoryCreate(SuccessStoryBase):
    pass


class SuccessStoryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    summary: Optional[str] = Field(None, max_length=500)
    full_story: Optional[str] = None
    project_name: Optional[str] = Field(None, max_length=200)
    grant_amount: Optional[float] = Field(None, ge=0)
    project_duration: Optional[str] = Field(None, max_length=100)
    impact_metrics: Optional[Dict[str, Any]] = None
    outcomes_achieved: Optional[str] = None
    lessons_learned: Optional[str] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = Field(None, max_length=200)
    organization_name: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[str] = Field(None, max_length=255)
    media_urls: Optional[List[str]] = None
    is_featured: Optional[bool] = None
    allow_contact: Optional[bool] = None
    status: Optional[StoryStatusEnum] = None


class SuccessStoryResponse(SuccessStoryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    author_id: int
    status: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None


# Story Comment Schemas
class StoryCommentBase(BaseModel):
    content: str = Field(..., max_length=1000)
    parent_id: Optional[int] = None


class StoryCommentCreate(StoryCommentBase):
    pass


class StoryCommentResponse(StoryCommentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    story_id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# Story Like Schema
class StoryLikeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    story_id: int
    user_id: int
    created_at: datetime

