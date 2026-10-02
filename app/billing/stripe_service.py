"""
GrantThrive — Stripe billing service
=====================================
All Stripe API access lives here. Plans are sold as monthly or annual
subscriptions whose prices are found by lookup key
(grantthrive_<plan>_<cycle>, created by scripts/stripe_setup.py).

GST: Checkout runs with Stripe Tax (automatic_tax) and the prices are
tax-exclusive, so customers with an Australian billing address are charged
10% GST on top of the plan price; overseas customers are not.

Subscription state is always re-read from Stripe before it is written to the
council, so webhook retries / out-of-order events cannot leave stale data.
"""
import logging
import time
from datetime import datetime, timezone

import stripe
from flask import current_app

from app import db
from app.common.plans import PAID_PLANS, BILLING_CYCLES, get_plan_limits
from app.models import Council

logger = logging.getLogger(__name__)

# Subscription statuses that grant the subscribed plan's entitlements.
# past_due keeps access while Stripe retries the payment.
ENTITLED_STATUSES = frozenset({"active", "trialing", "past_due"})

_PRICE_CACHE_SECONDS = 300
_price_cache = {"expires": 0.0, "prices": {}}


class BillingNotConfigured(RuntimeError):
    """Raised when STRIPE_SECRET_KEY is not set."""


def lookup_key(plan: str, cycle: str) -> str:
    return f"grantthrive_{plan}_{cycle}"


def _client():
    api_key = current_app.config.get("STRIPE_SECRET_KEY")
    if not api_key:
        raise BillingNotConfigured("Stripe billing is not configured.")
    stripe.api_key = api_key
    return stripe


def get_prices() -> dict:
    """Return {(plan, cycle): stripe.Price} for every GrantThrive plan (cached briefly)."""
    if _price_cache["expires"] > time.monotonic():
        return _price_cache["prices"]
    keys = [lookup_key(p, c) for p in PAID_PLANS for c in BILLING_CYCLES]
    prices = _client().Price.list(lookup_keys=keys, active=True, limit=len(keys)).data
    by_key = {price.lookup_key: price for price in prices}
    missing = [k for k in keys if k not in by_key]
    if missing:
        raise BillingNotConfigured(f"Stripe prices missing for: {', '.join(missing)}. Run scripts/stripe_setup.py.")
    _price_cache.update(
        expires=time.monotonic() + _PRICE_CACHE_SECONDS,
        prices={(p, c): by_key[lookup_key(p, c)] for p in PAID_PLANS for c in BILLING_CYCLES},
    )
    return _price_cache["prices"]


def plan_catalogue() -> list:
    """Plan prices (from Stripe; amounts exclude GST) with each plan's limits."""
    catalogue = []
    for (plan, cycle), price in get_prices().items():
        limits = get_plan_limits(plan)
        catalogue.append({
            "plan": plan,
            "name": limits.display_name,
            "billing_cycle": cycle,
            "amount_cents": price.unit_amount,
            "currency": price.currency,
            "interval": price.recurring.interval,
            "max_active_grants": limits.max_active_grants,
            "max_staff_users": limits.max_staff_users,
            "community_voting_included": limits.community_voting_included,
            "grant_mapping_included": limits.grant_mapping_included,
        })
    return catalogue


def _plan_for_lookup_key(key: str | None):
    for plan in PAID_PLANS:
        for cycle in BILLING_CYCLES:
            if key == lookup_key(plan, cycle):
                return plan, cycle
    return None, None


def _ensure_customer(council: Council, email: str) -> str:
    if council.stripe_customer_id:
        return council.stripe_customer_id
    customer = _client().Customer.create(
        email=email,
        name=council.name,
        metadata={"council_id": str(council.id)},
    )
    council.stripe_customer_id = customer.id
    db.session.commit()
    return customer.id


def has_live_subscription(council: Council) -> bool:
    return council.subscription_status in ENTITLED_STATUSES


def create_checkout_session(council: Council, email: str, plan: str, cycle: str) -> str:
    """Create a subscription Checkout Session and return its URL."""
    price = get_prices()[(plan, cycle)]
    app_url = current_app.config["FRONTEND_BASE_URL"]
    metadata = {"council_id": str(council.id), "plan": plan, "billing_cycle": cycle}
    session = _client().checkout.Session.create(
        mode="subscription",
        customer=_ensure_customer(council, email),
        client_reference_id=str(council.id),
        line_items=[{"price": price.id, "quantity": 1}],
        automatic_tax={"enabled": True},
        # Always charge in AUD; never convert to the visitor's local currency.
        adaptive_pricing={"enabled": False},
        billing_address_collection="required",
        customer_update={"address": "auto", "name": "auto"},
        tax_id_collection={"enabled": True},
        subscription_data={"metadata": metadata},
        metadata=metadata,
        success_url=f"{app_url}/portal/council/account-billing?checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{app_url}/portal/council/account-billing?checkout=cancelled",
    )
    return session.url


def create_portal_session(council: Council) -> str:
    """Create a Customer Portal session (payment method, invoices, plan change, cancel)."""
    params = {
        "customer": council.stripe_customer_id,
        "return_url": f"{current_app.config['FRONTEND_BASE_URL']}/portal/council/account-billing",
    }
    configuration = current_app.config.get("STRIPE_PORTAL_CONFIGURATION_ID")
    if configuration:
        params["configuration"] = configuration
    return _client().billing_portal.Session.create(**params).url


def _timestamp(value):
    return datetime.fromtimestamp(value, tz=timezone.utc).replace(tzinfo=None) if value else None


def sync_subscription(subscription_id: str) -> Council | None:
    """Re-read a subscription from Stripe and apply it to its council."""
    subscription = _client().Subscription.retrieve(subscription_id, expand=["items.data.price"])
    council = None
    council_id = subscription.metadata.to_dict().get("council_id") if subscription.metadata else None
    if council_id:
        council = db.session.get(Council, int(council_id))
    if council is None:
        council = Council.query.filter_by(stripe_customer_id=subscription.customer).first()
    if council is None:
        logger.warning("Stripe subscription %s has no matching council", subscription.id)
        return None

    item = subscription["items"].data[0]
    plan, cycle = _plan_for_lookup_key(item.price.lookup_key)
    if plan is None:
        logger.warning("Subscription %s uses a non-GrantThrive price %s", subscription.id, item.price.id)
        return council

    # A newer subscription for the same council wins; ignore stale ones.
    if council.stripe_subscription_id and council.stripe_subscription_id != subscription.id \
            and subscription.status not in ENTITLED_STATUSES:
        return council

    council.stripe_customer_id = subscription.customer
    council.stripe_subscription_id = subscription.id
    council.subscription_status = subscription.status
    council.billing_plan = plan
    council.billing_cycle = cycle
    council.cancel_at_period_end = bool(subscription.cancel_at_period_end)
    period_end = getattr(item, "current_period_end", None) or getattr(subscription, "current_period_end", None)
    council.current_period_end = _timestamp(period_end)

    if subscription.status in ENTITLED_STATUSES:
        council.plan = plan
        council.trial_ends_at = None
    elif subscription.status in ("canceled", "unpaid", "incomplete_expired"):
        council.plan = "trial"
    db.session.commit()
    logger.info("Council %s subscription %s: %s (%s/%s)", council.id, subscription.id, subscription.status, plan, cycle)
    return council


def sync_checkout_session(session_id: str, council: Council) -> Council:
    """Apply the subscription from a completed Checkout Session (on return from Stripe)."""
    session = _client().checkout.Session.retrieve(session_id)
    if session.client_reference_id != str(council.id):
        raise PermissionError("Checkout session does not belong to this council.")
    if session.subscription:
        return sync_subscription(session.subscription) or council
    return council


def construct_event(payload: bytes, signature: str):
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise BillingNotConfigured("STRIPE_WEBHOOK_SECRET is not set.")
    _client()
    return stripe.Webhook.construct_event(payload, signature, secret)


SUBSCRIPTION_EVENTS = frozenset({
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "customer.subscription.paused",
    "customer.subscription.resumed",
})


def handle_event(event) -> None:
    """Apply a verified webhook event."""
    obj = event.data.object
    if event.type == "checkout.session.completed" and obj.mode == "subscription" and obj.subscription:
        sync_subscription(obj.subscription)
    elif event.type in SUBSCRIPTION_EVENTS:
        sync_subscription(obj.id)
    elif event.type in ("invoice.paid", "invoice.payment_failed"):
        subscription_id = getattr(obj, "subscription", None) or _invoice_subscription(obj)
        if subscription_id:
            sync_subscription(subscription_id)


def _invoice_subscription(invoice):
    """Newer API versions nest the subscription under invoice.parent."""
    parent = getattr(invoice, "parent", None)
    details = getattr(parent, "subscription_details", None) if parent else None
    return getattr(details, "subscription", None) if details else None


def subscription_summary(council: Council) -> dict:
    return {
        "plan": council.billing_plan,
        "billing_cycle": council.billing_cycle,
        "status": council.subscription_status,
        "is_active": has_live_subscription(council),
        "current_period_end": council.current_period_end.isoformat() if council.current_period_end else None,
        "cancel_at_period_end": bool(council.cancel_at_period_end),
        "has_billing_account": bool(council.stripe_customer_id),
    }
