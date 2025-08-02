"""
GrantThrive Feature Toggle API Endpoints
Handles modular community feature configuration for council compliance
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud.feature_toggles import (
    get_organization_features, update_feature_toggle,
    get_feature_configuration, update_feature_configuration,
    get_available_features, reset_to_template
)
from app.models.user import User
from app.schemas.feature_toggles import (
    FeatureToggleResponse, FeatureToggleUpdate,
    FeatureConfigurationResponse, FeatureConfigurationUpdate
)

router = APIRouter()

# Feature Toggle Management
@router.get("/", response_model=List[FeatureToggleResponse])
def get_organization_feature_toggles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organization's feature toggle configuration"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return get_organization_features(db=db, organization_id=current_user.organization_id)

@router.put("/{feature_key}", response_model=FeatureToggleResponse)
def update_feature_toggle_status(
    feature_key: str,
    toggle_update: FeatureToggleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update feature toggle status"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return update_feature_toggle(
        db=db, organization_id=current_user.organization_id,
        feature_key=feature_key, toggle_update=toggle_update
    )

# Feature Configuration
@router.get("/{feature_key}/config", response_model=FeatureConfigurationResponse)
def get_feature_config(
    feature_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get feature-specific configuration"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return get_feature_configuration(
        db=db, organization_id=current_user.organization_id, feature_key=feature_key
    )

@router.put("/{feature_key}/config", response_model=FeatureConfigurationResponse)
def update_feature_config(
    feature_key: str,
    config_update: FeatureConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update feature-specific configuration"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return update_feature_configuration(
        db=db, organization_id=current_user.organization_id,
        feature_key=feature_key, config_update=config_update
    )

# Available Features Catalog
@router.get("/catalog/available")
def get_available_features_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get catalog of all available features"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return get_available_features()

# Configuration Templates
@router.get("/templates")
def get_configuration_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get predefined configuration templates for different council types"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return {
        "conservative": {
            "name": "Conservative Council",
            "description": "Minimal risk features with read-only content",
            "features": {
                "resource_library": {"enabled": True, "config": {"allow_uploads": False, "moderation": "pre_approval"}},
                "grant_statistics": {"enabled": True, "config": {"anonymized_only": True}},
                "grant_calendar": {"enabled": True, "config": {"public_events_only": True}},
                "forums": {"enabled": False},
                "professional_marketplace": {"enabled": False},
                "networking": {"enabled": False},
                "gamification": {"enabled": False}
            }
        },
        "standard": {
            "name": "Standard Council",
            "description": "Moderate engagement with controlled community features",
            "features": {
                "resource_library": {"enabled": True, "config": {"allow_uploads": True, "moderation": "post_approval"}},
                "grant_statistics": {"enabled": True, "config": {"anonymized_only": False}},
                "grant_calendar": {"enabled": True, "config": {"public_events_only": False}},
                "qa_platform": {"enabled": True, "config": {"moderation": "pre_approval"}},
                "success_stories": {"enabled": True, "config": {"council_curated": True}},
                "forums": {"enabled": False},
                "professional_marketplace": {"enabled": False},
                "networking": {"enabled": True, "config": {"events_only": True}},
                "gamification": {"enabled": True, "config": {"basic_points": True}}
            }
        },
        "progressive": {
            "name": "Progressive Council",
            "description": "Higher engagement with most community features enabled",
            "features": {
                "resource_library": {"enabled": True, "config": {"allow_uploads": True, "moderation": "post_approval"}},
                "grant_statistics": {"enabled": True, "config": {"anonymized_only": False}},
                "grant_calendar": {"enabled": True, "config": {"public_events_only": False}},
                "qa_platform": {"enabled": True, "config": {"moderation": "post_approval"}},
                "success_stories": {"enabled": True, "config": {"council_curated": False}},
                "forums": {"enabled": True, "config": {"moderation": "post_approval", "categories_limited": True}},
                "professional_marketplace": {"enabled": True, "config": {"verification_required": True}},
                "networking": {"enabled": True, "config": {"events_only": False}},
                "gamification": {"enabled": True, "config": {"basic_points": True, "achievements": True}}
            }
        },
        "innovation": {
            "name": "Innovation Council",
            "description": "All features enabled with maximum community engagement",
            "features": {
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
    }

@router.post("/apply-template/{template_name}")
def apply_configuration_template(
    template_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply a configuration template to the organization"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return reset_to_template(
        db=db, organization_id=current_user.organization_id, template_name=template_name
    )

# Public Feature Check (for frontend)
@router.get("/check/{feature_key}")
def check_feature_enabled(
    feature_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if a specific feature is enabled for the organization"""
    features = get_organization_features(db=db, organization_id=current_user.organization_id)
    
    for feature in features:
        if feature.feature_key == feature_key:
            return {
                "enabled": feature.is_enabled,
                "configuration": feature.configuration
            }
    
    return {"enabled": False, "configuration": {}}

# Bulk Feature Management
@router.put("/bulk-update")
def bulk_update_features(
    feature_updates: Dict[str, FeatureToggleUpdate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk update multiple feature toggles"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    results = {}
    for feature_key, toggle_update in feature_updates.items():
        try:
            result = update_feature_toggle(
                db=db, organization_id=current_user.organization_id,
                feature_key=feature_key, toggle_update=toggle_update
            )
            results[feature_key] = {"success": True, "feature": result}
        except Exception as e:
            results[feature_key] = {"success": False, "error": str(e)}
    
    return results

