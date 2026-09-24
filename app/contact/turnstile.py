"""Cloudflare Turnstile server-side validation for public forms."""

from __future__ import annotations

import logging
from typing import Any

import requests
from flask import current_app

logger = logging.getLogger(__name__)

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
MAX_TOKEN_LENGTH = 2048


class TurnstileVerificationError(RuntimeError):
    """A controlled verification failure safe to return to a visitor."""


def _expected_hostnames() -> set[str]:
    configured = current_app.config.get("TURNSTILE_EXPECTED_HOSTNAMES", "")
    return {item.strip().lower() for item in configured.split(",") if item.strip()}


def verify_turnstile_token(token: Any, remote_ip: str | None, expected_action: str) -> None:
    """Validate a one-time Turnstile token and raise a controlled error on failure.

    The form is rejected closed when Turnstile is not configured or Siteverify is
    unavailable. A test-only configuration switch is available for isolated unit
    tests; it is not enabled by any deployed configuration.
    """
    if current_app.config.get("TURNSTILE_TEST_BYPASS", False):
        return

    secret = current_app.config.get("TURNSTILE_SECRET_KEY", "").strip()
    if not secret:
        logger.error("Turnstile secret is not configured for protected public forms")
        raise TurnstileVerificationError("Verification is temporarily unavailable. Please try again later.")

    if not isinstance(token, str) or not token.strip() or len(token) > MAX_TOKEN_LENGTH:
        raise TurnstileVerificationError("Please complete the verification check and try again.")

    payload = {"secret": secret, "response": token.strip()}
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        response = requests.post(SITEVERIFY_URL, data=payload, timeout=5)
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Turnstile Siteverify request failed: %s", exc.__class__.__name__)
        raise TurnstileVerificationError("Verification is temporarily unavailable. Please try again later.") from exc

    if not result.get("success"):
        error_codes = result.get("error-codes") or []
        logger.info("Turnstile rejected a public form submission: %s", ",".join(map(str, error_codes)))
        raise TurnstileVerificationError("Verification expired or could not be confirmed. Please try again.")

    if result.get("action") != expected_action:
        logger.warning("Turnstile action mismatch: expected=%s received=%s", expected_action, result.get("action"))
        raise TurnstileVerificationError("Verification could not be confirmed. Please try again.")

    expected_hostnames = _expected_hostnames()
    returned_hostname = str(result.get("hostname") or "").lower()
    if expected_hostnames and returned_hostname not in expected_hostnames:
        logger.warning("Turnstile hostname mismatch: received=%s", returned_hostname)
        raise TurnstileVerificationError("Verification could not be confirmed. Please try again.")
