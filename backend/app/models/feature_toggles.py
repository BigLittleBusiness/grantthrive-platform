"""
GrantThrive Feature Toggle Models
Database models for modular community feature configuration
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, TEXT
from datetime import datetime
from enum import Enum
import json

from ..db.database import Base


# Custom JSON type for SQLite compatibility
class JSONType(TypeDecorator):
    """JSON type that works with SQLite"""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class FeatureRiskLevel(str, Enum):
    """Feature risk levels for council compliance"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FeatureToggle(Base):
    """Organization-specific feature toggle configuration"""
    __tablename__ = "feature_toggles"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Feature Details
    feature_name = Column(String(100), nullable=False, index=True)
    is_enabled = Column(Boolean, default=False, nullable=False)
    configuration = Column(JSONType)  # Feature-specific configuration
    
    # Risk and Compliance
    risk_level = Column(String(20), default="low", nullable=False)
    requires_moderation = Column(Boolean, default=False, nullable=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # organization = relationship("Organization")


class FeatureConfiguration(Base):
    """Global feature configuration and metadata"""
    __tablename__ = "feature_configurations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Feature Details
    feature_name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Risk and Compliance
    risk_level = Column(String(20), default="low", nullable=False)
    requires_moderation = Column(Boolean, default=False, nullable=False)
    default_enabled = Column(Boolean, default=False, nullable=False)
    
    # Configuration Schema
    configuration_schema = Column(JSONType)  # JSON schema for configuration validation
    compliance_notes = Column(Text)  # Notes for council compliance
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

