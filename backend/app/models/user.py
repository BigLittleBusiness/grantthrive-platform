"""
GrantThrive User Models
Enterprise-grade user management with role-based access control
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from ..db.database import Base


class UserRole(PyEnum):
    """User role enumeration"""
    SUPER_ADMIN = "super_admin"      # GrantThrive platform admin
    CLIENT_ADMIN = "client_admin"    # Council/organization admin
    CLIENT_USER = "client_user"      # Council/organization staff
    APPLICANT = "applicant"          # Grant applicants
    PROFESSIONAL = "professional"    # Service providers


class UserStatus(PyEnum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class User(Base):
    """
    Core user model supporting multi-tenant architecture
    """
    __tablename__ = "users"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Profile information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Role and permissions
    role = Column(Enum(UserRole), nullable=False, default=UserRole.APPLICANT)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.PENDING)
    
    # Organization association (for multi-tenant support)
    organization_id = Column(Integer, nullable=True, index=True)
    organization_name = Column(String(255), nullable=True)
    
    # Profile details
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Verification and security
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges"""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.CLIENT_ADMIN]
    
    @property
    def is_client_user(self) -> bool:
        """Check if user belongs to a client organization"""
        return self.role in [UserRole.CLIENT_ADMIN, UserRole.CLIENT_USER]
    
    def can_manage_grants(self) -> bool:
        """Check if user can manage grants"""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.CLIENT_ADMIN, UserRole.CLIENT_USER]
    
    def can_apply_for_grants(self) -> bool:
        """Check if user can apply for grants"""
        return self.role == UserRole.APPLICANT
    
    def can_provide_services(self) -> bool:
        """Check if user can provide professional services"""
        return self.role == UserRole.PROFESSIONAL

