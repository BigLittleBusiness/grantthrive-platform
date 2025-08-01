"""
GrantThrive User Management API
User CRUD operations and profile management
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...crud.user import (
    get_users,
    get_user,
    update_user,
    admin_update_user,
    deactivate_user,
    get_users_count,
    get_organization_users
)
from ...schemas.user import (
    UserResponse,
    UserUpdate,
    UserAdminUpdate,
    UserList,
    UserProfile
)
from ...api.deps import (
    get_current_user,
    get_current_admin_user,
    get_current_super_admin,
    require_organization_access
)
from ...models.user import User, UserRole, UserStatus


router = APIRouter()


@router.get("/me", response_model=UserProfile)
def get_my_profile(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user's profile
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user's profile
    """
    updated_user = update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.get("/", response_model=UserList)
def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    status: Optional[UserStatus] = Query(None, description="Filter by user status"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    search: Optional[str] = Query(None, description="Search in name, email, organization"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List users with filtering and pagination
    Requires admin privileges
    """
    # Super admins can see all users
    # Client admins can only see users from their organization
    if current_user.role != UserRole.SUPER_ADMIN:
        organization_id = current_user.organization_id
    
    users = get_users(
        db,
        skip=skip,
        limit=limit,
        role=role,
        status=status,
        organization_id=organization_id,
        search=search
    )
    
    total = get_users_count(
        db,
        role=role,
        status=status,
        organization_id=organization_id
    )
    
    return {
        "users": users,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user by ID
    Requires admin privileges
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Client admins can only view users from their organization
    if (current_user.role != UserRole.SUPER_ADMIN and 
        user.organization_id != current_user.organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this user not allowed"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
def admin_update_user_by_id(
    user_id: int,
    user_update: UserAdminUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Admin update user by ID
    Requires admin privileges
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Client admins can only update users from their organization
    if (current_user.role != UserRole.SUPER_ADMIN and 
        user.organization_id != current_user.organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this user not allowed"
        )
    
    # Only super admins can change roles to super_admin
    if (user_update.role == UserRole.SUPER_ADMIN and 
        current_user.role != UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign super admin role"
        )
    
    updated_user = admin_update_user(db, user_id, user_update)
    return updated_user


@router.delete("/{user_id}")
def deactivate_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Deactivate user by ID
    Requires admin privileges
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Client admins can only deactivate users from their organization
    if (current_user.role != UserRole.SUPER_ADMIN and 
        user.organization_id != current_user.organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this user not allowed"
        )
    
    # Cannot deactivate super admins
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate super admin"
        )
    
    # Cannot deactivate yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    deactivated_user = deactivate_user(db, user_id)
    return {"message": "User deactivated successfully"}


@router.get("/organization/{organization_id}", response_model=List[UserResponse])
def get_organization_users_list(
    organization_id: int,
    current_user: User = Depends(require_organization_access),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all users belonging to an organization
    Requires organization access
    """
    users = get_organization_users(db, organization_id)
    return users


@router.get("/stats/summary")
def get_user_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get user statistics summary
    Requires admin privileges
    """
    # Super admins see global stats, client admins see organization stats
    organization_id = None if current_user.role == UserRole.SUPER_ADMIN else current_user.organization_id
    
    stats = {
        "total_users": get_users_count(db, organization_id=organization_id),
        "active_users": get_users_count(db, status=UserStatus.ACTIVE, organization_id=organization_id),
        "pending_users": get_users_count(db, status=UserStatus.PENDING, organization_id=organization_id),
        "applicants": get_users_count(db, role=UserRole.APPLICANT, organization_id=organization_id),
        "professionals": get_users_count(db, role=UserRole.PROFESSIONAL, organization_id=organization_id),
        "client_users": get_users_count(db, role=UserRole.CLIENT_USER, organization_id=organization_id),
        "client_admins": get_users_count(db, role=UserRole.CLIENT_ADMIN, organization_id=organization_id)
    }
    
    if current_user.role == UserRole.SUPER_ADMIN:
        stats["super_admins"] = get_users_count(db, role=UserRole.SUPER_ADMIN)
    
    return stats

