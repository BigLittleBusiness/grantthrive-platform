"""
GrantThrive Feature Toggles CRUD Operations
Database operations for modular community feature management
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from ..models.feature_toggles import FeatureToggle
from ..schemas.feature_toggles import (
    FeatureToggleResponse, FeatureToggleUpdate,
    FeatureConfigurationResponse, FeatureConfigurationUpdate
)


def get_organization_features(db: Session, organization_id: int) -> List[FeatureToggleResponse]:
    """Get organization's feature toggle configuration"""
    features = db.query(FeatureToggle).filter(
        FeatureToggle.organization_id == organization_id
    ).all()
    
    # If no features exist, create default set
    if not features:
        features = _create_default_features(db, organization_id)
    
    return [
        FeatureToggleResponse(
            id=feature.id,
            organization_id=feature.organization_id,
            feature_key=feature.feature_key,
            feature_name=feature.feature_name,
            description=feature.description,
            is_enabled=feature.is_enabled,
            configuration=feature.configuration,
            tier=feature.tier,
            risk_level=feature.risk_level,
            created_at=feature.created_at,
            updated_at=feature.updated_at
        )
        for feature in features
    ]

def update_feature_toggle(
    db: Session,
    organization_id: int,
    feature_key: str,
    toggle_update: FeatureToggleUpdate
) -> FeatureToggleResponse:
    """Update feature toggle status"""
    feature = db.query(FeatureToggle).filter(
        FeatureToggle.organization_id == organization_id,
        FeatureToggle.feature_key == feature_key
    ).first()
    
    if not feature:
        raise ValueError(f"Feature {feature_key} not found")
    
    # Update fields
    for field, value in toggle_update.model_dump(exclude_unset=True).items():
        setattr(feature, field, value)
    
    feature.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(feature)
    
    return FeatureToggleResponse(
        id=feature.id,
        organization_id=feature.organization_id,
        feature_key=feature.feature_key,
        feature_name=feature.feature_name,
        description=feature.description,
        is_enabled=feature.is_enabled,
        configuration=feature.configuration,
        tier=feature.tier,
        risk_level=feature.risk_level,
        created_at=feature.created_at,
        updated_at=feature.updated_at
    )

def get_feature_configuration(
    db: Session,
    organization_id: int,
    feature_key: str
) -> FeatureConfigurationResponse:
    """Get feature-specific configuration"""
    feature = db.query(FeatureToggle).filter(
        FeatureToggle.organization_id == organization_id,
        FeatureToggle.feature_key == feature_key
    ).first()
    
    if not feature:
        raise ValueError(f"Feature {feature_key} not found")
    
    return FeatureConfigurationResponse(
        feature_key=feature.feature_key,
        is_enabled=feature.is_enabled,
        configuration=feature.configuration
    )

def update_feature_configuration(
    db: Session,
    organization_id: int,
    feature_key: str,
    config_update: FeatureConfigurationUpdate
) -> FeatureConfigurationResponse:
    """Update feature-specific configuration"""
    feature = db.query(FeatureToggle).filter(
        FeatureToggle.organization_id == organization_id,
        FeatureToggle.feature_key == feature_key
    ).first()
    
    if not feature:
        raise ValueError(f"Feature {feature_key} not found")
    
    # Update configuration
    if config_update.configuration is not None:
        feature.configuration = config_update.configuration
    
    feature.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(feature)
    
    return FeatureConfigurationResponse(
        feature_key=feature.feature_key,
        is_enabled=feature.is_enabled,
        configuration=feature.configuration
    )

def get_available_features() -> Dict[str, Any]:
    """Get catalog of all available features"""
    return {
        "tier_1": {
            "name": "Core Safe Features",
            "description": "Low-risk features with minimal moderation requirements",
            "features": {
                "resource_library": {
                    "name": "Resource Library",
                    "description": "Document and template sharing",
                    "risk_level": "low",
                    "moderation_required": False
                },
                "grant_statistics": {
                    "name": "Grant Statistics",
                    "description": "Anonymized grant data and analytics",
                    "risk_level": "low",
                    "moderation_required": False
                },
                "grant_calendar": {
                    "name": "Grant Calendar",
                    "description": "Grant deadlines and events calendar",
                    "risk_level": "low",
                    "moderation_required": False
                }
            }
        },
        "tier_2": {
            "name": "Moderated Features",
            "description": "Medium-risk features requiring active moderation",
            "features": {
                "qa_platform": {
                    "name": "Q&A Platform",
                    "description": "Community questions and answers",
                    "risk_level": "medium",
                    "moderation_required": True
                },
                "success_stories": {
                    "name": "Success Stories",
                    "description": "Grant success showcases",
                    "risk_level": "medium",
                    "moderation_required": True
                },
                "networking_events": {
                    "name": "Networking Events",
                    "description": "Community events and webinars",
                    "risk_level": "medium",
                    "moderation_required": True
                }
            }
        },
        "tier_3": {
            "name": "Advanced Features",
            "description": "High-risk features with extensive compliance requirements",
            "features": {
                "forums": {
                    "name": "Discussion Forums",
                    "description": "Open community discussions",
                    "risk_level": "high",
                    "moderation_required": True
                },
                "professional_marketplace": {
                    "name": "Professional Marketplace",
                    "description": "Professional services booking",
                    "risk_level": "high",
                    "moderation_required": True
                },
                "networking": {
                    "name": "User Networking",
                    "description": "Direct user connections",
                    "risk_level": "high",
                    "moderation_required": False
                },
                "gamification": {
                    "name": "Gamification",
                    "description": "Points, badges, and achievements",
                    "risk_level": "medium",
                    "moderation_required": False
                }
            }
        }
    }

def reset_to_template(db: Session, organization_id: int, template_name: str) -> Dict[str, Any]:
    """Apply a configuration template to the organization"""
    templates = {
        "conservative": {
            "resource_library": {"enabled": True, "config": {"allow_uploads": False, "moderation": "pre_approval"}},
            "grant_statistics": {"enabled": True, "config": {"anonymized_only": True}},
            "grant_calendar": {"enabled": True, "config": {"public_events_only": True}},
            "qa_platform": {"enabled": False},
            "success_stories": {"enabled": False},
            "forums": {"enabled": False},
            "professional_marketplace": {"enabled": False},
            "networking": {"enabled": False},
            "gamification": {"enabled": False}
        },
        "standard": {
            "resource_library": {"enabled": True, "config": {"allow_uploads": True, "moderation": "post_approval"}},
            "grant_statistics": {"enabled": True, "config": {"anonymized_only": False}},
            "grant_calendar": {"enabled": True, "config": {"public_events_only": False}},
            "qa_platform": {"enabled": True, "config": {"moderation": "pre_approval"}},
            "success_stories": {"enabled": True, "config": {"council_curated": True}},
            "forums": {"enabled": False},
            "professional_marketplace": {"enabled": False},
            "networking": {"enabled": True, "config": {"events_only": True}},
            "gamification": {"enabled": True, "config": {"basic_points": True}}
        },
        "progressive": {
            "resource_library": {"enabled": True, "config": {"allow_uploads": True, "moderation": "post_approval"}},
            "grant_statistics": {"enabled": True, "config": {"anonymized_only": False}},
            "grant_calendar": {"enabled": True, "config": {"public_events_only": False}},
            "qa_platform": {"enabled": True, "config": {"moderation": "post_approval"}},
            "success_stories": {"enabled": True, "config": {"council_curated": False}},
            "forums": {"enabled": True, "config": {"moderation": "post_approval", "categories_limited": True}},
            "professional_marketplace": {"enabled": True, "config": {"verification_required": True}},
            "networking": {"enabled": True, "config": {"events_only": False}},
            "gamification": {"enabled": True, "config": {"basic_points": True, "achievements": True}}
        },
        "innovation": {
            "resource_library": {"enabled": True, "config": {"allow_uploads": True, "moderation": "post_approval"}},
            "grant_statistics": {"enabled": True, "config": {"anonymized_only": False}},
            "grant_calendar": {"enabled": True, "config": {"public_events_only": False}},
            "qa_platform": {"enabled": True, "config": {"moderation": "community"}},
            "success_stories": {"enabled": True, "config": {"council_curated": False}},
            "forums": {"enabled": True, "config": {"moderation": "community", "categories_limited": False}},
            "professional_marketplace": {"enabled": True, "config": {"verification_required": True}},
            "networking": {"enabled": True, "config": {"events_only": False}},
            "gamification": {"enabled": True, "config": {"basic_points": True, "achievements": True, "leaderboards": True}}
        }
    }
    
    if template_name not in templates:
        raise ValueError(f"Template {template_name} not found")
    
    template = templates[template_name]
    
    # Update all features according to template
    for feature_key, settings in template.items():
        feature = db.query(FeatureToggle).filter(
            FeatureToggle.organization_id == organization_id,
            FeatureToggle.feature_key == feature_key
        ).first()
        
        if feature:
            feature.is_enabled = settings["enabled"]
            feature.configuration = settings.get("config", {})
            feature.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Applied {template_name} template successfully"}

def _create_default_features(db: Session, organization_id: int) -> List[FeatureToggle]:
    """Create default feature toggles for new organization"""
    from datetime import datetime
    
    default_features = [
        {
            "feature_key": "resource_library",
            "feature_name": "Resource Library",
            "description": "Document and template sharing",
            "tier": 1,
            "risk_level": "low",
            "is_enabled": True,
            "configuration": {"allow_uploads": False, "moderation": "pre_approval"}
        },
        {
            "feature_key": "grant_statistics",
            "feature_name": "Grant Statistics",
            "description": "Grant data and analytics",
            "tier": 1,
            "risk_level": "low",
            "is_enabled": True,
            "configuration": {"anonymized_only": True}
        },
        {
            "feature_key": "grant_calendar",
            "feature_name": "Grant Calendar",
            "description": "Grant deadlines and events",
            "tier": 1,
            "risk_level": "low",
            "is_enabled": True,
            "configuration": {"public_events_only": True}
        },
        {
            "feature_key": "qa_platform",
            "feature_name": "Q&A Platform",
            "description": "Community questions and answers",
            "tier": 2,
            "risk_level": "medium",
            "is_enabled": False,
            "configuration": {"moderation": "pre_approval"}
        },
        {
            "feature_key": "success_stories",
            "feature_name": "Success Stories",
            "description": "Grant success showcases",
            "tier": 2,
            "risk_level": "medium",
            "is_enabled": False,
            "configuration": {"council_curated": True}
        },
        {
            "feature_key": "forums",
            "feature_name": "Discussion Forums",
            "description": "Community discussions",
            "tier": 3,
            "risk_level": "high",
            "is_enabled": False,
            "configuration": {"moderation": "pre_approval", "categories_limited": True}
        },
        {
            "feature_key": "professional_marketplace",
            "feature_name": "Professional Marketplace",
            "description": "Professional services",
            "tier": 3,
            "risk_level": "high",
            "is_enabled": False,
            "configuration": {"verification_required": True}
        },
        {
            "feature_key": "networking",
            "feature_name": "User Networking",
            "description": "User connections and networking",
            "tier": 3,
            "risk_level": "high",
            "is_enabled": False,
            "configuration": {"events_only": True}
        },
        {
            "feature_key": "gamification",
            "feature_name": "Gamification",
            "description": "Points, badges, achievements",
            "tier": 3,
            "risk_level": "medium",
            "is_enabled": False,
            "configuration": {"basic_points": True}
        }
    ]
    
    features = []
    for feature_data in default_features:
        feature = FeatureToggle(
            organization_id=organization_id,
            **feature_data
        )
        db.add(feature)
        features.append(feature)
    
    db.commit()
    return features

