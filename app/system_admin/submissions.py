"""System-admin APIs for protected public form submissions.

The API exposes decrypted submission data only after system-admin JWT and role
checks. It deliberately has no public route and records staff changes in the
audit log without copying visitor content into audit metadata.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from flask import jsonify, request

from app import db
from app.auth.routes import role_required
from app.models import AuditLog, PublicSubmission
from app.system_admin import bp

VALID_STATUSES = {"new", "in_progress", "resolved"}
VALID_TYPES = {"contact", "waitlist"}


def _iso(value):
    return value.isoformat() if value else None


def _summary(submission: PublicSubmission) -> dict:
    """Return list-safe fields to an authorised system administrator."""
    return {
        "id": submission.id,
        "submission_type": submission.submission_type,
        "contact_type": submission.contact_type,
        "status": submission.status,
        "name": submission.name,
        "email": submission.email,
        "organisation": submission.organisation,
        "received_at": _iso(submission.received_at),
        "notification_status": submission.notification_status,
        "resolved_at": _iso(submission.resolved_at),
    }


def _detail(submission: PublicSubmission) -> dict:
    data = _summary(submission)
    data.update({
        "phone": submission.phone,
        "message": submission.message,
        "internal_note": submission.internal_note,
        "notification_attempted_at": _iso(submission.notification_attempted_at),
        "updated_at": _iso(submission.updated_at),
        "resolved_by": (
            f"{submission.resolved_by.first_name or ''} {submission.resolved_by.last_name or ''}".strip()
            if submission.resolved_by
            else None
        ),
    })
    return data


def _audit(user_id: int, action: str, submission_id: int, *, old_status: str | None = None, new_status: str | None = None) -> None:
    """Add audit metadata without writing PII or message content to the audit log."""
    metadata = {"submission_id": submission_id}
    if old_status is not None:
        metadata["old_status"] = old_status
    if new_status is not None:
        metadata["new_status"] = new_status
    db.session.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type="public_submission",
            entity_id=submission_id,
            new_values=json.dumps(metadata, sort_keys=True),
            ip_address=(request.headers.get("CF-Connecting-IP") or request.remote_addr or "")[:45],
            user_agent=(request.headers.get("User-Agent") or "")[:500],
        )
    )


@bp.get("/admin/form-submissions")
@role_required("system_admin")
def list_form_submissions(current_user):
    """List form submissions with safe filters and pagination."""
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except ValueError:
        return jsonify({"error": "page and per_page must be numbers."}), 400

    status = request.args.get("status", "").strip()
    submission_type = request.args.get("type", "").strip()
    if status and status not in VALID_STATUSES:
        return jsonify({"error": "Unsupported status filter."}), 422
    if submission_type and submission_type not in VALID_TYPES:
        return jsonify({"error": "Unsupported form type filter."}), 422

    query = PublicSubmission.query
    if status:
        query = query.filter_by(status=status)
    if submission_type:
        query = query.filter_by(submission_type=submission_type)
    result = query.order_by(PublicSubmission.received_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "submissions": [_summary(item) for item in result.items],
        "pagination": {
            "page": result.page,
            "per_page": result.per_page,
            "pages": result.pages,
            "total": result.total,
        },
    }), 200


@bp.get("/admin/form-submissions/<int:submission_id>")
@role_required("system_admin")
def get_form_submission(current_user, submission_id: int):
    """Retrieve one protected submission and audit the privileged data view."""
    submission = db.session.get(PublicSubmission, submission_id)
    if not submission:
        return jsonify({"error": "Form submission not found."}), 404

    _audit(current_user.id, "public_submission.viewed", submission.id)
    db.session.commit()
    return jsonify({"submission": _detail(submission)}), 200


@bp.patch("/admin/form-submissions/<int:submission_id>")
@role_required("system_admin")
def update_form_submission(current_user, submission_id: int):
    """Update operational status and encrypted internal note for a submission."""
    submission = db.session.get(PublicSubmission, submission_id)
    if not submission:
        return jsonify({"error": "Form submission not found."}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A valid update is required."}), 400
    unexpected = set(data) - {"status", "internal_note"}
    if unexpected:
        return jsonify({"error": "Unsupported update fields."}), 400
    if not data:
        return jsonify({"error": "No changes were supplied."}), 422

    old_status = submission.status
    status_changed = False
    if "status" in data:
        status = data["status"]
        if not isinstance(status, str) or status not in VALID_STATUSES:
            return jsonify({"error": "Status must be new, in_progress, or resolved."}), 422
        status_changed = status != submission.status
        submission.status = status
        if status == "resolved":
            submission.resolved_at = datetime.now(timezone.utc)
            submission.resolved_by_user_id = current_user.id
        else:
            submission.resolved_at = None
            submission.resolved_by_user_id = None

    if "internal_note" in data:
        note = data["internal_note"]
        if not isinstance(note, str):
            return jsonify({"error": "internal_note must be text."}), 422
        note = note.strip()
        if len(note) > 5000:
            return jsonify({"error": "internal_note is too long."}), 422
        submission.internal_note = note or None

    _audit(
        current_user.id,
        "public_submission.updated",
        submission.id,
        old_status=old_status if status_changed else None,
        new_status=submission.status if status_changed else None,
    )
    db.session.commit()
    return jsonify({"message": "Submission updated.", "submission": _detail(submission)}), 200
