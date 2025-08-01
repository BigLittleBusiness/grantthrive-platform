"""
GrantThrive Grant Models
Comprehensive grant management with application lifecycle support
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from decimal import Decimal
from ..db.database import Base


class GrantStatus(PyEnum):
    """Grant status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class ApplicationStatus(PyEnum):
    """Application status enumeration"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    REQUIRES_CHANGES = "requires_changes"


class GrantCategory(PyEnum):
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
    OTHER = "other"


class Grant(Base):
    """
    Core grant model for managing funding opportunities
    """
    __tablename__ = "grants"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    
    # Grant details
    description = Column(Text, nullable=False)
    objectives = Column(Text, nullable=True)
    eligibility_criteria = Column(Text, nullable=False)
    application_guidelines = Column(Text, nullable=True)
    
    # Financial information
    total_funding = Column(Numeric(12, 2), nullable=False)
    min_amount = Column(Numeric(12, 2), nullable=True)
    max_amount = Column(Numeric(12, 2), nullable=True)
    allocated_amount = Column(Numeric(12, 2), default=0)
    
    # Categorization
    category = Column(Enum(GrantCategory), nullable=False)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Timeline
    application_open_date = Column(DateTime(timezone=True), nullable=False)
    application_close_date = Column(DateTime(timezone=True), nullable=False)
    decision_date = Column(DateTime(timezone=True), nullable=True)
    project_start_date = Column(DateTime(timezone=True), nullable=True)
    project_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Status and visibility
    status = Column(Enum(GrantStatus), nullable=False, default=GrantStatus.DRAFT)
    is_featured = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    
    # Organization (multi-tenant support)
    organization_id = Column(Integer, nullable=False, index=True)
    organization_name = Column(String(255), nullable=False)
    
    # Contact information
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    contact_person = Column(String(255), nullable=True)
    
    # Application requirements
    required_documents = Column(Text, nullable=True)  # JSON string
    application_form_fields = Column(Text, nullable=True)  # JSON string
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    applications = relationship("Application", back_populates="grant")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Grant(id={self.id}, title='{self.title}', status='{self.status.value}')>"
    
    @property
    def is_open(self) -> bool:
        """Check if grant is currently open for applications"""
        from datetime import datetime
        now = datetime.utcnow()
        return (
            self.status == GrantStatus.PUBLISHED and
            self.application_open_date <= now <= self.application_close_date
        )
    
    @property
    def remaining_funding(self) -> Decimal:
        """Calculate remaining funding available"""
        return self.total_funding - self.allocated_amount
    
    @property
    def application_count(self) -> int:
        """Get total number of applications"""
        return len(self.applications)


class Application(Base):
    """
    Grant application model
    """
    __tablename__ = "applications"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Application details
    project_title = Column(String(255), nullable=False)
    project_description = Column(Text, nullable=False)
    requested_amount = Column(Numeric(12, 2), nullable=False)
    project_duration = Column(String(100), nullable=True)
    
    # Applicant information
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_name = Column(String(255), nullable=True)
    abn_acn = Column(String(20), nullable=True)
    
    # Grant association
    grant_id = Column(Integer, ForeignKey("grants.id"), nullable=False)
    
    # Status and workflow
    status = Column(Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.DRAFT)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Review information
    reviewer_notes = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)  # 0-100 scoring system
    
    # Application data
    form_data = Column(Text, nullable=True)  # JSON string for dynamic form data
    documents = Column(Text, nullable=True)  # JSON string for document references
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    grant = relationship("Grant", back_populates="applications")
    applicant = relationship("User", foreign_keys=[applicant_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<Application(id={self.id}, ref='{self.reference_number}', status='{self.status.value}')>"
    
    @property
    def is_editable(self) -> bool:
        """Check if application can be edited"""
        return self.status in [ApplicationStatus.DRAFT, ApplicationStatus.REQUIRES_CHANGES]
    
    @property
    def is_submitted(self) -> bool:
        """Check if application has been submitted"""
        return self.status != ApplicationStatus.DRAFT
    
    def generate_reference_number(self) -> str:
        """Generate unique reference number"""
        from datetime import datetime
        year = datetime.now().year
        return f"GT{year}{self.grant_id:04d}{self.id:06d}"

