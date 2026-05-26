"""
app/tenancy/logo.py
~~~~~~~~~~~~~~~~~~~~
S3-backed council logo upload endpoint.

Endpoint:
  POST  /api/councils/<id>/logo  — Upload a council logo to S3 and update logo_url

The uploaded logo is stored in S3 under ``logos/council-{id}/{uuid}_{filename}``.
The ``logo_url`` field on the Council record is updated to a permanent public-read
URL (since logos are non-sensitive branding assets that need to be visible in the
React frontend and on the public transparency portal without authentication).

Permission:
  council_admin (own council only) or system_admin
"""

import io
import logging
from datetime import datetime, timezone

from flask import request, jsonify

from app import db
from app.tenancy import councils_bp
from app.auth.routes import token_required
from app.common.s3_service import (
    s3_service,
    ALLOWED_LOGO_EXTENSIONS,
    MAX_LOGO_SIZE_BYTES,
)
from app.models import Council

logger = logging.getLogger(__name__)


@councils_bp.route("/councils/<int:council_id>/logo", methods=["POST"])
@token_required
def upload_council_logo(current_user, council_id):
    """Upload a council logo image to S3 and update the council's logo_url.

    Expects a multipart/form-data POST with a single file field named ``logo``.

    The logo is stored in S3 with public-read access so it can be served
    directly in the React frontend and public portal pages without requiring
    a pre-signed URL.

    Returns:
        200 — updated council dict with new logo_url on success
        400 — validation error
        403 — access denied
        404 — council not found
        503 — S3 not configured
    """
    if not s3_service.is_configured():
        return jsonify({
            "error": (
                "File storage is not configured. "
                "Set the AWS_S3_BUCKET environment variable to enable logo uploads."
            )
        }), 503

    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({"error": "Council not found."}), 404

    is_system_admin = current_user.role == "system_admin"
    is_own_council  = (
        current_user.council_id == council_id
        and current_user.role == "council_admin"
    )
    if not is_system_admin and not is_own_council:
        return jsonify({"error": "Access denied."}), 403

    # ── Validate file presence ──────────────────────────────────────────────
    if "logo" not in request.files:
        return jsonify({
            "error": "No file provided. Include a 'logo' field in the form data."
        }), 400

    file = request.files["logo"]
    if not file.filename:
        return jsonify({"error": "File has no filename."}), 400

    # ── Validate file type ──────────────────────────────────────────────────
    original_filename = file.filename
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    if ext not in ALLOWED_LOGO_EXTENSIONS:
        return jsonify({
            "error": (
                f"File type '.{ext}' is not allowed for logos. "
                f"Permitted types: {', '.join(sorted(ALLOWED_LOGO_EXTENSIONS))}"
            )
        }), 400

    # ── Validate file size ──────────────────────────────────────────────────
    file_bytes = file.read()
    file_size = len(file_bytes)
    if file_size > MAX_LOGO_SIZE_BYTES:
        max_mb = MAX_LOGO_SIZE_BYTES // (1024 * 1024)
        return jsonify({"error": f"Logo file exceeds the maximum size of {max_mb} MB."}), 400
    if file_size == 0:
        return jsonify({"error": "File is empty."}), 400

    # ── Build S3 key ────────────────────────────────────────────────────────
    s3_key = s3_service.make_logo_key(council_id, original_filename)
    content_type = file.content_type or f"image/{ext}"

    # ── Delete old logo from S3 if it was previously uploaded via this endpoint
    # (logo_url values that are external URLs are left untouched)
    if council.logo_url and council.logo_url.startswith(
        f"https://{s3_service.bucket}.s3."
    ):
        # Extract the key from the existing URL and delete the old object
        try:
            old_key = council.logo_url.split(
                f"{s3_service.bucket}.s3.amazonaws.com/"
            )[-1].split(
                f"{s3_service.bucket}.s3.{s3_service._region}.amazonaws.com/"
            )[-1]
            if old_key and old_key != council.logo_url:
                s3_service.delete_object(old_key)
        except Exception:
            pass  # Non-fatal — old logo cleanup is best-effort

    # ── Upload to S3 ────────────────────────────────────────────────────────
    # Logos are uploaded with public-read ACL so they can be served directly
    # in <img> tags without requiring pre-signed URLs.
    try:
        import boto3
        client = s3_service._get_client()
        client.put_object(
            Bucket=s3_service.bucket,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
            ServerSideEncryption="AES256",
            # Logos are public branding assets — no ACL restriction needed
            # (bucket policy controls public access at the bucket level)
        )
        region = s3_service._region or "ap-southeast-2"
        logo_url = (
            f"https://{s3_service.bucket}.s3.{region}.amazonaws.com/{s3_key}"
        )
    except Exception as exc:
        logger.error("S3 logo upload failed for council %d: %s", council_id, exc)
        return jsonify({"error": "Logo upload failed. Please try again."}), 500

    # ── Update the council record ───────────────────────────────────────────
    council.logo_url   = logo_url
    council.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info(
        "Logo uploaded: council_id=%d s3_key=%s by user_id=%d",
        council_id, s3_key, current_user.id,
    )
    return jsonify({"council": council.to_dict()}), 200
