"""
GrantThrive User Schemas
Pydantic models for API request/response serialization
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from ..models.user import UserRole, UserStatus


# Base schemas
class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    organization_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str
    role: UserRole = UserRole.APPLICANT
    username: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """Schema for user updates"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    organization_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    username: Optional[str]
    role: UserRole
    status: UserStatus
    is_active: bool
    is_verified: bool
    organization_id: Optional[int]
    avatar_url: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    """Extended user profile schema"""
    full_name: str
    is_admin: bool
    is_client_user: bool
    
    class Config:
        from_attributes = True


# Authentication schemas
class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Schema for token data"""
    email: Optional[str] = None
    user_id: Optional[int] = None


class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class ChangePassword(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# Admin schemas
class UserAdminUpdate(BaseModel):
    """Schema for admin user updates"""
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    organization_id: Optional[int] = None


class UserList(BaseModel):
    """Schema for paginated user list"""
    users: list[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int

