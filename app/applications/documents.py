"""
app/applications/documents.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
File upload endpoint for grant application supporting documents.

Endpoint:
  POST  /api/applications/<id>/documents  — Upload a document to S3

The document is stored in S3 with encryption and metadata tracking.
Access is controlled via permission checks (only applicants can upload for their own applications).

Allowed file types: PDF, Word, Excel, PowerPoint, images, CSV
Maximum file size: 16 MB
"""

import io
import logging
from datetime import datetime, timezone

from flask import request, jsonify

from app import db
from app.applications import bp
from app.auth.routes import token_required
from app.common.permissions import permission_required
from app.common.s3_service import s3_service, is_allowed_file, MAX_DOCUMENT_SIZE_BYTES
from app.models import Application, ApplicationDocument

logger = logging.getLogger(__name__)


@bp.route("/<int:app_id>/documents", methods=["POST"])
@token_required
@permission_required("applications:read_own")
def upload_document(current_user, app_id):
    """
    Upload a supporting document for a grant application to S3.
    
    Expects multipart/form-data with file field named 'file'.
    
    Returns:
        201 — document metadata on success
        400 — validation error (missing file, wrong type, too large)
        403 — access denied
        404 — application not found
        503 — S3 not configured
    """
    if not s3_service.is_configured():
        return jsonify({
            "error": "File storage is not configured. Set AWS_S3_BUCKET environment variable."
        }), 503

    # ── Verify application exists ──────────────────────────────────────────
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404

    # ── Check file present ─────────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "File name is empty."}), 400

    # ── Validate file type ─────────────────────────────────────────────────
    if not is_allowed_file(file.filename):
        return jsonify({
            "error": f"File type not allowed. Allowed: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, GIF, CSV, ZIP"
        }), 400

    # ── Validate file size ─────────────────────────────────────────────────
    file_bytes = file.read()
    if len(file_bytes) == 0:
        return jsonify({"error": "File is empty."}), 400

    if len(file_bytes) > MAX_DOCUMENT_SIZE_BYTES:
        return jsonify({
            "error": f"File exceeds maximum size of {MAX_DOCUMENT_SIZE_BYTES / 1024 / 1024:.0f} MB"
        }), 400

    # ── Generate S3 key and upload ─────────────────────────────────────────
    try:
        original_filename = file.filename
        council_id = application.grant.council_id
        s3_key = s3_service.make_document_key(council_id, original_filename)
        content_type = file.content_type or "application/octet-stream"

        s3_service.upload_fileobj(
            io.BytesIO(file_bytes),
            s3_key,
            content_type=content_type,
            extra_metadata={
                "application_id": str(app_id),
                "council_id": str(council_id),
                "uploaded_by": str(current_user.id),
            }
        )
    except RuntimeError as exc:
        logger.error("S3 upload error for application %d: %s", app_id, exc)
        return jsonify({"error": "File upload failed. Please try again."}), 500

    # ── Create database record ─────────────────────────────────────────────
    try:
        doc = ApplicationDocument(
            application_id=app_id,
            filename=file.filename,
            s3_key=s3_key,
            file_size=len(file_bytes),
            content_type=content_type,
            uploaded_at=datetime.now(timezone.utc),
            uploaded_by_id=current_user.id,
        )
        db.session.add(doc)
        db.session.commit()

        logger.info(
            "Document uploaded: app_id=%d doc_id=%d s3_key=%s user_id=%d",
            app_id, doc.id, s3_key, current_user.id,
        )

        return jsonify({
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "s3_key": doc.s3_key,
                "file_size": doc.file_size,
                "content_type": doc.content_type,
                "uploaded_at": doc.uploaded_at.isoformat(),
            }
        }), 201

    except Exception as exc:
        logger.error("Failed to save document metadata: %s", exc)
        # Attempt to delete the uploaded file if DB save fails
        try:
            s3_service.delete_object(s3_key)
        except Exception:
            pass
        return jsonify({"error": "Failed to save document metadata."}), 500


@bp.route("/<int:app_id>/documents/<int:doc_id>/download", methods=["GET"])
@token_required
@permission_required("applications:read_own")
def download_document(current_user, app_id, doc_id):
    """
    Generate a pre-signed URL to download a document.
    
    Returns:
        200 — pre-signed URL for download
        404 — document not found
        403 — access denied
    """
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404

    doc = db.session.get(ApplicationDocument, doc_id)
    if not doc or doc.application_id != app_id:
        return jsonify({"error": "Document not found."}), 404

    try:
        url = s3_service.generate_presigned_url(
            doc.s3_key,
            expiry_seconds=3600,  # 1 hour
            filename_hint=doc.filename
        )
        return jsonify({"download_url": url}), 200
    except RuntimeError as exc:
        logger.error("Failed to generate presigned URL for doc %d: %s", doc_id, exc)
        return jsonify({"error": "Failed to generate download URL."}), 500


@bp.route("/<int:app_id>/documents/<int:doc_id>", methods=["DELETE"])
@token_required
@permission_required("applications:read_own")
def delete_document(current_user, app_id, doc_id):
    """
    Delete an uploaded document from S3 and database.
    
    Returns:
        204 — document deleted
        404 — document not found
        403 — access denied
    """
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404

    doc = db.session.get(ApplicationDocument, doc_id)
    if not doc or doc.application_id != app_id:
        return jsonify({"error": "Document not found."}), 404

    try:
        # Delete from S3
        s3_service.delete_object(doc.s3_key)
        
        # Delete from database
        db.session.delete(doc)
        db.session.commit()

        logger.info("Document deleted: app_id=%d doc_id=%d user_id=%d", app_id, doc_id, current_user.id)
        return "", 204

    except Exception as exc:
        logger.error("Failed to delete document %d: %s", doc_id, exc)
        return jsonify({"error": "Failed to delete document."}), 500
