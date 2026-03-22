"""
GrantThrive — Plan Limits & Feature Flags
==========================================
Single source of truth for all council subscription tier rules.

Plans map directly to the three tiers shown on grantthrive.com/pricing:

  small       — Small Council   ($200/mo)   5K–20K population
  medium      — Medium Council  ($500/mo)   20K–100K population
  large       — Large Council   ($1,100/mo) 100K+ population

  trial       — 14-day trial (same limits as 'small', no add-ons)
  enterprise  — Legacy alias for 'large' (backward compatibility)

Grant Limits
------------
The pricing page advertises *application* limits, but the backend enforces
*grant creation* limits (a grant is the program; applications are submitted
to it).  The relationship is:
  - Small:  up to 10 active grants at any one time  (≈200 apps/year)
  - Medium: up to 50 active grants at any one time  (≈1,000 apps/year)
  - Large:  unlimited grants

Feature Flags
-------------
  community_voting  — Community Voting System (add-on for Small; included for Medium/Large)
  grant_mapping     — Interactive Grant Mapping (add-on for Small; included for Medium/Large)

Staff User Limits
-----------------
  Small:  3 staff accounts
  Medium: 10 staff accounts
  Large:  unlimited

Add-ons (Small Council only)
-----------------------------
  community_voting_addon  — +$50/mo
  grant_mapping_addon     — +$50/mo

Usage
-----
    from app.common.plans import get_plan_limits, can_use_feature, check_grant_limit

    limits = get_plan_limits(council.plan)
    if not can_use_feature(council, 'community_voting'):
        abort(403, description="Community Voting is not included in your plan.")
    ok, msg = check_grant_limit(council)
    if not ok:
        abort(403, description=msg)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# ── Plan definitions ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PlanLimits:
    """Immutable limits and feature flags for a subscription plan."""
    # Grant creation limits (None = unlimited)
    max_active_grants: Optional[int]
    # Staff user limits (None = unlimited)
    max_staff_users: Optional[int]
    # Included features (always available regardless of add-ons)
    community_voting_included: bool
    grant_mapping_included: bool
    # Add-ons available for purchase (Small only)
    community_voting_addon_available: bool
    grant_mapping_addon_available: bool
    # SMS — included in Medium/Large; purchasable add-on for Small
    sms_included: bool
    sms_addon_available: bool
    # Human-readable display name
    display_name: str
    # Monthly price in AUD cents (for reference / billing)
    monthly_price_aud_cents: int
    # Annual price in AUD cents (10 x monthly = 2 months free)
    annual_price_aud_cents: int
    # Annual per-month equivalent in AUD cents (for display)
    annual_monthly_price_aud_cents: int


PLAN_LIMITS: dict[str, PlanLimits] = {
    "small": PlanLimits(
        display_name                   = "Small Council",
        max_active_grants              = 10,
        max_staff_users                = 3,
        community_voting_included      = False,
        grant_mapping_included         = False,
        community_voting_addon_available = True,
        grant_mapping_addon_available  = True,
        sms_included           = False,
        sms_addon_available    = True,
        monthly_price_aud_cents        = 20000,   # $200.00
        annual_price_aud_cents         = 200000,  # $2,000.00 (10 x $200 = 2 months free)
        annual_monthly_price_aud_cents = 16700,   # ~$167/mo
    ),
    "medium": PlanLimits(
        display_name                   = "Medium Council",
        max_active_grants              = 50,
        max_staff_users                = 10,
        community_voting_included      = True,
        grant_mapping_included         = True,
        community_voting_addon_available = False,
        grant_mapping_addon_available  = False,
        sms_included           = True,
        sms_addon_available    = False,
        monthly_price_aud_cents        = 50000,   # $500.00
        annual_price_aud_cents         = 500000,  # $5,000.00 (10 x $500 = 2 months free)
        annual_monthly_price_aud_cents = 41700,   # ~$417/mo
    ),
    "large": PlanLimits(
        display_name                   = "Large Council",
        max_active_grants              = None,    # unlimited
        max_staff_users                = None,    # unlimited
        community_voting_included      = True,
        grant_mapping_included         = True,
        community_voting_addon_available = False,
        grant_mapping_addon_available  = False,
        sms_included           = True,
        sms_addon_available    = False,
        monthly_price_aud_cents        = 110000,  # $1,100.00
        annual_price_aud_cents         = 1100000, # $11,000.00 (10 x $1,100 = 2 months free)
        annual_monthly_price_aud_cents = 91700,   # ~$917/mo
    ),
    # ── Special plans ─────────────────────────────────────────────────────────
    "trial": PlanLimits(
        display_name                   = "Trial (14 days)",
        max_active_grants              = 10,      # same as small
        max_staff_users                = 3,
        community_voting_included      = False,
        grant_mapping_included         = False,
        community_voting_addon_available = False, # no add-ons during trial
        grant_mapping_addon_available  = False,
        sms_included           = False,
        sms_addon_available    = False,  # SMS not available on trial
        monthly_price_aud_cents        = 0,
        annual_price_aud_cents         = 0,
        annual_monthly_price_aud_cents = 0,
    ),
    "enterprise": PlanLimits(
        # Legacy alias — maps to large
        display_name                   = "Enterprise (Legacy)",
        max_active_grants              = None,
        max_staff_users                = None,
        community_voting_included      = True,
        grant_mapping_included         = True,
        community_voting_addon_available = False,
        grant_mapping_addon_available  = False,
        sms_included           = True,
        sms_addon_available    = False,
        monthly_price_aud_cents        = 110000,
        annual_price_aud_cents         = 1100000,
        annual_monthly_price_aud_cents = 91700,
    ),
    # ── Fallback for unknown plan strings ─────────────────────────────────────
    "starter": PlanLimits(
        # Backward-compat alias for 'small'
        display_name                   = "Starter (Legacy)",
        max_active_grants              = 10,
        max_staff_users                = 3,
        community_voting_included      = False,
        grant_mapping_included         = False,
        community_voting_addon_available = True,
        grant_mapping_addon_available  = True,
        sms_included           = False,
        sms_addon_available    = True,
        monthly_price_aud_cents        = 20000,
        annual_price_aud_cents         = 200000,
        annual_monthly_price_aud_cents = 16700,
    ),
    "professional": PlanLimits(
        # Backward-compat alias for 'medium'
        display_name                   = "Professional (Legacy)",
        max_active_grants              = 50,
        max_staff_users                = 10,
        community_voting_included      = True,
        grant_mapping_included         = True,
        community_voting_addon_available = False,
        grant_mapping_addon_available  = False,
        sms_included           = True,
        sms_addon_available    = False,
        monthly_price_aud_cents        = 50000,
        annual_price_aud_cents         = 500000,
        annual_monthly_price_aud_cents = 41700,
    ),
}

# Default fallback for unknown plan strings
_DEFAULT_PLAN = PLAN_LIMITS["small"]


# ── Public helpers ────────────────────────────────────────────────────────────

def get_plan_limits(plan: str) -> PlanLimits:
    """Return the PlanLimits for the given plan string.

    Falls back to the 'small' limits for unknown plan strings so the
    application never crashes on unexpected data.
    """
    return PLAN_LIMITS.get(plan, _DEFAULT_PLAN)


def get_live_plan_pricing(plan_key: str) -> dict:
    """Return live pricing for a plan from the database, falling back to compiled defaults.

    This is the authoritative source for pricing used at billing/signup time.
    The PricingConfig table is updated by system admins via the admin dashboard.
    If the database is unavailable, compiled defaults from PLAN_LIMITS are used.

    Args:
        plan_key: One of 'small', 'medium', 'large'.

    Returns:
        A dict with keys:
            monthly_price_aud_cents
            annual_price_aud_cents
            annual_monthly_price_aud_cents
            addon_community_voting_cents   (None for medium/large)
            addon_grant_mapping_cents      (None for medium/large)
            display_name
            source: 'database' | 'defaults'
    """
    limits = PLAN_LIMITS.get(plan_key, _DEFAULT_PLAN)
    defaults = {
        "monthly_price_aud_cents":        limits.monthly_price_aud_cents,
        "annual_price_aud_cents":         limits.annual_price_aud_cents,
        "annual_monthly_price_aud_cents": limits.annual_monthly_price_aud_cents,
        "addon_community_voting_cents":   5000 if limits.community_voting_addon_available else None,
        "addon_grant_mapping_cents":      5000 if limits.grant_mapping_addon_available else None,
        "display_name":                   limits.display_name,
        "source":                         "defaults",
    }
    try:
        from app.models import PricingConfig
        row = PricingConfig.query.filter_by(plan_key=plan_key).first()
        if row:
            return {
                "monthly_price_aud_cents":        row.monthly_price_aud_cents,
                "annual_price_aud_cents":         row.annual_price_aud_cents,
                "annual_monthly_price_aud_cents": row.annual_monthly_price_aud_cents,
                "addon_community_voting_cents":   row.addon_community_voting_cents if limits.community_voting_addon_available else None,
                "addon_grant_mapping_cents":      row.addon_grant_mapping_cents if limits.grant_mapping_addon_available else None,
                "display_name":                   row.display_name,
                "source":                         "database",
            }
    except Exception:
        pass  # DB unavailable — fall through to defaults
    return defaults


def can_use_feature(council, feature: str) -> bool:
    """Return True if the council can use the named feature.

    Checks both the plan's included features and any purchased add-ons
    stored on the council record.

    Args:
        council: A Council model instance.
        feature: One of 'community_voting' or 'grant_mapping'.

    Returns:
        True if the feature is available to this council.
    """
    limits = get_plan_limits(council.plan)

    if feature == "community_voting":
        if limits.community_voting_included:
            return True
        # Check if the add-on has been purchased
        return bool(getattr(council, "addon_community_voting", False))

    if feature == "grant_mapping":
        if limits.grant_mapping_included:
            return True
        return bool(getattr(council, "addon_grant_mapping", False))

    if feature == "sms":
        if limits.sms_included:
            return True
        # Check if the SMS add-on has been enabled by GrantThrive
        return bool(getattr(council, "addon_sms", False))

    # Unknown feature — deny by default
    return False


def check_grant_limit(council) -> tuple[bool, str]:
    """Check whether the council can create another active grant.

    Counts all non-archived, non-closed grants for the council and
    compares against the plan's max_active_grants limit.

    Args:
        council: A Council model instance (must have a .grants relationship).

    Returns:
        (True, "") if the council is within its limit.
        (False, human_readable_message) if the limit has been reached.
    """
    limits = get_plan_limits(council.plan)

    if limits.max_active_grants is None:
        # Unlimited plan
        return True, ""

    from app.models import Grant  # local import to avoid circular dependency
    active_count = Grant.query.filter(
        Grant.council_id == council.id,
        Grant.status.notin_(["archived", "closed"]),
    ).count()

    if active_count >= limits.max_active_grants:
        return False, (
            f"Your {limits.display_name} plan allows up to "
            f"{limits.max_active_grants} active grants. "
            f"You currently have {active_count}. "
            "Please close or archive an existing grant, or upgrade your plan."
        )
    return True, ""


def check_staff_limit(council) -> tuple[bool, str]:
    """Check whether the council can add another staff user.

    Args:
        council: A Council model instance.

    Returns:
        (True, "") if within limit.
        (False, human_readable_message) if limit reached.
    """
    limits = get_plan_limits(council.plan)

    if limits.max_staff_users is None:
        return True, ""

    from app.models import User  # local import
    staff_count = User.query.filter(
        User.council_id == council.id,
        User.role.in_(["council_admin", "council_staff"]),
        User.is_active == True,
    ).count()

    if staff_count >= limits.max_staff_users:
        return False, (
            f"Your {limits.display_name} plan allows up to "
            f"{limits.max_staff_users} staff accounts. "
            f"You currently have {staff_count}. "
            "Please deactivate an existing account or upgrade your plan."
        )
    return True, ""


def plan_entitlements(plan: str) -> dict:
    """Return a JSON-serialisable dict of entitlements for the given plan.

    Used in API responses so the frontend can show/hide features without
    hard-coding plan logic.  Pricing fields are sourced from the live
    database via get_live_plan_pricing() so they reflect admin edits.
    """
    limits = get_plan_limits(plan)
    pricing = get_live_plan_pricing(plan)
    return {
        "plan":                          plan,
        "display_name":                  pricing.get("display_name", limits.display_name),
        "max_active_grants":             limits.max_active_grants,
        "max_staff_users":               limits.max_staff_users,
        "community_voting_included":     limits.community_voting_included,
        "grant_mapping_included":        limits.grant_mapping_included,
        "community_voting_addon_available": limits.community_voting_addon_available,
        "grant_mapping_addon_available": limits.grant_mapping_addon_available,
        "sms_included":                  limits.sms_included,
        "sms_addon_available":           limits.sms_addon_available,
        # Live pricing fields
        "monthly_price_aud_cents":        pricing["monthly_price_aud_cents"],
        "annual_price_aud_cents":         pricing["annual_price_aud_cents"],
        "annual_monthly_price_aud_cents": pricing["annual_monthly_price_aud_cents"],
        "addon_community_voting_cents":   pricing.get("addon_community_voting_cents"),
        "addon_grant_mapping_cents":      pricing.get("addon_grant_mapping_cents"),
    }
