"""
GrantThrive Application Management API
Grant application CRUD operations and workflow management
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...crud.grant import (
    get_applications,
    get_application,
    get_application_by_reference,
    create_application,
    update_application,
    submit_application,
    review_application,
    get_applications_count,
    get_user_applications,
    get_grant_applications,
    get_grant
)
from ...schemas.grant import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationSummary,
    ApplicationList,
    ApplicationReview,
    ApplicationStats
)
from ...api.deps import (
    get_current_user,
    get_current_applicant,
    get_current_client_user,
    get_current_admin_user,
    require_organization_access
)
from ...models.user import User, UserRole
from ...models.grant import ApplicationStatus, GrantStatus
from datetime import datetime


router = APIRouter()


@router.get("/", response_model=ApplicationList)
def list_applications(
    skip: int = Query(0, ge=0, description="Number of applications to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of applications to return"),
    status: Optional[ApplicationStatus] = Query(None, description="Filter by application status"),
    grant_id: Optional[int] = Query(None, description="Filter by grant ID"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List applications with filtering and pagination
    Access control based on user role
    """
    applicant_id = None
    
    # Applicants can only see their own applications
    if current_user.role == UserRole.APPLICANT:
        applicant_id = current_user.id
        organization_id = None  # Applicants can't filter by organization
    
    # Client users can only see applications for their organization's grants
    elif current_user.is_client_user and current_user.role != UserRole.SUPER_ADMIN:
        organization_id = current_user.organization_id
    
    applications = get_applications(
        db,
        skip=skip,
        limit=limit,
        status=status,
        grant_id=grant_id,
        applicant_id=applicant_id,
        organization_id=organization_id
    )
    
    total = get_applications_count(
        db,
        status=status,
        grant_id=grant_id,
        applicant_id=applicant_id,
        organization_id=organization_id
    )
    
    return {
        "applications": applications,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "pages": (total + limit - 1) // limit
    }


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_new_application(
    application_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new grant application
    Available to all authenticated users
    """
    # Check if grant exists and is open for applications
    grant = get_grant(db, application_data.grant_id)
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant not found"
        )
    
    if grant.status != GrantStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grant is not open for applications"
        )
    
    # Check if application period is open
    now = datetime.utcnow()
    if now < grant.application_open_date or now > grant.application_close_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grant application period is not currently open"
        )
    
    # Check if user already has an application for this grant
    existing_applications = get_applications(
        db,
        grant_id=application_data.grant_id,
        applicant_id=current_user.id
    )
    if existing_applications:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an application for this grant"
        )
    
    # Validate requested amount against grant limits
    if grant.min_amount and application_data.requested_amount < grant.min_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested amount must be at least ${grant.min_amount}"
        )
    
    if grant.max_amount and application_data.requested_amount > grant.max_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested amount cannot exceed ${grant.max_amount}"
        )
    
    application = create_application(db, application_data, current_user.id)
    
    # Update grant application count
    grant.application_count += 1
    db.commit()
    
    return application


@router.get("/my", response_model=List[ApplicationSummary])
def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get current user's applications
    """
    applications = get_user_applications(db, current_user.id)
    return applications


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application_by_id(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get application by ID
    Access control based on user role and ownership
    """
    application = get_application(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check access permissions
    can_access = False
    
    # Applicant can access their own applications
    if current_user.id == application.applicant_id:
        can_access = True
    
    # Client users can access applications for their organization's grants
    elif current_user.is_client_user:
        grant = get_grant(db, application.grant_id)
        if grant and grant.organization_id == current_user.organization_id:
            can_access = True
    
    # Super admins can access all applications
    elif current_user.role == UserRole.SUPER_ADMIN:
        can_access = True
    
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this application not allowed"
        )
    
    return application


@router.get("/reference/{reference_number}", response_model=ApplicationResponse)
def get_application_by_reference(
    reference_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get application by reference number
    Access control based on user role and ownership
    """
    application = get_application_by_reference(db, reference_number)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Same access control logic as get_application_by_id
    can_access = False
    
    if current_user.id == application.applicant_id:
        can_access = True
    elif current_user.is_client_user:
        grant = get_grant(db, application.grant_id)
        if grant and grant.organization_id == current_user.organization_id:
            can_access = True
    elif current_user.role == UserRole.SUPER_ADMIN:
        can_access = True
    
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this application not allowed"
        )
    
    return application


@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application_by_id(
    application_id: int,
    application_update: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update application by ID
    Only applicant can update their own draft applications
    """
    application = get_application(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Only applicant can update their own applications
    if current_user.id != application.applicant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own applications"
        )
    
    # Can only update draft applications
    if application.status != ApplicationStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update draft applications"
        )
    
    updated_application = update_application(db, application_id, application_update)
    return updated_application


@router.post("/{application_id}/submit")
def submit_application_for_review(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Submit application for review
    Only applicant can submit their own draft applications
    """
    application = get_application(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Only applicant can submit their own applications
    if current_user.id != application.applicant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only submit your own applications"
        )
    
    # Check if grant is still open
    grant = get_grant(db, application.grant_id)
    if not grant or grant.status != GrantStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grant is no longer accepting applications"
        )
    
    now = datetime.utcnow()
    if now > grant.application_close_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application deadline has passed"
        )
    
    submitted_application = submit_application(db, application_id)
    if not submitted_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application cannot be submitted"
        )
    
    return {"message": "Application submitted successfully", "application": submitted_application}


@router.post("/{application_id}/review")
def review_application_by_id(
    application_id: int,
    review_data: ApplicationReview,
    current_user: User = Depends(get_current_client_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Review and update application status
    Requires client organization privileges
    """
    application = get_application(db, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check if user can review this application
    grant = get_grant(db, application.grant_id)
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant not found"
        )
    
    if (current_user.role != UserRole.SUPER_ADMIN and 
        grant.organization_id != current_user.organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot review applications for this grant"
        )
    
    # Can only review submitted applications
    if application.status not in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only review submitted applications"
        )
    
    reviewed_application = review_application(
        db,
        application_id,
        current_user.id,
        review_data.status,
        review_data.reviewer_notes,
        review_data.feedback,
        review_data.score
    )
    
    return {"message": "Application reviewed successfully", "application": reviewed_application}


@router.get("/grant/{grant_id}", response_model=List[ApplicationSummary])
def get_grant_applications_list(
    grant_id: int,
    current_user: User = Depends(get_current_client_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all applications for a specific grant
    Requires client organization privileges
    """
    grant = get_grant(db, grant_id)
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant not found"
        )
    
    # Check permissions
    if (current_user.role != UserRole.SUPER_ADMIN and 
        grant.organization_id != current_user.organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this grant's applications not allowed"
        )
    
    applications = get_grant_applications(db, grant_id)
    return applications


@router.get("/stats/summary")
def get_application_stats(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    grant_id: Optional[int] = Query(None, description="Filter by grant"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get application statistics summary
    Requires admin privileges
    """
    # Super admins can see global stats, client admins see organization stats
    if current_user.role != UserRole.SUPER_ADMIN:
        organization_id = current_user.organization_id
    
    stats = {
        "total_applications": get_applications_count(db, organization_id=organization_id, grant_id=grant_id),
        "submitted_applications": get_applications_count(db, status=ApplicationStatus.SUBMITTED, organization_id=organization_id, grant_id=grant_id),
        "approved_applications": get_applications_count(db, status=ApplicationStatus.APPROVED, organization_id=organization_id, grant_id=grant_id),
        "rejected_applications": get_applications_count(db, status=ApplicationStatus.REJECTED, organization_id=organization_id, grant_id=grant_id),
        "pending_applications": get_applications_count(db, status=ApplicationStatus.UNDER_REVIEW, organization_id=organization_id, grant_id=grant_id),
    }
    
    # Calculate funding statistics
    applications = get_applications(db, skip=0, limit=10000, organization_id=organization_id, grant_id=grant_id)
    total_requested = sum(app.requested_amount for app in applications)
    approved_apps = [app for app in applications if app.status == ApplicationStatus.APPROVED]
    total_approved = sum(app.requested_amount for app in approved_apps)
    
    stats["total_requested"] = total_requested
    stats["total_approved"] = total_approved
    stats["approval_rate"] = (len(approved_apps) / len(applications) * 100) if applications else 0
    
    return stats

