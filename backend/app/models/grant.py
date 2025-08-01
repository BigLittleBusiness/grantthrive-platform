"""
GrantThrive Grant Models
Database models for grant management system
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, TEXT
from datetime import datetime
from enum import Enum
import json

from ..db.database import Base


class GrantStatus(str, Enum):
    """Grant status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"


class GrantCategory(str, Enum):
    """Grant category enumeration"""
    COMMUNITY = "community"
    ENVIRONMENT = "environment"
    ARTS_CULTURE = "arts_culture"
    SPORTS_RECREATION = "sports_recreation"
    EDUCATION = "education"
    HEALTH = "health"
    INFRASTRUCTURE = "infrastructure"
    ECONOMIC_DEVELOPMENT = "economic_development"
    YOUTH = "youth"
    SENIORS = "seniors"
    DISABILITY = "disability"
    INDIGENOUS = "indigenous"
    OTHER = "other"


class ApplicationStatus(str, Enum):
    """Application status enumeration"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


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


class Grant(Base):
    """Grant model for managing funding opportunities"""
    __tablename__ = "grants"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    objectives = Column(Text)
    eligibility_criteria = Column(Text)
    application_guidelines = Column(Text)
    
    # Funding details
    total_funding = Column(Numeric(15, 2))
    min_amount = Column(Numeric(15, 2))
    max_amount = Column(Numeric(15, 2))
    allocated_amount = Column(Numeric(15, 2), default=0)
    
    # Categorization
    category = Column(String(50), nullable=False, index=True)
    tags = Column(JSONType)  # List of tags
    
    # Timeline
    application_open_date = Column(DateTime, nullable=False)
    application_close_date = Column(DateTime, nullable=False)
    decision_date = Column(DateTime)
    project_start_date = Column(DateTime)
    project_end_date = Column(DateTime)
    
    # Status and features
    status = Column(String(20), default=GrantStatus.DRAFT, index=True)
    is_featured = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    
    # Organization details
    organization_id = Column(Integer, ForeignKey("users.organization_id"), index=True)
    organization_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50))
    contact_person = Column(String(255))
    
    # Application requirements
    required_documents = Column(JSONType)  # List of required documents
    application_form_fields = Column(JSONType)  # Custom form fields
    
    # Metrics
    view_count = Column(Integer, default=0)
    application_count = Column(Integer, default=0)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    applications = relationship("Application", back_populates="grant")
    creator = relationship("User", foreign_keys=[created_by])


class Application(Base):
    """Application model for grant applications"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String(50), unique=True, index=True)
    
    # Project details
    project_title = Column(String(255), nullable=False)
    project_description = Column(Text, nullable=False)
    requested_amount = Column(Numeric(15, 2), nullable=False)
    project_duration = Column(String(100))
    
    # Applicant details
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_name = Column(String(255), nullable=False)
    abn_acn = Column(String(50))
    
    # Grant relationship
    grant_id = Column(Integer, ForeignKey("grants.id"), nullable=False, index=True)
    
    # Application data
    form_data = Column(JSONType)  # Custom form responses
    documents = Column(JSONType)  # List of uploaded documents
    
    # Status and workflow
    status = Column(String(20), default=ApplicationStatus.DRAFT, index=True)
    submitted_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    
    # Review details
    reviewer_notes = Column(Text)
    feedback = Column(Text)
    score = Column(Integer)  # 0-100 score
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    grant = relationship("Grant", back_populates="applications")
    applicant = relationship("User", foreign_keys=[applicant_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

