"""
GrantThrive Success Stories and Networking Models
Database models for success stories showcase and networking features
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


class StoryStatus(str, Enum):
    """Success story status"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    FEATURED = "featured"


class SuccessStory(Base):
    """Success stories showcase"""
    __tablename__ = "success_stories"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    
    # Grant Information
    grant_id = Column(Integer, ForeignKey("grants.id"), nullable=True, index=True)
    grant_title = Column(String(255))  # In case grant is deleted
    grant_amount = Column(Numeric(12, 2))
    funding_organization = Column(String(255))
    
    # Organization Information
    organization_id = Column(Integer, ForeignKey("users.organization_id"), nullable=True, index=True)
    organization_name = Column(String(255), nullable=False)
    organization_type = Column(String(100))  # nonprofit, community_group, business, etc.
    organization_size = Column(String(50))  # small, medium, large
    
    # Project Details
    project_category = Column(String(100))  # education, health, environment, etc.
    project_duration = Column(String(100))  # e.g., "6 months", "2 years"
    beneficiaries_count = Column(Integer)
    beneficiaries_description = Column(Text)
    
    # Impact Metrics
    impact_metrics = Column(JSONType)  # List of impact measurements
    outcomes_achieved = Column(JSONType)  # List of key outcomes
    lessons_learned = Column(JSONType)  # List of lessons learned
    
    # Media
    featured_image_url = Column(String(500))
    gallery_images = Column(JSONType)  # List of image URLs
    video_url = Column(String(500))
    
    # Author and Attribution
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    author_name = Column(String(255))
    author_title = Column(String(255))
    
    # Professional Services (if applicable)
    used_professional_services = Column(Boolean, default=False)
    professional_services_used = Column(JSONType)  # List of services used
    professional_testimonial = Column(Text)
    
    # Status and Moderation
    status = Column(String(20), default=StoryStatus.DRAFT.value, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    is_public = Column(Boolean, default=True)
    
    # Approval Workflow
    submitted_at = Column(DateTime)
    approved_at = Column(DateTime)
    approved_by = Column(Integer, ForeignKey("users.id"))
    rejection_reason = Column(Text)
    
    # Engagement
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    # SEO and Discovery
    tags = Column(JSONType)  # List of tags
    location = Column(String(255))  # Project location
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    grant = relationship("Grant", foreign_keys=[grant_id])
    author = relationship("User", foreign_keys=[author_id])
    approver = relationship("User", foreign_keys=[approved_by])
    likes = relationship("StoryLike", back_populates="story")
    comments = relationship("StoryComment", back_populates="story")


class StoryLike(Base):
    """Success story likes"""
    __tablename__ = "story_likes"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("success_stories.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    story = relationship("SuccessStory", back_populates="likes")
    user = relationship("User")


class StoryComment(Base):
    """Success story comments"""
    __tablename__ = "story_comments"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("success_stories.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    
    # Threading
    parent_comment_id = Column(Integer, ForeignKey("story_comments.id"), nullable=True, index=True)
    
    # Moderation
    is_approved = Column(Boolean, default=True)
    
    # Engagement
    like_count = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    story = relationship("SuccessStory", back_populates="comments")
    author = relationship("User")
    parent_comment = relationship("StoryComment", remote_side=[id])
    replies = relationship("StoryComment", back_populates="parent_comment")
    likes = relationship("CommentLike", back_populates="comment")


class CommentLike(Base):
    """Story comment likes"""
    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("story_comments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    comment = relationship("StoryComment", back_populates="likes")
    user = relationship("User")


class UserConnection(Base):
    """User networking connections"""
    __tablename__ = "user_connections"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Connection Details
    status = Column(String(20), default="pending", index=True)  # pending, accepted, declined, blocked
    message = Column(Text)  # Optional message with connection request
    
    # Mutual Connection
    is_mutual = Column(Boolean, default=False)
    
    # Interaction History
    last_interaction = Column(DateTime)
    interaction_count = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    recipient = relationship("User", foreign_keys=[recipient_id])


class NetworkingEvent(Base):
    """Networking events and webinars"""
    __tablename__ = "networking_events"

    id = Column(Integer, primary_key=True, index=True)
    
    # Event Details
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    event_type = Column(String(50), nullable=False)  # webinar, workshop, networking, conference
    
    # Scheduling
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, nullable=False)
    timezone = Column(String(50), default="Australia/Sydney")
    
    # Location/Platform
    is_virtual = Column(Boolean, default=True)
    venue_name = Column(String(255))
    venue_address = Column(Text)
    meeting_url = Column(String(500))
    meeting_password = Column(String(100))
    
    # Organization
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("users.organization_id"), nullable=True, index=True)
    
    # Capacity and Registration
    max_attendees = Column(Integer)
    registration_required = Column(Boolean, default=True)
    registration_deadline = Column(DateTime)
    is_free = Column(Boolean, default=True)
    cost = Column(Numeric(10, 2))
    
    # Content
    agenda = Column(JSONType)  # List of agenda items
    speakers = Column(JSONType)  # List of speaker information
    materials = Column(JSONType)  # List of materials/resources
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    status = Column(String(20), default="upcoming")  # upcoming, live, completed, cancelled
    
    # Engagement
    registration_count = Column(Integer, default=0)
    attendance_count = Column(Integer, default=0)
    
    # Recording
    recording_url = Column(String(500))
    recording_available = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organizer = relationship("User", foreign_keys=[organizer_id])
    registrations = relationship("EventRegistration", back_populates="event")


class EventRegistration(Base):
    """Event registrations"""
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("networking_events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Registration Details
    registration_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="registered")  # registered, attended, no_show, cancelled
    
    # Additional Information
    questions_responses = Column(JSONType)  # Responses to registration questions
    dietary_requirements = Column(Text)
    accessibility_needs = Column(Text)
    
    # Attendance
    attended = Column(Boolean, default=False)
    attendance_duration = Column(Integer)  # Minutes attended
    
    # Feedback
    rating = Column(Integer)  # 1-5 stars
    feedback = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = relationship("NetworkingEvent", back_populates="registrations")
    user = relationship("User")


class UserInterest(Base):
    """User interests for networking and content recommendations"""
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Interest Categories
    grant_categories = Column(JSONType)  # List of grant categories of interest
    project_types = Column(JSONType)  # List of project types
    funding_amounts = Column(JSONType)  # Preferred funding ranges
    geographic_areas = Column(JSONType)  # Geographic areas of interest
    
    # Professional Interests
    service_categories = Column(JSONType)  # Professional services of interest
    collaboration_interests = Column(JSONType)  # Types of collaboration sought
    
    # Learning Preferences
    learning_topics = Column(JSONType)  # Topics for learning/development
    event_preferences = Column(JSONType)  # Preferred event types
    
    # Communication Preferences
    newsletter_frequency = Column(String(20), default="weekly")  # daily, weekly, monthly, never
    notification_preferences = Column(JSONType)  # Notification settings
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

