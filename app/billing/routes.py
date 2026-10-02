"""
GrantThrive — Billing API (mounted at /api/billing)
====================================================
  GET  /plans              — Plan prices from Stripe (public; amounts exclude GST)
  POST /checkout-session   — Start a Stripe Checkout subscription  { plan, billing_cycle }
  POST /checkout-session/sync — Apply a completed checkout on return  { session_id }
  POST /portal-session     — Open the Stripe Customer Portal
  POST /webhook            — Stripe webhook (signature verified)

Checkout and portal are for the council's own council_admin.
"""
import logging

import stripe
from flask import request, jsonify

from app import db
from app.billing import bp
from app.billing import stripe_service as billing
from app.common.decorators import role_required
from app.common.plans import validate_plan_selection
from app.models import Council

logger = logging.getLogger(__name__)


def _own_council(user):
    council = db.session.get(Council, user.council_id) if user.council_id else None
    if council is None:
        return None, (jsonify({"error": "Your account is not linked to a council."}), 400)
    return council, None


def _billing_error(exc):
    if isinstance(exc, billing.BillingNotConfigured):
        logger.error("Billing unavailable: %s", exc)
        return jsonify({"error": "Billing is not available right now. Please contact GrantThrive support."}), 503
    logger.exception("Stripe request failed: %s", exc)
    return jsonify({"error": "The payment provider could not process the request. Please try again."}), 502


@bp.route("/plans", methods=["GET"])
def plans():
    try:
        return jsonify({"plans": billing.plan_catalogue(), "tax_note": "Prices exclude GST. 10% GST is added for Australian customers."})
    except (billing.BillingNotConfigured, stripe.StripeError) as exc:
        return _billing_error(exc)


@bp.route("/checkout-session", methods=["POST"])
@role_required("council_admin")
def checkout_session(current_user):
    council, error = _own_council(current_user)
    if error:
        return error
    data = request.get_json(silent=True) or {}
    plan, cycle = data.get("plan"), data.get("billing_cycle")
    invalid = validate_plan_selection(plan, cycle)
    if invalid:
        return jsonify({"error": invalid}), 400
    if billing.has_live_subscription(council):
        return jsonify({"error": "Your council already has an active subscription. Use Manage billing to change it."}), 409
    try:
        return jsonify({"url": billing.create_checkout_session(council, current_user.email, plan, cycle)}), 201
    except (billing.BillingNotConfigured, stripe.StripeError) as exc:
        return _billing_error(exc)


@bp.route("/checkout-session/sync", methods=["POST"])
@role_required("council_admin")
def sync_checkout(current_user):
    council, error = _own_council(current_user)
    if error:
        return error
    session_id = (request.get_json(silent=True) or {}).get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required."}), 400
    try:
        council = billing.sync_checkout_session(session_id, council)
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403
    except (billing.BillingNotConfigured, stripe.StripeError) as exc:
        return _billing_error(exc)
    return jsonify({"subscription": billing.subscription_summary(council), "plan": council.plan})


@bp.route("/portal-session", methods=["POST"])
@role_required("council_admin")
def portal_session(current_user):
    council, error = _own_council(current_user)
    if error:
        return error
    if not council.stripe_customer_id:
        return jsonify({"error": "Your council has no billing account yet. Subscribe to a plan first."}), 409
    try:
        return jsonify({"url": billing.create_portal_session(council)}), 201
    except (billing.BillingNotConfigured, stripe.StripeError) as exc:
        return _billing_error(exc)


@bp.route("/webhook", methods=["POST"])
def webhook():
    try:
        event = billing.construct_event(request.get_data(), request.headers.get("Stripe-Signature", ""))
    except billing.BillingNotConfigured as exc:
        return _billing_error(exc)
    except (ValueError, stripe.SignatureVerificationError):
        return jsonify({"error": "Invalid webhook signature."}), 400
    try:
        billing.handle_event(event)
    except stripe.StripeError as exc:
        # Let Stripe retry the delivery later.
        return _billing_error(exc)
    return jsonify({"received": True})
