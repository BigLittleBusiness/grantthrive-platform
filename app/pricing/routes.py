"""
Pricing Management API
======================
Endpoints for reading and updating plan pricing configuration.

Public endpoints (no auth required):
  GET  /api/pricing/plans          — returns current pricing for all plans (used by marketing site)

System-admin-only endpoints:
  GET  /api/pricing/admin/plans    — full pricing config including audit metadata
  PUT  /api/pricing/admin/plans/<plan_key>  — update pricing for a specific plan
  POST /api/pricing/admin/plans/reset       — reset all prices to compiled defaults
  GET  /api/pricing/admin/history           — audit log of pricing changes
"""

from flask import jsonify, request, g
from sqlalchemy.exc import SQLAlchemyError

from app.pricing import pricing_bp
from app.models import PricingConfig, db
from app.common.decorators import token_required, role_required
from app.common.plans import PLAN_LIMITS, get_plan_limits


# ── Helpers ───────────────────────────────────────────────────────────────────

EDITABLE_PLANS = ['small', 'medium', 'large']

def _config_to_dict(cfg: PricingConfig) -> dict:
    """Serialise a PricingConfig row to a JSON-safe dict."""
    return {
        'plan_key':                     cfg.plan_key,
        'display_name':                 cfg.display_name,
        'monthly_price_aud_cents':      cfg.monthly_price_aud_cents,
        'annual_price_aud_cents':       cfg.annual_price_aud_cents,
        'annual_monthly_price_aud_cents': cfg.annual_monthly_price_aud_cents,
        'addon_community_voting_cents': cfg.addon_community_voting_cents,
        'addon_grant_mapping_cents':    cfg.addon_grant_mapping_cents,
        'updated_at':                   cfg.updated_at.isoformat() if cfg.updated_at else None,
        'updated_by':                   cfg.updated_by,
    }


def _seed_defaults():
    """Ensure all editable plans have a PricingConfig row (idempotent)."""
    for key in EDITABLE_PLANS:
        if not PricingConfig.query.filter_by(plan_key=key).first():
            limits = PLAN_LIMITS[key]
            row = PricingConfig(
                plan_key                      = key,
                display_name                  = limits.display_name,
                monthly_price_aud_cents       = limits.monthly_price_aud_cents,
                annual_price_aud_cents        = limits.annual_price_aud_cents,
                annual_monthly_price_aud_cents= limits.annual_monthly_price_aud_cents,
                addon_community_voting_cents  = 5000,   # $50/mo default
                addon_grant_mapping_cents     = 5000,   # $50/mo default
            )
            db.session.add(row)
    db.session.commit()


# ── Public endpoint ───────────────────────────────────────────────────────────

@pricing_bp.route('/api/pricing/plans', methods=['GET'])
def get_public_pricing():
    """
    Public — no auth required.
    Returns current pricing for all three plans.
    Used by the marketing website to display live prices.
    """
    try:
        _seed_defaults()
        configs = PricingConfig.query.filter(
            PricingConfig.plan_key.in_(EDITABLE_PLANS)
        ).all()

        # Build a dict keyed by plan_key for easy frontend lookup
        result = {}
        for cfg in configs:
            result[cfg.plan_key] = {
                'display_name':                 cfg.display_name,
                'monthly_price_aud_cents':      cfg.monthly_price_aud_cents,
                'annual_price_aud_cents':       cfg.annual_price_aud_cents,
                'annual_monthly_price_aud_cents': cfg.annual_monthly_price_aud_cents,
                # Add-ons only relevant for small plan
                'addon_community_voting_cents': cfg.addon_community_voting_cents if cfg.plan_key == 'small' else None,
                'addon_grant_mapping_cents':    cfg.addon_grant_mapping_cents if cfg.plan_key == 'small' else None,
            }
        return jsonify({'plans': result}), 200

    except SQLAlchemyError:
        # Fall back to compiled defaults if DB is unavailable
        fallback = {}
        for key in EDITABLE_PLANS:
            lim = PLAN_LIMITS[key]
            fallback[key] = {
                'display_name':                 lim.display_name,
                'monthly_price_aud_cents':      lim.monthly_price_aud_cents,
                'annual_price_aud_cents':       lim.annual_price_aud_cents,
                'annual_monthly_price_aud_cents': lim.annual_monthly_price_aud_cents,
                'addon_community_voting_cents': 5000 if key == 'small' else None,
                'addon_grant_mapping_cents':    5000 if key == 'small' else None,
            }
        return jsonify({'plans': fallback, 'source': 'defaults'}), 200


# ── System-admin endpoints ────────────────────────────────────────────────────

@pricing_bp.route('/api/pricing/admin/plans', methods=['GET'])
@token_required
@role_required('system_admin')
def get_admin_pricing():
    """
    System admin — returns full pricing config with audit metadata.
    """
    _seed_defaults()
    configs = PricingConfig.query.filter(
        PricingConfig.plan_key.in_(EDITABLE_PLANS)
    ).order_by(PricingConfig.plan_key).all()

    return jsonify({
        'plans': [_config_to_dict(c) for c in configs]
    }), 200


@pricing_bp.route('/api/pricing/admin/plans/<plan_key>', methods=['PUT'])
@token_required
@role_required('system_admin')
def update_plan_pricing(plan_key):
    """
    System admin — update pricing for a specific plan.

    Accepted body fields (all optional, all in AUD cents):
      monthly_price_aud_cents
      annual_price_aud_cents
      annual_monthly_price_aud_cents   (display only — per-month equiv of annual)
      addon_community_voting_cents     (small plan only)
      addon_grant_mapping_cents        (small plan only)
      display_name
    """
    if plan_key not in EDITABLE_PLANS:
        return jsonify({'error': f'Plan "{plan_key}" is not editable. Must be one of: {EDITABLE_PLANS}'}), 400

    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    _seed_defaults()
    cfg = PricingConfig.query.filter_by(plan_key=plan_key).first()

    # Validate and apply each accepted field
    updatable = [
        'monthly_price_aud_cents',
        'annual_price_aud_cents',
        'annual_monthly_price_aud_cents',
        'addon_community_voting_cents',
        'addon_grant_mapping_cents',
        'display_name',
    ]

    errors = []
    for field in updatable:
        if field not in data:
            continue
        value = data[field]

        if field == 'display_name':
            if not isinstance(value, str) or not value.strip():
                errors.append(f'"{field}" must be a non-empty string')
                continue
            cfg.display_name = value.strip()
        else:
            # All other fields are integer cent values
            if not isinstance(value, int) or value < 0:
                errors.append(f'"{field}" must be a non-negative integer (AUD cents)')
                continue
            # Add-on fields only apply to small plan
            if field in ('addon_community_voting_cents', 'addon_grant_mapping_cents') and plan_key != 'small':
                errors.append(f'"{field}" is only applicable to the small plan')
                continue
            setattr(cfg, field, value)

    if errors:
        return jsonify({'errors': errors}), 422

    # Audit trail
    from datetime import datetime, timezone
    cfg.updated_at = datetime.now(timezone.utc)
    cfg.updated_by = g.current_user.email if hasattr(g, 'current_user') else 'system_admin'

    # Write to pricing audit log
    from app.models import AuditLog
    try:
        log = AuditLog(
            user_id     = g.current_user.id if hasattr(g, 'current_user') else None,
            action      = 'pricing_updated',
            entity_type = 'pricing_config',
            entity_id   = 0,
            new_values  = str(data),
            ip_address  = request.remote_addr,
        )
        db.session.add(log)
    except Exception:
        pass  # Audit failure must not block the update

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error saving pricing update', 'detail': str(e)}), 500

    return jsonify({
        'message': f'Pricing for "{plan_key}" updated successfully',
        'plan': _config_to_dict(cfg)
    }), 200


@pricing_bp.route('/api/pricing/admin/plans/reset', methods=['POST'])
@token_required
@role_required('system_admin')
def reset_pricing_to_defaults():
    """
    System admin — reset all plan prices to the compiled defaults in plans.py.
    Requires confirmation body: { "confirm": true }
    """
    data = request.get_json(silent=True) or {}
    if not data.get('confirm'):
        return jsonify({'error': 'Send { "confirm": true } to confirm reset'}), 400

    from datetime import datetime, timezone
    for key in EDITABLE_PLANS:
        limits = PLAN_LIMITS[key]
        cfg = PricingConfig.query.filter_by(plan_key=key).first()
        if not cfg:
            cfg = PricingConfig(plan_key=key)
            db.session.add(cfg)
        cfg.display_name                   = limits.display_name
        cfg.monthly_price_aud_cents        = limits.monthly_price_aud_cents
        cfg.annual_price_aud_cents         = limits.annual_price_aud_cents
        cfg.annual_monthly_price_aud_cents = limits.annual_monthly_price_aud_cents
        cfg.addon_community_voting_cents   = 5000
        cfg.addon_grant_mapping_cents      = 5000
        cfg.updated_at                     = datetime.now(timezone.utc)
        cfg.updated_by                     = g.current_user.email if hasattr(g, 'current_user') else 'system_admin'

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error during reset', 'detail': str(e)}), 500

    return jsonify({'message': 'All plan prices reset to defaults'}), 200


@pricing_bp.route('/api/pricing/admin/history', methods=['GET'])
@token_required
@role_required('system_admin')
def get_pricing_history():
    """
    System admin — returns audit log entries for pricing changes.
    """
    from app.models import AuditLog
    try:
        logs = AuditLog.query.filter(
            AuditLog.action == 'pricing_updated'
        ).order_by(AuditLog.created_at.desc()).limit(100).all()

        return jsonify({
            'history': [
                {
                    'id':         l.id,
                    'entity_type': l.entity_type,
                    'changes':    l.new_values,
                    'changed_by': l.user_id,
                    'ip_address': l.ip_address,
                    'timestamp':  l.created_at.isoformat() if l.created_at else None,
                }
                for l in logs
            ]
        }), 200
    except Exception:
        return jsonify({'history': []}), 200
