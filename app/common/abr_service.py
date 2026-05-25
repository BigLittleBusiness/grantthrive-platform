"""
abr_service.py — Australian Business Register (ABR) API integration.

This module provides ABN validation and business name lookup via the ABR's
free public API (ABN Lookup Web Services).

To activate:
    1. Register for a free GUID at https://abr.business.gov.au/Tools/WebServices
    2. Set the environment variable:  ABR_GUID=<your-guid>
    3. Restart the application.

When ABR_GUID is not set, the module operates in OFFLINE mode:
    - Format validation (11-digit checksum) is still performed.
    - No live ABR lookup is made.
    - All responses include a flag indicating whether live validation occurred.

ABR API reference: https://abr.business.gov.au/json/
"""

import os
import re
import logging
import requests
from functools import lru_cache
from typing import TypedDict

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

ABR_GUID: str | None = os.environ.get("ABR_GUID")
ABR_BASE_URL = "https://abr.business.gov.au/json/"
ABR_TIMEOUT_SECONDS = 5

# ── Public result type ────────────────────────────────────────────────────────


class ABNResult(TypedDict):
    """Structured result returned by all public functions in this module."""
    abn: str                    # Normalised 11-digit ABN (digits only)
    valid_format: bool          # Passed the 11-digit checksum algorithm
    active: bool | None         # True = active, False = cancelled, None = unknown
    entity_name: str | None     # Legal/trading name from ABR
    entity_type: str | None     # e.g. "Australian Private Company"
    state: str | None           # Registered state/territory
    postcode: str | None        # Registered postcode
    gst_registered: bool | None # True if registered for GST
    live_validated: bool        # True if an actual ABR API call was made
    error: str | None           # Human-readable error message, if any


# ── ABN format validation (checksum) ─────────────────────────────────────────

_WEIGHTS = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]


def _normalise_abn(raw: str) -> str:
    """Strip all non-digit characters and return the bare 11-digit string."""
    return re.sub(r"\D", "", raw or "")


def validate_abn_format(raw_abn: str) -> bool:
    """
    Validate an ABN using the official 11-digit weighted checksum algorithm.

    Reference: https://abr.business.gov.au/Help/AbnFormat
    Returns True if the ABN passes the checksum, False otherwise.
    """
    digits = _normalise_abn(raw_abn)
    if len(digits) != 11:
        return False
    # Step 1: subtract 1 from the first (left-most) digit
    d = [int(c) for c in digits]
    d[0] -= 1
    # Step 2: multiply each digit by its weighting factor
    total = sum(w * v for w, v in zip(_WEIGHTS, d))
    # Step 3: sum must be divisible by 89
    return total % 89 == 0


# ── ABR live lookup ───────────────────────────────────────────────────────────

def _parse_abr_response(data: dict, abn: str) -> ABNResult:
    """
    Parse the JSON response from the ABR ABN Lookup endpoint into an ABNResult.

    The ABR returns a nested structure under the key "ABRPayloadSearchResults"
    → "response" → "businessEntity202001".
    """
    try:
        payload = data["ABRPayloadSearchResults"]["response"]
    except (KeyError, TypeError):
        return ABNResult(
            abn=abn, valid_format=True, active=None, entity_name=None,
            entity_type=None, state=None, postcode=None, gst_registered=None,
            live_validated=True,
            error="Unexpected ABR response structure.",
        )

    # The ABR may return an exception block instead of a business entity
    exception = payload.get("exception")
    if exception:
        exc_desc = exception.get("exceptionDescription", "ABR lookup failed.")
        return ABNResult(
            abn=abn, valid_format=True, active=None, entity_name=None,
            entity_type=None, state=None, postcode=None, gst_registered=None,
            live_validated=True, error=exc_desc,
        )

    entity = payload.get("businessEntity202001", {})

    # ── Status ────────────────────────────────────────────────────────────────
    abn_status = entity.get("ABN", {})
    if isinstance(abn_status, list):
        abn_status = abn_status[0] if abn_status else {}
    is_active = abn_status.get("identifierStatus", "").lower() == "active"

    # ── Entity name ───────────────────────────────────────────────────────────
    entity_name: str | None = None
    main_name = entity.get("mainName")
    if main_name:
        entity_name = main_name.get("organisationName") or main_name.get("fullName")
    if not entity_name:
        legal_name = entity.get("legalName")
        if legal_name:
            given = legal_name.get("givenName", "")
            family = legal_name.get("familyName", "")
            entity_name = f"{given} {family}".strip() or None

    # ── Entity type ───────────────────────────────────────────────────────────
    entity_type_data = entity.get("entityType", {})
    entity_type = entity_type_data.get("entityDescription") if entity_type_data else None

    # ── Address ───────────────────────────────────────────────────────────────
    address = entity.get("mainBusinessPhysicalAddress", {})
    if isinstance(address, list):
        address = address[0] if address else {}
    state = address.get("stateCode")
    postcode = address.get("postcode")

    # ── GST ───────────────────────────────────────────────────────────────────
    gst_data = entity.get("goodsAndServicesTax")
    gst_registered: bool | None = None
    if gst_data:
        gst_status = gst_data.get("identifierStatus", "").lower()
        gst_registered = gst_status == "active"

    return ABNResult(
        abn=abn,
        valid_format=True,
        active=is_active,
        entity_name=entity_name,
        entity_type=entity_type,
        state=state,
        postcode=postcode,
        gst_registered=gst_registered,
        live_validated=True,
        error=None,
    )


def lookup_abn(raw_abn: str) -> ABNResult:
    """
    Validate and look up an ABN.

    Behaviour:
    - Always runs the local 11-digit checksum first.
    - If ABR_GUID is configured, performs a live ABR API call.
    - If ABR_GUID is not configured, returns format-only result with
      live_validated=False so callers can decide how to handle it.

    Args:
        raw_abn: The ABN string as entered by the user (spaces/hyphens allowed).

    Returns:
        ABNResult TypedDict.
    """
    abn = _normalise_abn(raw_abn)

    # ── Step 1: Format check ──────────────────────────────────────────────────
    if not validate_abn_format(abn):
        return ABNResult(
            abn=abn,
            valid_format=False,
            active=None,
            entity_name=None,
            entity_type=None,
            state=None,
            postcode=None,
            gst_registered=None,
            live_validated=False,
            error="Invalid ABN format. An ABN must be 11 digits and pass the checksum.",
        )

    # ── Step 2: Live ABR lookup (only if GUID is configured) ─────────────────
    if not ABR_GUID:
        logger.debug(
            "ABR_GUID not configured — ABN %s passed format check only.", abn
        )
        return ABNResult(
            abn=abn,
            valid_format=True,
            active=None,
            entity_name=None,
            entity_type=None,
            state=None,
            postcode=None,
            gst_registered=None,
            live_validated=False,
            error=None,
        )

    url = f"{ABR_BASE_URL}AbnDetails.aspx"
    params = {
        "abn": abn,
        "guid": ABR_GUID,
    }

    try:
        response = requests.get(url, params=params, timeout=ABR_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        logger.warning("ABR API timeout for ABN %s", abn)
        return ABNResult(
            abn=abn, valid_format=True, active=None, entity_name=None,
            entity_type=None, state=None, postcode=None, gst_registered=None,
            live_validated=False,
            error="ABR lookup timed out. The ABN format is valid but could not be verified live.",
        )
    except requests.exceptions.RequestException as exc:
        logger.warning("ABR API request failed for ABN %s: %s", abn, exc)
        return ABNResult(
            abn=abn, valid_format=True, active=None, entity_name=None,
            entity_type=None, state=None, postcode=None, gst_registered=None,
            live_validated=False,
            error="ABR lookup failed. The ABN format is valid but could not be verified live.",
        )
    except ValueError:
        logger.warning("ABR API returned non-JSON response for ABN %s", abn)
        return ABNResult(
            abn=abn, valid_format=True, active=None, entity_name=None,
            entity_type=None, state=None, postcode=None, gst_registered=None,
            live_validated=False,
            error="ABR returned an unexpected response.",
        )

    return _parse_abr_response(data, abn)
