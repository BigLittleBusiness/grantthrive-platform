"""
GrantThrive Professional Services Marketplace Schemas
Pydantic schemas for marketplace API endpoints
"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal


class ServiceCategoryEnum(str, Enum):
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


class ApplicationStatusEnum(str, Enum):
    """Professional application status"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class BookingStatusEnum(str, Enum):
    """Service booking status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class PricingTypeEnum(str, Enum):
    """Pricing type enumeration"""
    HOURLY = "hourly"
    FIXED = "fixed"
    CUSTOM = "custom"


# Professional Profile Schemas
class ProfessionalProfileBase(BaseModel):
    business_name: Optional[str] = Field(None, max_length=255)
    business_registration: Optional[str] = Field(None, max_length=100)
    abn_acn: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., max_length=255)
    bio: str
    specializations: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    postcode: Optional[str] = Field(None, max_length=10)
    country: str = Field(default="Australia", max_length=50)
    service_areas: Optional[List[str]] = None
    remote_services: bool = Field(default=True)
    qualifications: Optional[List[Dict[str, Any]]] = None
    portfolio_items: Optional[List[Dict[str, Any]]] = None
    hourly_rate_min: Optional[Decimal] = Field(None, ge=0)
    hourly_rate_max: Optional[Decimal] = Field(None, ge=0)
    project_rate_min: Optional[Decimal] = Field(None, ge=0)
    project_rate_max: Optional[Decimal] = Field(None, ge=0)


class ProfessionalProfileCreate(ProfessionalProfileBase):
    pass


class ProfessionalProfileUpdate(BaseModel):
    business_name: Optional[str] = Field(None, max_length=255)
    business_registration: Optional[str] = Field(None, max_length=100)
    abn_acn: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    specializations: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    postcode: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=50)
    service_areas: Optional[List[str]] = None
    remote_services: Optional[bool] = None
    qualifications: Optional[List[Dict[str, Any]]] = None
    portfolio_items: Optional[List[Dict[str, Any]]] = None
    hourly_rate_min: Optional[Decimal] = Field(None, ge=0)
    hourly_rate_max: Optional[Decimal] = Field(None, ge=0)
    project_rate_min: Optional[Decimal] = Field(None, ge=0)
    project_rate_max: Optional[Decimal] = Field(None, ge=0)


class ProfessionalProfileSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    business_name: Optional[str] = None
    title: str
    bio: str
    specializations: Optional[List[str]] = None
    experience_years: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    remote_services: bool
    application_status: ApplicationStatusEnum
    is_active: bool
    is_featured: bool
    is_verified: bool
    total_bookings: int
    completed_projects: int
    average_rating: float
    total_reviews: int
    response_rate: float
    response_time_hours: int
    hourly_rate_min: Optional[Decimal] = None
    hourly_rate_max: Optional[Decimal] = None
    created_at: datetime


class ProfessionalProfile(ProfessionalProfileBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    application_status: ApplicationStatusEnum
    application_date: datetime
    approval_date: Optional[datetime] = None
    approved_by: Optional[int] = None
    rejection_reason: Optional[str] = None
    is_active: bool
    is_featured: bool
    is_verified: bool
    total_bookings: int
    completed_projects: int
    average_rating: float
    total_reviews: int
    response_rate: float
    response_time_hours: int
    created_at: datetime
    updated_at: datetime


# Professional Service Schemas
class ProfessionalServiceBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    category: ServiceCategoryEnum
    pricing_type: PricingTypeEnum
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    fixed_price: Optional[Decimal] = Field(None, ge=0)
    price_description: Optional[str] = None
    duration_estimate: Optional[str] = Field(None, max_length=100)
    deliverables: Optional[List[str]] = None
    requirements: Optional[List[str]] = None
    max_concurrent_projects: int = Field(default=5, ge=1, le=20)


class ProfessionalServiceCreate(ProfessionalServiceBase):
    pass


class ProfessionalServiceUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[ServiceCategoryEnum] = None
    pricing_type: Optional[PricingTypeEnum] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    fixed_price: Optional[Decimal] = Field(None, ge=0)
    price_description: Optional[str] = None
    duration_estimate: Optional[str] = Field(None, max_length=100)
    deliverables: Optional[List[str]] = None
    requirements: Optional[List[str]] = None
    is_active: Optional[bool] = None
    max_concurrent_projects: Optional[int] = Field(None, ge=1, le=20)


class ProfessionalService(ProfessionalServiceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    professional_id: int
    is_active: bool
    is_featured: bool
    booking_count: int
    completion_rate: float
    average_rating: float
    created_at: datetime
    updated_at: datetime


# Service Booking Schemas
class ServiceBookingBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    requirements: Optional[List[str]] = None
    preferred_start_date: Optional[datetime] = None
    client_notes: Optional[str] = None


class ServiceBookingCreate(ServiceBookingBase):
    service_id: int


class ServiceBookingUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    preferred_start_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    quoted_price: Optional[Decimal] = Field(None, ge=0)
    final_price: Optional[Decimal] = Field(None, ge=0)
    pricing_notes: Optional[str] = None
    status: Optional[BookingStatusEnum] = None
    client_notes: Optional[str] = None
    professional_notes: Optional[str] = None


class ServiceBookingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    booking_reference: str
    title: str
    service_id: int
    client_id: int
    professional_id: int
    status: BookingStatusEnum
    quoted_price: Optional[Decimal] = None
    preferred_start_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    created_at: datetime


class ServiceBooking(ServiceBookingBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    booking_reference: str
    client_id: int
    professional_id: int
    service_id: int
    actual_start_date: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    quoted_price: Optional[Decimal] = None
    final_price: Optional[Decimal] = None
    pricing_notes: Optional[str] = None
    status: BookingStatusEnum
    professional_notes: Optional[str] = None
    admin_notes: Optional[str] = None
    milestones: Optional[List[Dict[str, Any]]] = None
    progress_updates: Optional[List[Dict[str, Any]]] = None
    client_files: Optional[List[Dict[str, Any]]] = None
    deliverable_files: Optional[List[Dict[str, Any]]] = None
    last_message_at: Optional[datetime] = None
    unread_messages_client: int
    unread_messages_professional: int
    created_at: datetime
    updated_at: datetime


# Booking Message Schemas
class BookingMessageBase(BaseModel):
    message: str
    message_type: str = Field(default="text")
    attachments: Optional[List[Dict[str, Any]]] = None


class BookingMessageCreate(BookingMessageBase):
    pass


class BookingMessage(BookingMessageBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    booking_id: int
    sender_id: int
    is_read: bool
    is_system_message: bool
    created_at: datetime


# Professional Review Schemas
class ProfessionalReviewBase(BaseModel):
    overall_rating: int = Field(..., ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    timeliness_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    review_text: Optional[str] = None
    would_recommend: Optional[bool] = None


class ProfessionalReviewCreate(ProfessionalReviewBase):
    pass


class ProfessionalReviewUpdate(BaseModel):
    professional_response: str


class ProfessionalReview(ProfessionalReviewBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    professional_id: int
    booking_id: int
    reviewer_id: int
    professional_response: Optional[str] = None
    response_date: Optional[datetime] = None
    is_approved: bool
    is_featured: bool
    created_at: datetime
    updated_at: datetime


# Professional Document Schemas
class ProfessionalDocumentBase(BaseModel):
    document_type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    expiry_date: Optional[datetime] = None


class ProfessionalDocumentCreate(ProfessionalDocumentBase):
    pass


class ProfessionalDocument(ProfessionalDocumentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    professional_id: int
    file_url: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    is_verified: bool
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Application Schemas
class ProfessionalApplicationCreate(BaseModel):
    profile: ProfessionalProfileCreate
    documents: Optional[List[ProfessionalDocumentCreate]] = None


class ProfessionalApplicationReview(BaseModel):
    status: ApplicationStatusEnum
    rejection_reason: Optional[str] = None
    admin_notes: Optional[str] = None


# Statistics Schemas
class MarketplaceStats(BaseModel):
    total_professionals: int
    active_professionals: int
    pending_applications: int
    total_services: int
    total_bookings: int
    completed_bookings: int
    average_rating: float
    categories_count: Dict[str, int]

