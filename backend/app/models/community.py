"""
GrantThrive Community Models
Database models for community features including forums, resources, and networking
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


class ForumCategory(Base):
    """Forum categories for organizing discussions"""
    __tablename__ = "forum_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    color = Column(String(7), default="#3B82F6")  # Hex color
    icon = Column(String(50))  # Icon name/class
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Organization-specific categories
    organization_id = Column(Integer, ForeignKey("users.organization_id"), nullable=True, index=True)
    is_global = Column(Boolean, default=True)  # Global vs organization-specific
    
    # Moderation
    requires_approval = Column(Boolean, default=False)
    moderator_only = Column(Boolean, default=False)
    
    # Statistics
    topic_count = Column(Integer, default=0)
    post_count = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    topics = relationship("ForumTopic", back_populates="category")
    creator = relationship("User", foreign_keys=[created_by])


class ForumTopic(Base):
    """Forum topics/threads"""
    __tablename__ = "forum_topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # Category and organization
    category_id = Column(Integer, ForeignKey("forum_categories.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("users.organization_id"), nullable=True, index=True)
    
    # Author
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Status and moderation
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Statistics
    view_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    # Last activity
    last_post_at = Column(DateTime, default=datetime.utcnow)
    last_post_by = Column(Integer, ForeignKey("users.id"))
    
    # Tags
    tags = Column(JSONType)  # List of tags
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("ForumCategory", back_populates="topics")
    author = relationship("User", foreign_keys=[author_id])
    last_poster = relationship("User", foreign_keys=[last_post_by])
    posts = relationship("ForumPost", back_populates="topic")
    likes = relationship("ForumTopicLike", back_populates="topic")


class ForumPost(Base):
    """Forum posts/replies"""
    __tablename__ = "forum_posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    
    # Topic and author
    topic_id = Column(Integer, ForeignKey("forum_topics.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Reply structure
    parent_post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=True, index=True)
    
    # Status and moderation
    is_approved = Column(Boolean, default=True)
    is_solution = Column(Boolean, default=False)  # Marked as solution to topic
    
    # Statistics
    like_count = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    edited_at = Column(DateTime)
    edited_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    topic = relationship("ForumTopic", back_populates="posts")
    author = relationship("User", foreign_keys=[author_id])
    editor = relationship("User", foreign_keys=[edited_by])
    parent_post = relationship("ForumPost", remote_side=[id])
    replies = relationship("ForumPost", back_populates="parent_post")
    likes = relationship("ForumPostLike", back_populates="post")


class ForumTopicLike(Base):
    """Topic likes/reactions"""
    __tablename__ = "forum_topic_likes"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("forum_topics.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    topic = relationship("ForumTopic", back_populates="likes")
    user = relationship("User")


class ForumPostLike(Base):
    """Post likes/reactions"""
    __tablename__ = "forum_post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("ForumPost", back_populates="likes")
    user = relationship("User")


class ResourceCategory(Base):
    """Categories for resource library"""
    __tablename__ = "resource_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Organization-specific categories
    organization_id = Column(Integer, ForeignKey("users.organization_id"), nullable=True, index=True)
    is_global = Column(Boolean, default=True)
    
    # Statistics
    resource_count = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    resources = relationship("Resource", back_populates="category")
    creator = relationship("User", foreign_keys=[created_by])


class ResourceType(str, Enum):
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


class Resource(Base):
    """Resource library items"""
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    
    # Content
    resource_type = Column(String(20), nullable=False, index=True)
    file_url = Column(String(500))  # File path or external URL
    file_name = Column(String(255))
    file_size = Column(Integer)  # Size in bytes
    mime_type = Column(String(100))
    
    # External link
    external_url = Column(String(500))
    
    # Categorization
    category_id = Column(Integer, ForeignKey("resource_categories.id"), nullable=False, index=True)
    tags = Column(JSONType)  # List of tags
    
    # Organization and access
    organization_id = Column(Integer, ForeignKey("users.organization_id"), nullable=True, index=True)
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Author and approval
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_approved = Column(Boolean, default=True)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    
    # Statistics
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    rating_average = Column(Numeric(3, 2), default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("ResourceCategory", back_populates="resources")
    author = relationship("User", foreign_keys=[author_id])
    approver = relationship("User", foreign_keys=[approved_by])
    likes = relationship("ResourceLike", back_populates="resource")
    ratings = relationship("ResourceRating", back_populates="resource")


class ResourceLike(Base):
    """Resource likes"""
    __tablename__ = "resource_likes"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resource = relationship("Resource", back_populates="likes")
    user = relationship("User")


class ResourceRating(Base):
    """Resource ratings"""
    __tablename__ = "resource_ratings"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    resource = relationship("Resource", back_populates="ratings")
    user = relationship("User")


class UserFollow(Base):
    """User following relationships"""
    __tablename__ = "user_follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    follower = relationship("User", foreign_keys=[follower_id])
    following = relationship("User", foreign_keys=[following_id])

