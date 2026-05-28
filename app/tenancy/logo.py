"""
app/tenancy/logo.py
~~~~~~~~~~~~~~~~~~~
Council logo upload endpoint.

Endpoint:
  POST  /api/councils/<id>/logo  — Upload a council logo to S3

The logo is stored in S3 with public-read ACL so it can be served directly
in <img> tags without requiring pre-signed URLs (branding asset, not sensitive).

Permission:
  council_admin (own council only) or system_admin
"""

import io
import logging
from datetime import datetime, timezone

from flask import request, jsonify

from app import db
from app.auth.routes import token_required
from app.common.s3_service import s3_service, ALLOWED_LOGO_EXTENSIONS, MAX_LOGO_SIZE_BYTES
from app.models import Council

logger = logging.getLogger(__name__)


def upload_council_logo(bp):
    """
    Register the logo upload route on the given blueprint.
    Called from tenancy/__init__.py or routes.py
    """

    @bp.route("/councils/<int:council_id>/logo", methods=["POST"])
    @token_required
    def upload_logo(current_user, council_id):
        """
        Upload a council logo image to S3 and update the council's logo_url.

        Expects a multipart/form-data POST with a single file field named 'logo'.

        The logo is stored in S3 with public-read access so it can be served
        directly in the React frontend without requiring a pre-signed URL.

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

        # ── Verify council exists ────────────────────────────────────────
        council = db.session.get(Council, council_id)
        if not council:
            return jsonify({"error": "Council not found."}), 404

        # ── Check authorization ────────────────────────────────────────────
        is_own_council = current_user.council_id == council_id
        is_system_admin = current_user.role == 'system_admin'
        if not (is_own_council or is_system_admin):
            return jsonify({"error": "Access denied."}), 403

        # ── Check file present ─────────────────────────────────────────────
        if "logo" not in request.files:
            return jsonify({"error": "No file provided."}), 400

        file = request.files["logo"]
        if file.filename == "":
            return jsonify({"error": "File name is empty."}), 400

        # ── Validate file type ─────────────────────────────────────────────
        if "." not in file.filename:
            return jsonify({"error": "File must have an extension."}), 400

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_LOGO_EXTENSIONS:
            return jsonify({
                "error": f"File type not allowed. Allowed: {', '.join(sorted(ALLOWED_LOGO_EXTENSIONS))}"
            }), 400

        # ── Validate file size ─────────────────────────────────────────────
        file_bytes = file.read()
        if len(file_bytes) == 0:
            return jsonify({"error": "File is empty."}), 400

        if len(file_bytes) > MAX_LOGO_SIZE_BYTES:
            return jsonify({
                "error": f"File exceeds maximum size of {MAX_LOGO_SIZE_BYTES / 1024 / 1024:.0f} MB"
            }), 400

        # ── Generate S3 key and upload ─────────────────────────────────────
        try:
            original_filename = file.filename
            s3_key = s3_service.make_logo_key(council_id, original_filename)
            content_type = file.content_type or "image/jpeg"

            s3_service.upload_fileobj(
                io.BytesIO(file_bytes),
                s3_key,
                content_type=content_type,
                extra_metadata={
                    "council_id": str(council_id),
                    "uploaded_by": str(current_user.id),
                }
            )
        except RuntimeError as exc:
            logger.error("S3 logo upload failed for council %d: %s", council_id, exc)
            return jsonify({"error": "Logo upload failed. Please try again."}), 500

        # ── Generate public URL ────────────────────────────────────────────
        region = s3_service.region or "ap-southeast-2"
        logo_url = f"https://{s3_service.bucket}.s3.{region}.amazonaws.com/{s3_key}"

        # ── Update the council record ──────────────────────────────────────
        council.logo_url = logo_url
        council.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(
            "Logo uploaded: council_id=%d s3_key=%s user_id=%d",
            council_id, s3_key, current_user.id,
        )

        return jsonify({
            "council": council.to_dict() if hasattr(council, 'to_dict') else {
                "id": council.id,
                "name": council.name,
                "logo_url": council.logo_url,
            }
        }), 200
