#!/usr/bin/env python3
"""
GrantThrive — Stripe account setup (idempotent)
================================================
Prepares a Stripe account (test or live) for GrantThrive subscriptions:

  1. Finds the six GrantThrive plan prices by product name
     ("GrantThrive Small - Monthly" … "GrantThrive Large - Yearly").
  2. Gives each price its lookup key (grantthrive_<plan>_<cycle>) — the app
     resolves prices by lookup key, never by hard-coded ID.
  3. Marks each price tax-exclusive so Stripe Tax adds 10% GST on top for
     Australian customers (AUD prices otherwise default to GST-inclusive).
  4. Sets the products' tax code to "Software as a service — business use".
  5. Creates (or updates) a GrantThrive-specific Customer Portal configuration
     and prints its ID for STRIPE_PORTAL_CONFIGURATION_ID.

Run from the backend directory:
    STRIPE_SECRET_KEY=sk_... python scripts/stripe_setup.py

Prerequisite (dashboard): Stripe Tax active with an Australian registration.
"""
import os
import sys

import stripe

PLANS = ("small", "medium", "large")
CYCLES = {"monthly": "Monthly", "annual": "Yearly"}   # app cycle -> product name suffix
SAAS_BUSINESS_TAX_CODE = "txcd_10103001"
PORTAL_METADATA = {"app": "grantthrive"}


def lookup_key(plan: str, cycle: str) -> str:
    return f"grantthrive_{plan}_{cycle}"


def find_price(plan: str, cycle: str):
    key = lookup_key(plan, cycle)
    existing = stripe.Price.list(lookup_keys=[key], active=True, expand=["data.product"]).data
    if existing:
        return existing[0]
    name = f"GrantThrive {plan.capitalize()} - {CYCLES[cycle]}"
    for price in stripe.Price.list(active=True, limit=100, expand=["data.product"]).auto_paging_iter():
        if price.product.name == name and price.recurring:
            return price
    sys.exit(f"No active recurring price found for product '{name}'. Create it in Stripe first.")


def main():
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or sys.exit("Set STRIPE_SECRET_KEY.")

    settings = stripe.tax.Settings.retrieve()
    if settings.status != "active":
        sys.exit("Stripe Tax is not active on this account — activate it and add an AU registration first.")

    portal_products = []
    for plan in PLANS:
        for cycle in CYCLES:
            price = find_price(plan, cycle)
            updates = {}
            if price.lookup_key != lookup_key(plan, cycle):
                updates.update(lookup_key=lookup_key(plan, cycle), transfer_lookup_key=True)
            if price.tax_behavior == "unspecified":
                updates["tax_behavior"] = "exclusive"
            elif price.tax_behavior != "exclusive":
                sys.exit(f"{price.id} is tax-{price.tax_behavior}; Stripe cannot change it. Create a new exclusive price.")
            if updates:
                stripe.Price.modify(price.id, **updates)
            if price.product.tax_code != SAAS_BUSINESS_TAX_CODE:
                stripe.Product.modify(price.product.id, tax_code=SAAS_BUSINESS_TAX_CODE)
            portal_products.append({"product": price.product.id, "prices": [price.id]})
            print(f"  {lookup_key(plan, cycle):28} {price.id}  {price.unit_amount / 100:>9.2f} {price.currency.upper()} + GST (AU)")

    features = {
        "customer_update": {"enabled": True, "allowed_updates": ["email", "address", "tax_id"]},
        "invoice_history": {"enabled": True},
        "payment_method_update": {"enabled": True},
        "subscription_cancel": {"enabled": True, "mode": "at_period_end"},
        "subscription_update": {
            "enabled": True,
            "default_allowed_updates": ["price"],
            "proration_behavior": "create_prorations",
            "products": portal_products,
        },
    }
    business_profile = {"headline": "Manage your GrantThrive subscription"}

    existing = next(
        (c for c in stripe.billing_portal.Configuration.list(limit=100).auto_paging_iter()
         if c.metadata and c.metadata.to_dict().get("app") == PORTAL_METADATA["app"]),
        None,
    )
    if existing:
        config = stripe.billing_portal.Configuration.modify(
            existing.id, features=features, business_profile=business_profile, active=True)
    else:
        config = stripe.billing_portal.Configuration.create(
            features=features, business_profile=business_profile, metadata=PORTAL_METADATA)

    print(f"\nSTRIPE_PORTAL_CONFIGURATION_ID={config.id}")


if __name__ == "__main__":
    main()
