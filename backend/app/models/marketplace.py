"""
GrantThrive Professional Services Marketplace Models
Database models for professional services, bookings, and reviews
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric, Enum as SQLEnum
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


class ServiceCategory(str, Enum):
    """Service category enumeration"""
    GRANT_WRITING = "grant_writing"
    FINANCIAL_ADVISORY = "financial_advisory"
    STRATEGIC_CONSULTING = "strategic_consulting"
    LEGAL_ADVISORY = "legal_advisory"
    PROJECT_MANAGEMENT = "project_management"
    EVALUATION_REPORTING = "evaluation_reporting"
    TRAINING_WORKSHOPS = "training_workshops"
    MARKETING_COMMUNICATIONS = "marketing_communications"
    TECHNICAL_SUPPORT = "technical_support"
    OTHER = "other"


class ApplicationStatus(str, Enum):
    """Professional application status"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class BookingStatus(str, Enum):
    """Service booking status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class ProfessionalProfile(Base):
    """Professional service provider profiles"""
    __tablename__ = "professional_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Business Information
    business_name = Column(String(255))
    business_registration = Column(String(100))
    abn_acn = Column(String(50))  # Australian Business Number / Company Number
    
    # Professional Details
    title = Column(String(255), nullable=False)
    bio = Column(Text, nullable=False)
    specializations = Column(JSONType)  # List of specialization areas
    experience_years = Column(Integer)
    
    # Contact Information
    phone = Column(String(20))
    website = Column(String(255))
    linkedin_url = Column(String(255))
    
    # Location
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    postcode = Column(String(10))
    country = Column(String(50), default="Australia")
    
    # Service Areas
    service_areas = Column(JSONType)  # List of geographic service areas
    remote_services = Column(Boolean, default=True)
    
    # Qualifications
    qualifications = Column(JSONType)  # List of qualifications/certifications
    portfolio_items = Column(JSONType)  # List of portfolio items
    
    # Application Status
    application_status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.PENDING, index=True)
    application_date = Column(DateTime, default=datetime.utcnow)
    approval_date = Column(DateTime)
    approved_by = Column(Integer, ForeignKey("users.id"))
    rejection_reason = Column(Text)
    
    # Profile Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Statistics
    total_bookings = Column(Integer, default=0)
    completed_projects = Column(Integer, default=0)
    average_rating = Column(Numeric(3, 2), default=0.0)
    total_reviews = Column(Integer, default=0)
    response_rate = Column(Numeric(5, 2), default=0.0)  # Percentage
    response_time_hours = Column(Integer, default=24)
    
    # Pricing
    hourly_rate_min = Column(Numeric(10, 2))
    hourly_rate_max = Column(Numeric(10, 2))
    project_rate_min = Column(Numeric(10, 2))
    project_rate_max = Column(Numeric(10, 2))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by])
    services = relationship("ProfessionalService", back_populates="professional")
    bookings = relationship("ServiceBooking", back_populates="professional")
    reviews = relationship("ProfessionalReview", back_populates="professional")


class ProfessionalService(Base):
    """Services offered by professionals"""
    __tablename__ = "professional_services"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professional_profiles.id"), nullable=False, index=True)
    
    # Service Details
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(ServiceCategory), nullable=False, index=True)
    
    # Pricing
    pricing_type = Column(String(20), nullable=False)  # hourly, fixed, custom
    hourly_rate = Column(Numeric(10, 2))
    fixed_price = Column(Numeric(10, 2))
    price_description = Column(Text)
    
    # Service Details
    duration_estimate = Column(String(100))  # e.g., "2-4 weeks", "1-2 hours"
    deliverables = Column(JSONType)  # List of deliverables
    requirements = Column(JSONType)  # List of client requirements
    
    # Availability
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    max_concurrent_projects = Column(Integer, default=5)
    
    # Statistics
    booking_count = Column(Integer, default=0)
    completion_rate = Column(Numeric(5, 2), default=0.0)
    average_rating = Column(Numeric(3, 2), default=0.0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    professional = relationship("ProfessionalProfile", back_populates="services")
    bookings = relationship("ServiceBooking", back_populates="service")


class ServiceBooking(Base):
    """Service bookings/appointments"""
    __tablename__ = "service_bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(20), unique=True, nullable=False, index=True)
    
    # Parties
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    professional_id = Column(Integer, ForeignKey("professional_profiles.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("professional_services.id"), nullable=False, index=True)
    
    # Booking Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(JSONType)  # Specific client requirements
    
    # Scheduling
    preferred_start_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    estimated_completion = Column(DateTime)
    actual_completion = Column(DateTime)
    
    # Pricing
    quoted_price = Column(Numeric(10, 2))
    final_price = Column(Numeric(10, 2))
    pricing_notes = Column(Text)
    
    # Status and Communication
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, index=True)
    client_notes = Column(Text)
    professional_notes = Column(Text)
    admin_notes = Column(Text)
    
    # Milestones and Progress
    milestones = Column(JSONType)  # List of project milestones
    progress_updates = Column(JSONType)  # List of progress updates
    
    # Files and Deliverables
    client_files = Column(JSONType)  # Files provided by client
    deliverable_files = Column(JSONType)  # Files delivered by professional
    
    # Communication
    last_message_at = Column(DateTime)
    unread_messages_client = Column(Integer, default=0)
    unread_messages_professional = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("User", foreign_keys=[client_id])
    professional = relationship("ProfessionalProfile", back_populates="bookings")
    service = relationship("ProfessionalService", back_populates="bookings")
    messages = relationship("BookingMessage", back_populates="booking")
    review = relationship("ProfessionalReview", back_populates="booking", uselist=False)


class BookingMessage(Base):
    """Messages within service bookings"""
    __tablename__ = "booking_messages"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("service_bookings.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Message Content
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text, file, milestone, status_update
    
    # File Attachments
    attachments = Column(JSONType)  # List of file attachments
    
    # Status
    is_read = Column(Boolean, default=False)
    is_system_message = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    booking = relationship("ServiceBooking", back_populates="messages")
    sender = relationship("User")


class ProfessionalReview(Base):
    """Reviews and ratings for professionals"""
    __tablename__ = "professional_reviews"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professional_profiles.id"), nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("service_bookings.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Rating (1-5 stars)
    overall_rating = Column(Integer, nullable=False)
    communication_rating = Column(Integer)
    quality_rating = Column(Integer)
    timeliness_rating = Column(Integer)
    value_rating = Column(Integer)
    
    # Review Content
    title = Column(String(255))
    review_text = Column(Text)
    
    # Recommendation
    would_recommend = Column(Boolean)
    
    # Professional Response
    professional_response = Column(Text)
    response_date = Column(DateTime)
    
    # Status
    is_approved = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    professional = relationship("ProfessionalProfile", back_populates="reviews")
    booking = relationship("ServiceBooking", back_populates="review")
    reviewer = relationship("User")


class ProfessionalDocument(Base):
    """Documents uploaded by professionals for verification"""
    __tablename__ = "professional_documents"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professional_profiles.id"), nullable=False, index=True)
    
    # Document Details
    document_type = Column(String(50), nullable=False)  # qualification, insurance, license, portfolio
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # File Information
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"))
    verified_at = Column(DateTime)
    verification_notes = Column(Text)
    
    # Expiry (for licenses, insurance, etc.)
    expiry_date = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    professional = relationship("ProfessionalProfile")
    verifier = relationship("User", foreign_keys=[verified_by])

