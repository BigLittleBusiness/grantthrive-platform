"""
GrantThrive User CRUD Operations
Enterprise-grade database operations for user management
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models.user import User, UserRole, UserStatus
from ..schemas.user import UserCreate, UserUpdate, UserAdminUpdate
from ..core.security import get_password_hash, verify_password


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_users(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    organization_id: Optional[int] = None,
    search: Optional[str] = None
) -> List[User]:
    """Get users with filtering and pagination"""
    query = db.query(User)
    
    # Apply filters
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)
    if organization_id:
        query = query.filter(User.organization_id == organization_id)
    if search:
        search_filter = or_(
            User.first_name.ilike(f"%{search}%"),
            User.last_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            User.organization_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    return query.offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """Create new user"""
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        bio=user.bio,
        role=user.role,
        organization_name=user.organization_name
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update user information"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def admin_update_user(db: Session, user_id: int, user_update: UserAdminUpdate) -> Optional[User]:
    """Admin update user (includes role, status, etc.)"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def update_user_password(db: Session, user_id: int, new_password: str) -> Optional[User]:
    """Update user password"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(db_user)
    return db_user


def verify_user_email(db: Session, user_id: int) -> Optional[User]:
    """Mark user email as verified"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    db_user.is_verified = True
    db_user.email_verification_token = None
    db.commit()
    db.refresh(db_user)
    return db_user


def deactivate_user(db: Session, user_id: int) -> Optional[User]:
    """Deactivate user account"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    db_user.is_active = False
    db_user.status = UserStatus.INACTIVE
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users_count(
    db: Session,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    organization_id: Optional[int] = None
) -> int:
    """Get total count of users with filters"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)
    if organization_id:
        query = query.filter(User.organization_id == organization_id)
    
    return query.count()


def get_organization_users(db: Session, organization_id: int) -> List[User]:
    """Get all users belonging to an organization"""
    return db.query(User).filter(User.organization_id == organization_id).all()


def update_last_login(db: Session, user_id: int) -> Optional[User]:
    """Update user's last login timestamp"""
    from datetime import datetime
    
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    db_user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user

