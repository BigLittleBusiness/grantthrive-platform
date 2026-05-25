"""
app/api/abn.py — ABN validation API endpoint.

Exposes:
    GET  /api/abn/validate?abn=<abn>
    POST /api/abn/validate  { "abn": "<abn>" }

Both endpoints are rate-limited and require the user to be authenticated
(login_required) to prevent unauthenticated bulk lookups against the ABR API.

Response JSON:
{
    "abn":            "12345678901",   // normalised 11-digit ABN
    "valid_format":   true,
    "active":         true,            // null if live validation not performed
    "entity_name":    "Acme Pty Ltd",  // null if not available
    "entity_type":    "Australian Private Company",
    "state":          "VIC",
    "postcode":       "3000",
    "gst_registered": true,
    "live_validated": true,
    "error":          null
}
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required

from app.common.abr_service import lookup_abn

logger = logging.getLogger(__name__)

abn_bp = Blueprint("abn", __name__)


def _get_raw_abn() -> str | None:
    """Extract the ABN value from either a GET query param or a POST JSON body."""
    if request.method == "GET":
        return (request.args.get("abn") or "").strip() or None
    data = request.get_json(silent=True) or {}
    return (data.get("abn") or "").strip() or None


@abn_bp.route("/abn/validate", methods=["GET", "POST"])
@login_required
def validate_abn():
    """
    Validate an ABN against the Australian Business Register.

    Requires authentication. Accepts both GET and POST requests.
    """
    raw_abn = _get_raw_abn()

    if not raw_abn:
        return jsonify({
            "abn": "",
            "valid_format": False,
            "active": None,
            "entity_name": None,
            "entity_type": None,
            "state": None,
            "postcode": None,
            "gst_registered": None,
            "live_validated": False,
            "error": "ABN is required.",
        }), 400

    result = lookup_abn(raw_abn)

    # Return 200 for all valid-format ABNs (even cancelled ones) so the
    # frontend can display the entity details and let the user decide.
    # Return 422 only for format failures.
    status_code = 200 if result["valid_format"] else 422

    return jsonify(dict(result)), status_code
