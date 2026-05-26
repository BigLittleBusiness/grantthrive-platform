"""
app/applications/documents.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
S3-backed document upload and download endpoints for grant applications.

Endpoints:
  POST   /api/applications/<id>/documents          — Upload a document to S3
  GET    /api/applications/<id>/documents           — List documents for an application
  GET    /api/applications/<id>/documents/<doc_id>  — Get a pre-signed S3 download URL
  DELETE /api/applications/<id>/documents/<doc_id>  — Delete a document from S3 + DB

Permission matrix:
  Upload / delete  — application owner (community_member / professional_consultant)
                     OR council_staff, council_admin, system_admin
  List / download  — same as above
"""

import logging
from datetime import datetime, timezone

from flask import request, jsonify

from app import db
from app.applications import bp
from app.common.permissions import permission_required
from app.common.s3_service import (
    s3_service,
    ALLOWED_DOCUMENT_EXTENSIONS,
    MAX_DOCUMENT_SIZE_BYTES,
)
from app.models import Application, ApplicationDocument

logger = logging.getLogger(__name__)

# Maximum number of documents per application
MAX_DOCUMENTS_PER_APPLICATION = 20


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _can_access(user, application: Application) -> bool:
    """Return True if the user may read/write documents on this application."""
    if user.role == "system_admin":
        return True
    if user.role in ("council_admin", "council_staff"):
        return application.grant.council_id == user.council_id
    # community_member / professional_consultant — own applications only
    return application.applicant_id == user.id


def _doc_to_dict(doc: ApplicationDocument) -> dict:
    return {
        "id":                doc.id,
        "application_id":    doc.application_id,
        "original_filename": doc.original_filename,
        "file_size":         doc.file_size,
        "mime_type":         doc.mime_type,
        "uploaded_at":       doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        # s3_key is intentionally omitted from API responses for security
    }


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@bp.route("/<int:app_id>/documents", methods=["POST"])
@permission_required("applications:read_own")
def upload_document(current_user, app_id):
    """Upload a supporting document for a grant application to S3.

    Expects a multipart/form-data POST with a single file field named ``file``.

    Returns:
        201 — document metadata dict on success
        400 — validation error (missing file, wrong type, too large, too many)
        403 — access denied
        404 — application not found
        503 — S3 not configured (development environment)
    """
    if not s3_service.is_configured():
        return jsonify({
            "error": (
                "File storage is not configured. "
                "Set the AWS_S3_BUCKET environment variable to enable document uploads."
            )
        }), 503

    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404

    if not _can_access(current_user, application):
        return jsonify({"error": "Access denied."}), 403

    # ── Validate file presence ──────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Include a 'file' field in the form data."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "File has no filename."}), 400

    # ── Validate file type ──────────────────────────────────────────────────
    original_filename = file.filename
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        return jsonify({
            "error": (
                f"File type '.{ext}' is not allowed. "
                f"Permitted types: {', '.join(sorted(ALLOWED_DOCUMENT_EXTENSIONS))}"
            )
        }), 400

    # ── Validate file size ──────────────────────────────────────────────────
    # Read the stream into memory to check size, then reset for upload
    file_bytes = file.read()
    file_size = len(file_bytes)
    if file_size > MAX_DOCUMENT_SIZE_BYTES:
        max_mb = MAX_DOCUMENT_SIZE_BYTES // (1024 * 1024)
        return jsonify({"error": f"File exceeds the maximum size of {max_mb} MB."}), 400
    if file_size == 0:
        return jsonify({"error": "File is empty."}), 400

    # ── Check document count limit ──────────────────────────────────────────
    existing_count = ApplicationDocument.query.filter_by(
        application_id=app_id
    ).count()
    if existing_count >= MAX_DOCUMENTS_PER_APPLICATION:
        return jsonify({
            "error": f"Maximum of {MAX_DOCUMENTS_PER_APPLICATION} documents per application."
        }), 400

    # ── Determine S3 key and MIME type ──────────────────────────────────────
    council_id = application.grant.council_id
    s3_key = s3_service.make_document_key(council_id, app_id, original_filename)
    content_type = file.content_type or "application/octet-stream"

    # ── Upload to S3 ────────────────────────────────────────────────────────
    import io
    try:
        s3_service.upload_fileobj(
            io.BytesIO(file_bytes),
            s3_key,
            content_type=content_type,
            extra_metadata={
                "application_id": str(app_id),
                "uploaded_by":    str(current_user.id),
                "council_id":     str(council_id),
            },
        )
    except RuntimeError as exc:
        logger.error("S3 upload error for application %d: %s", app_id, exc)
        return jsonify({"error": "File upload failed. Please try again."}), 500

    # ── Persist metadata to database ────────────────────────────────────────
    # Extract the sanitised filename portion from the key for display
    stored_filename = s3_key.split("/")[-1]

    doc = ApplicationDocument(
        application_id=app_id,
        filename=stored_filename,
        original_filename=original_filename,
        s3_key=s3_key,
        file_size=file_size,
        mime_type=content_type,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.session.add(doc)
    db.session.commit()

    logger.info(
        "Document uploaded: application_id=%d doc_id=%d s3_key=%s by user_id=%d",
        app_id, doc.id, s3_key, current_user.id,
    )
    return jsonify({"document": _doc_to_dict(doc)}), 201


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@bp.route("/<int:app_id>/documents", methods=["GET"])
@permission_required("applications:read_own")
def list_documents(current_user, app_id):
    """Return a list of document metadata records for an application."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404

    if not _can_access(current_user, application):
        return jsonify({"error": "Access denied."}), 403

    docs = ApplicationDocument.query.filter_by(application_id=app_id).all()
    return jsonify({"documents": [_doc_to_dict(d) for d in docs]}), 200


# ---------------------------------------------------------------------------
# Download (pre-signed URL)
# ---------------------------------------------------------------------------

@bp.route("/<int:app_id>/documents/<int:doc_id>", methods=["GET"])
@permission_required("applications:read_own")
def get_document_url(current_user, app_id, doc_id):
    """Return a time-limited pre-signed S3 URL to download a document.

    The URL expires after 1 hour.  The client should redirect to it or
    open it in a new tab immediately — do not cache the URL.
    """
    if not s3_service.is_configured():
        return jsonify({"error": "File storage is not configured."}), 503

    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404

    if not _can_access(current_user, application):
        return jsonify({"error": "Access denied."}), 403

    doc = db.session.get(ApplicationDocument, doc_id)
    if not doc or doc.application_id != app_id:
        return jsonify({"error": "Document not found."}), 404

    if not doc.s3_key:
        return jsonify({"error": "Document has no associated S3 key."}), 404

    try:
        url = s3_service.generate_presigned_url(
            doc.s3_key,
            expiry_seconds=3600,
            filename_hint=doc.original_filename,
        )
    except RuntimeError as exc:
        logger.error("Pre-signed URL generation failed for doc %d: %s", doc_id, exc)
        return jsonify({"error": "Could not generate download URL. Please try again."}), 500

    return jsonify({
        "document": _doc_to_dict(doc),
        "download_url": url,
        "expires_in_seconds": 3600,
    }), 200


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@bp.route("/<int:app_id>/documents/<int:doc_id>", methods=["DELETE"])
@permission_required("applications:read_own")
def delete_document(current_user, app_id, doc_id):
    """Delete a document from S3 and remove its database record."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404

    if not _can_access(current_user, application):
        return jsonify({"error": "Access denied."}), 403

    doc = db.session.get(ApplicationDocument, doc_id)
    if not doc or doc.application_id != app_id:
        return jsonify({"error": "Document not found."}), 404

    # Delete from S3 first (non-fatal if it fails — DB record is still removed)
    if doc.s3_key and s3_service.is_configured():
        s3_service.delete_object(doc.s3_key)

    db.session.delete(doc)
    db.session.commit()

    logger.info(
        "Document deleted: application_id=%d doc_id=%d by user_id=%d",
        app_id, doc_id, current_user.id,
    )
    return jsonify({"message": "Document deleted successfully."}), 200
