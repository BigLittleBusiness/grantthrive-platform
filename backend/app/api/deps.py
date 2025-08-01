"""
GrantThrive API Dependencies
Authentication and authorization dependencies for FastAPI
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..core.security import verify_token
from ..crud.user import get_user, update_last_login
from ..models.user import User, UserRole


# Security scheme for JWT tokens
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token and extract payload
        payload = verify_token(credentials.credentials, "access")
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # Get user from database
    user = get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    # Update last login timestamp
    update_last_login(db, user.id)
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for clarity)
    """
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user with admin privileges
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_current_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current super admin user
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user


def get_current_client_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current client organization user
    """
    if not current_user.is_client_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client organization access required"
        )
    return current_user


def get_current_applicant(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current applicant user
    """
    if current_user.role != UserRole.APPLICANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Applicant access required"
        )
    return current_user


def get_current_professional(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current professional service provider
    """
    if current_user.role != UserRole.PROFESSIONAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professional service provider access required"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    Useful for endpoints that work for both authenticated and anonymous users
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials, "access")
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        user = get_user(db, user_id=user_id)
        if user is None or not user.is_active:
            return None
        
        update_last_login(db, user.id)
        return user
    except Exception:
        return None


def check_organization_access(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> bool:
    """
    Check if current user has access to specific organization
    """
    # Super admins have access to all organizations
    if current_user.role == UserRole.SUPER_ADMIN:
        return True
    
    # Client users can only access their own organization
    if current_user.is_client_user:
        return current_user.organization_id == organization_id
    
    # Other roles don't have organization access
    return False


def require_organization_access(
    organization_id: int,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require organization access or raise 403
    """
    if not check_organization_access(organization_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this organization not allowed"
        )
    return current_user

