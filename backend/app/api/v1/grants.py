"""
GrantThrive Grant Management API
Grant CRUD operations and lifecycle management
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...crud.grant import (
    get_grants,
    get_grant,
    get_grant_by_slug,
    create_grant,
    update_grant,
    delete_grant,
    get_grants_count,
    get_organization_grants
)
from ...schemas.grant import (
    GrantCreate,
    GrantUpdate,
    GrantResponse,
    GrantSummary,
    GrantList,
    GrantStats
)
from ...api.deps import (
    get_current_user,
    get_current_client_user,
    get_current_admin_user,
    require_organization_access,
    get_optional_current_user
)
from ...models.user import User, UserRole
from ...models.grant import GrantStatus, GrantCategory
from decimal import Decimal


router = APIRouter()


@router.get("/", response_model=GrantList)
def list_grants(
    skip: int = Query(0, ge=0, description="Number of grants to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of grants to return"),
    status: Optional[GrantStatus] = Query(None, description="Filter by grant status"),
    category: Optional[GrantCategory] = Query(None, description="Filter by grant category"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    search: Optional[str] = Query(None, description="Search in title, description, organization"),
    is_featured: Optional[bool] = Query(None, description="Filter featured grants"),
    is_open: Optional[bool] = Query(None, description="Filter open for applications"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List grants with filtering and pagination
    Public endpoint - no authentication required
    """
    # For public access, only show published grants
    if not current_user or current_user.role == UserRole.APPLICANT:
        status = GrantStatus.PUBLISHED
    
    # Client users can only see their organization's grants when authenticated
    if current_user and current_user.is_client_user and not organization_id:
        organization_id = current_user.organization_id
    
    grants = get_grants(
        db,
        skip=skip,
        limit=limit,
        status=status,
        category=category,
        organization_id=organization_id,
        search=search,
        is_featured=is_featured,
        is_open=is_open
    )
    
    total = get_grants_count(
        db,
        status=status,
        category=category,
        organization_id=organization_id
    )
    
    return {
        "grants": grants,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/featured", response_model=List[GrantSummary])
def get_featured_grants(
    limit: int = Query(5, ge=1, le=20, description="Number of featured grants to return"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get featured grants for homepage
    Public endpoint
    """
    grants = get_grants(
        db,
        skip=0,
        limit=limit,
        status=GrantStatus.PUBLISHED,
        is_featured=True,
        is_open=True
    )
    return grants


@router.get("/open", response_model=List[GrantSummary])
def get_open_grants(
    limit: int = Query(10, ge=1, le=50, description="Number of open grants to return"),
    category: Optional[GrantCategory] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get currently open grants
    Public endpoint
    """
    grants = get_grants(
        db,
        skip=0,
        limit=limit,
        status=GrantStatus.PUBLISHED,
        category=category,
        is_open=True
    )
    return grants


@router.post("/", response_model=GrantResponse, status_code=status.HTTP_201_CREATED)
def create_new_grant(
    grant_data: GrantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new grant
    Requires authentication - super admins can create for any org, others for their own
    """
    # Super admins can create grants for any organization
    if current_user.role == UserRole.SUPER_ADMIN:
        pass  # No restrictions
    # Client users can only create grants for their organization
    elif current_user.is_client_user:
        if grant_data.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only create grants for your organization"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create grants"
        )
    
    grant = create_grant(db, grant_data, current_user.id)
    return grant


@router.get("/{grant_id}", response_model=GrantResponse)
def get_grant_by_id(
    grant_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get grant by ID
    Public endpoint for published grants
    """
    grant = get_grant(db, grant_id)
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant not found"
        )
    
    # Check access permissions
    if grant.status != GrantStatus.PUBLISHED:
        # Only organization members and admins can view unpublished grants
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grant not found"
            )
        
        if (current_user.role not in [UserRole.SUPER_ADMIN] and
            grant.organization_id != current_user.organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this grant not allowed"
            )
    
    # Increment view count for published grants
    if grant.status == GrantStatus.PUBLISHED:
        grant.view_count += 1
        db.commit()
    
    return grant


@router.get("/slug/{slug}", response_model=GrantResponse)
def get_grant_by_slug_endpoint(
    slug: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get grant by slug
    Public endpoint for published grants
    """
    grant = get_grant_by_slug(db, slug)
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant not found"
        )
    
    # Check access permissions (same logic as get_grant_by_id)
    if grant.status != GrantStatus.PUBLISHED:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grant not found"
            )
        
        if (current_user.role not in [UserRole.SUPER_ADMIN] and
            grant.organization_id != current_user.organization_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this grant not allowed"
            )
    
    # Increment view count for published grants
    if grant.status == GrantStatus.PUBLISHED:
        grant.view_count += 1
        db.commit()
    
    return grant


@router.put("/{grant_id}", response_model=GrantResponse)
def update_grant_by_id(
    grant_id: int,
    grant_update: GrantUpdate,
    current_user: User = Depends(get_current_client_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update grant by ID
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
            detail="Access to this grant not allowed"
        )
    
    updated_grant = update_grant(db, grant_id, grant_update)
    return updated_grant


@router.delete("/{grant_id}")
def delete_grant_by_id(
    grant_id: int,
    current_user: User = Depends(get_current_client_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete grant by ID (soft delete)
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
            detail="Access to this grant not allowed"
        )
    
    # Cannot delete published grants with applications
    if grant.status == GrantStatus.PUBLISHED and grant.application_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete grant with existing applications"
        )
    
    success = delete_grant(db, grant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete grant"
        )
    
    return {"message": "Grant deleted successfully"}


@router.post("/{grant_id}/publish")
def publish_grant(
    grant_id: int,
    current_user: User = Depends(get_current_client_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Publish a draft grant
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
            detail="Access to this grant not allowed"
        )
    
    if grant.status != GrantStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft grants can be published"
        )
    
    # Update status to published
    grant_update = GrantUpdate(status=GrantStatus.PUBLISHED)
    updated_grant = update_grant(db, grant_id, grant_update)
    
    return {"message": "Grant published successfully", "grant": updated_grant}


@router.post("/{grant_id}/close")
def close_grant(
    grant_id: int,
    current_user: User = Depends(get_current_client_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Close a published grant
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
            detail="Access to this grant not allowed"
        )
    
    if grant.status != GrantStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only published grants can be closed"
        )
    
    # Update status to closed
    grant_update = GrantUpdate(status=GrantStatus.CLOSED)
    updated_grant = update_grant(db, grant_id, grant_update)
    
    return {"message": "Grant closed successfully", "grant": updated_grant}


@router.get("/organization/{organization_id}", response_model=List[GrantResponse])
def get_organization_grants_list(
    organization_id: int,
    current_user: User = Depends(require_organization_access),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all grants belonging to an organization
    Requires organization access
    """
    grants = get_organization_grants(db, organization_id)
    return grants


@router.get("/stats/summary")
def get_grant_stats(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get grant statistics summary
    Requires admin privileges
    """
    # Super admins can see global stats, client admins see organization stats
    if current_user.role != UserRole.SUPER_ADMIN:
        organization_id = current_user.organization_id
    
    stats = {
        "total_grants": get_grants_count(db, organization_id=organization_id),
        "published_grants": get_grants_count(db, status=GrantStatus.PUBLISHED, organization_id=organization_id),
        "draft_grants": get_grants_count(db, status=GrantStatus.DRAFT, organization_id=organization_id),
        "closed_grants": get_grants_count(db, status=GrantStatus.CLOSED, organization_id=organization_id),
    }
    
    # Calculate funding statistics
    grants = get_grants(db, skip=0, limit=10000, organization_id=organization_id)
    total_funding = sum(grant.total_funding or 0 for grant in grants)
    stats["total_funding"] = total_funding
    stats["average_funding"] = total_funding / len(grants) if grants else 0
    
    # Category breakdown
    category_counts = {}
    for grant in grants:
        category = grant.category.value
        category_counts[category] = category_counts.get(category, 0) + 1
    stats["by_category"] = category_counts
    
    return stats

