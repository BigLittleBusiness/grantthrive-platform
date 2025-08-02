"""
GrantThrive Feature Toggles Schemas
Pydantic schemas for feature toggle API endpoints
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FeatureRiskLevelEnum(str, Enum):
    """Feature risk levels for council compliance"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ComplianceTemplateEnum(str, Enum):
    """Council compliance templates"""
    CONSERVATIVE = "conservative"
    STANDARD = "standard"
    PROGRESSIVE = "progressive"
    INNOVATION = "innovation"


# Feature Toggle Schemas
class FeatureToggleBase(BaseModel):
    feature_name: str = Field(..., max_length=100)
    is_enabled: bool = Field(default=False)
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)


class FeatureToggleUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None


class FeatureToggleResponse(FeatureToggleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    organization_id: int
    risk_level: str
    requires_moderation: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


# Feature Configuration Schemas
class FeatureConfigurationBase(BaseModel):
    feature_name: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=500)
    risk_level: FeatureRiskLevelEnum
    requires_moderation: bool = Field(default=False)
    default_enabled: bool = Field(default=False)
    configuration_schema: Optional[Dict[str, Any]] = Field(default_factory=dict)
    compliance_notes: Optional[str] = None


class FeatureConfigurationUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    risk_level: Optional[FeatureRiskLevelEnum] = None
    requires_moderation: Optional[bool] = None
    default_enabled: Optional[bool] = None
    configuration_schema: Optional[Dict[str, Any]] = None
    compliance_notes: Optional[str] = None


class FeatureConfigurationResponse(FeatureConfigurationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# Compliance Template Schemas
class ComplianceTemplateResponse(BaseModel):
    template_name: str
    display_name: str
    description: str
    enabled_features: Dict[str, bool]
    feature_configurations: Dict[str, Dict[str, Any]]
    risk_summary: Dict[str, int]  # count by risk level

