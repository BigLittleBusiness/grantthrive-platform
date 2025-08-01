"""
GrantThrive Grant Schemas
Pydantic models for grant and application API serialization
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from ..models.grant import GrantStatus, ApplicationStatus, GrantCategory


# Grant schemas
class GrantBase(BaseModel):
    """Base grant schema with common fields"""
    title: str
    description: str
    objectives: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    application_guidelines: Optional[str] = None
    total_funding: Optional[Decimal] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    category: GrantCategory
    tags: Optional[List[str]] = None
    application_open_date: datetime
    application_close_date: datetime
    decision_date: Optional[datetime] = None
    project_start_date: Optional[datetime] = None
    project_end_date: Optional[datetime] = None
    organization_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    contact_person: Optional[str] = None
    required_documents: Optional[List[str]] = None
    application_form_fields: Optional[Dict[str, Any]] = None


class GrantCreate(GrantBase):
    """Schema for grant creation"""
    organization_id: int
    
    @field_validator('application_close_date')
    @classmethod
    def validate_close_date(cls, v, info):
        if hasattr(info, 'data') and 'application_open_date' in info.data:
            if v <= info.data['application_open_date']:
                raise ValueError('Application close date must be after open date')
        return v


class GrantUpdate(BaseModel):
    """Schema for grant updates"""
    title: Optional[str] = None
    description: Optional[str] = None
    objectives: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    application_guidelines: Optional[str] = None
    total_funding: Optional[Decimal] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    category: Optional[GrantCategory] = None
    tags: Optional[List[str]] = None
    application_open_date: Optional[datetime] = None
    application_close_date: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    project_start_date: Optional[datetime] = None
    project_end_date: Optional[datetime] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_person: Optional[str] = None
    required_documents: Optional[List[str]] = None
    application_form_fields: Optional[Dict[str, Any]] = None
    status: Optional[GrantStatus] = None
    is_featured: Optional[bool] = None


class GrantResponse(GrantBase):
    """Schema for grant response"""
    id: int
    slug: str
    status: GrantStatus
    organization_id: int
    is_featured: bool
    view_count: int
    application_count: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    
    model_config = {"from_attributes": True}


class GrantSummary(BaseModel):
    """Schema for grant summary (list view)"""
    id: int
    title: str
    slug: str
    description: str
    category: GrantCategory
    status: GrantStatus
    total_funding: Optional[Decimal]
    min_amount: Optional[Decimal]
    max_amount: Optional[Decimal]
    application_open_date: datetime
    application_close_date: datetime
    organization_name: str
    is_featured: bool
    application_count: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class GrantList(BaseModel):
    """Schema for paginated grant list"""
    grants: List[GrantSummary]
    total: int
    page: int
    per_page: int
    pages: int


# Application schemas
class ApplicationBase(BaseModel):
    """Base application schema with common fields"""
    project_title: str
    project_description: str
    requested_amount: Decimal
    project_duration: Optional[str] = None
    organization_name: str
    abn_acn: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None
    documents: Optional[List[str]] = None


class ApplicationCreate(ApplicationBase):
    """Schema for application creation"""
    grant_id: int
    
    @field_validator('requested_amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Requested amount must be greater than 0')
        return v


class ApplicationUpdate(BaseModel):
    """Schema for application updates"""
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    requested_amount: Optional[Decimal] = None
    project_duration: Optional[str] = None
    organization_name: Optional[str] = None
    abn_acn: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None
    documents: Optional[List[str]] = None


class ApplicationResponse(ApplicationBase):
    """Schema for application response"""
    id: int
    reference_number: str
    status: ApplicationStatus
    grant_id: int
    applicant_id: int
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[int]
    reviewer_notes: Optional[str]
    feedback: Optional[str]
    score: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ApplicationSummary(BaseModel):
    """Schema for application summary (list view)"""
    id: int
    reference_number: str
    project_title: str
    requested_amount: Decimal
    status: ApplicationStatus
    grant_id: int
    grant_title: str
    organization_name: str
    submitted_at: Optional[datetime]
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ApplicationList(BaseModel):
    """Schema for paginated application list"""
    applications: List[ApplicationSummary]
    total: int
    page: int
    per_page: int
    pages: int


class ApplicationReview(BaseModel):
    """Schema for application review"""
    status: ApplicationStatus
    reviewer_notes: Optional[str] = None
    feedback: Optional[str] = None
    score: Optional[int] = None
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Score must be between 0 and 100')
        return v


# Statistics schemas
class GrantStats(BaseModel):
    """Schema for grant statistics"""
    total_grants: int
    published_grants: int
    draft_grants: int
    closed_grants: int
    total_funding: Decimal
    average_funding: Decimal
    by_category: Dict[str, int]


class ApplicationStats(BaseModel):
    """Schema for application statistics"""
    total_applications: int
    submitted_applications: int
    approved_applications: int
    rejected_applications: int
    pending_applications: int
    total_requested: Decimal
    total_approved: Decimal
    approval_rate: float

