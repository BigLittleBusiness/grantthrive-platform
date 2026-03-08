"""
GrantThrive — Applications API
================================
RBAC-protected REST endpoints for grant applications.

Permission matrix:
  applications:create      — community_member, professional_consultant
  applications:read_own    — community_member, professional_consultant (own only)
  applications:read        — council_staff, council_admin, system_admin
  applications:update_own  — community_member, professional_consultant (own, draft only)
  applications:delete_own  — community_member, professional_consultant (own, draft only)
  applications:review      — council_staff, council_admin, system_admin
  applications:approve     — council_admin, system_admin
  applications:reject      — council_admin, system_admin
  applications:update_status — council_staff, council_admin, system_admin

Endpoints:
  GET    /api/applications                — List own applications (community) or all (staff+)
  POST   /api/applications                — Submit a new application
  GET    /api/applications/<id>           — Get application detail
  PATCH  /api/applications/<id>           — Update a draft application (own only)
  DELETE /api/applications/<id>           — Delete a draft application (own only)
  POST   /api/applications/<id>/submit    — Submit a draft application
  POST   /api/applications/<id>/review    — Submit a review score (staff+)
  POST   /api/applications/<id>/approve   — Approve an application (admin+)
  POST   /api/applications/<id>/reject    — Reject an application (admin+)
  PATCH  /api/applications/<id>/status    — Update application status (staff+)
"""

import logging
from datetime import datetime, timezone

from flask import request, jsonify

from app import db
from app.applications import bp
from app.models import Application, Grant, Review
from app.common.permissions import permission_required, has_permission

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _app_to_dict(app: Application, detail: bool = False) -> dict:
    d = {
        "id":                app.id,
        "grant_id":          app.grant_id,
        "applicant_id":      app.applicant_id,
        "organization_name": app.organization_name,
        "project_title":     app.project_title,
        "amount_requested":  float(app.amount_requested) if app.amount_requested else None,
        "status":            app.status,
        "submitted_at":      app.submitted_at.isoformat() if app.submitted_at else None,
        "created_at":        app.created_at.isoformat() if app.created_at else None,
    }
    if detail:
        d.update({
            "project_description": app.project_description,
            "contact_person":      app.contact_person,
            "contact_email":       app.contact_email,
            "contact_phone":       app.contact_phone,
            "address":             app.address,
            "postcode":            app.postcode,
            "latitude":            app.latitude,
            "longitude":           app.longitude,
            "reviewed_at":         app.reviewed_at.isoformat() if app.reviewed_at else None,
            "decision_date":       app.decision_date.isoformat() if app.decision_date else None,
            "total_score":         app.total_score,
            "average_score":       app.average_score,
            "community_votes":     app.community_votes,
            "community_score":     app.community_score,
            "updated_at":          app.updated_at.isoformat() if app.updated_at else None,
        })
    return d


def _can_access_application(user, application: Application) -> bool:
    """Return True if the user is allowed to read this application."""
    if user.role == "system_admin":
        return True
    if user.role in ("council_admin", "council_staff"):
        grant = db.session.get(Grant, application.grant_id)
        return grant and grant.council_id == user.council_id
    return application.applicant_id == user.id


# ── Routes ────────────────────────────────────────────────────────────────────

@bp.route("/", methods=["GET"])
@permission_required("applications:read_own")
def list_applications(current_user):
    """List applications scoped by role."""
    page     = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    status   = request.args.get("status")
    grant_id = request.args.get("grant_id", type=int)

    query = Application.query

    if current_user.role == "system_admin":
        pass
    elif current_user.role in ("council_admin", "council_staff"):
        council_grant_ids = [
            g.id for g in Grant.query.filter_by(council_id=current_user.council_id).all()
        ]
        query = query.filter(Application.grant_id.in_(council_grant_ids))
    else:
        query = query.filter_by(applicant_id=current_user.id)

    if status:
        query = query.filter_by(status=status)
    if grant_id:
        query = query.filter_by(grant_id=grant_id)

    query = query.order_by(Application.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "applications": [_app_to_dict(a) for a in pagination.items],
        "total":        pagination.total,
        "page":         pagination.page,
        "per_page":     pagination.per_page,
        "total_pages":  pagination.pages,
    }), 200


@bp.route("/<int:app_id>", methods=["GET"])
@permission_required("applications:read_own")
def get_application(current_user, app_id):
    """Get a single application by ID."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404
    if not _can_access_application(current_user, application):
        return jsonify({"error": "Access denied."}), 403
    return jsonify(_app_to_dict(application, detail=True)), 200


@bp.route("/", methods=["POST"])
@permission_required("applications:create")
def create_application(current_user):
    """Create a new grant application."""
    data = request.get_json(silent=True) or {}

    required = ["grant_id", "organization_name", "project_title",
                 "project_description", "amount_requested",
                 "contact_person", "contact_email"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    grant = db.session.get(Grant, data["grant_id"])
    if not grant:
        return jsonify({"error": "Grant not found."}), 404
    if not grant.is_open:
        return jsonify({"error": "This grant is not currently accepting applications."}), 409

    if not grant.allow_multiple_applications:
        existing = Application.query.filter_by(
            grant_id=grant.id, applicant_id=current_user.id
        ).filter(Application.status != "withdrawn").first()
        if existing:
            return jsonify({"error": "You have already applied for this grant."}), 409

    application = Application(
        grant_id            = grant.id,
        applicant_id        = current_user.id,
        organization_name   = data["organization_name"].strip(),
        project_title       = data["project_title"].strip(),
        project_description = data["project_description"].strip(),
        amount_requested    = data["amount_requested"],
        contact_person      = data["contact_person"].strip(),
        contact_email       = data["contact_email"].strip().lower(),
        contact_phone       = data.get("contact_phone", "").strip() or None,
        address             = data.get("address"),
        postcode            = data.get("postcode"),
        latitude            = data.get("latitude"),
        longitude           = data.get("longitude"),
        status              = "draft",
    )
    db.session.add(application)
    db.session.commit()

    logger.info("Application created: id=%d grant_id=%d by user_id=%d",
                application.id, grant.id, current_user.id)
    return jsonify(_app_to_dict(application, detail=True)), 201


@bp.route("/<int:app_id>", methods=["PATCH"])
@permission_required("applications:update_own")
def update_application(current_user, app_id):
    """Update a draft application (own only)."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404
    if application.applicant_id != current_user.id and current_user.role != "system_admin":
        return jsonify({"error": "Access denied."}), 403
    if application.status != "draft":
        return jsonify({"error": "Only draft applications can be edited."}), 409

    data = request.get_json(silent=True) or {}
    updatable = [
        "organization_name", "project_title", "project_description",
        "amount_requested", "contact_person", "contact_email",
        "contact_phone", "address", "postcode", "latitude", "longitude",
    ]
    for field in updatable:
        if field in data:
            setattr(application, field, data[field])

    application.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(_app_to_dict(application, detail=True)), 200


@bp.route("/<int:app_id>", methods=["DELETE"])
@permission_required("applications:delete_own")
def delete_application(current_user, app_id):
    """Withdraw a draft or submitted application (own only)."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404
    if application.applicant_id != current_user.id and current_user.role != "system_admin":
        return jsonify({"error": "Access denied."}), 403
    if application.status not in ("draft", "submitted"):
        return jsonify({"error": "Only draft or submitted applications can be withdrawn."}), 409

    application.status     = "withdrawn"
    application.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"message": "Application withdrawn."}), 200


@bp.route("/<int:app_id>/submit", methods=["POST"])
@permission_required("applications:update_own")
def submit_application(current_user, app_id):
    """Submit a draft application for review."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404
    if application.applicant_id != current_user.id and current_user.role != "system_admin":
        return jsonify({"error": "Access denied."}), 403
    if application.status != "draft":
        return jsonify({"error": "Only draft applications can be submitted."}), 409

    grant = db.session.get(Grant, application.grant_id)
    if not grant or not grant.is_open:
        return jsonify({"error": "The grant is no longer accepting applications."}), 409

    application.status       = "submitted"
    application.submitted_at = datetime.now(timezone.utc)
    application.updated_at   = datetime.now(timezone.utc)
    db.session.commit()

    logger.info("Application submitted: id=%d by user_id=%d", application.id, current_user.id)
    return jsonify(_app_to_dict(application, detail=True)), 200


@bp.route("/<int:app_id>/review", methods=["POST"])
@permission_required("applications:review")
def review_application(current_user, app_id):
    """Submit a review for an application (council_staff+)."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404
    if not _can_access_application(current_user, application):
        return jsonify({"error": "Access denied."}), 403
    if application.status not in ("submitted", "under_review"):
        return jsonify({"error": "Application is not in a reviewable state."}), 409

    data = request.get_json(silent=True) or {}

    existing = Review.query.filter_by(
        application_id=application.id, reviewer_id=current_user.id
    ).first()

    if existing:
        existing.comments       = data.get("comments", existing.comments)
        existing.recommendation = data.get("recommendation", existing.recommendation)
        existing.total_score    = data.get("total_score", existing.total_score)
        existing.is_complete    = data.get("is_complete", existing.is_complete)
        if existing.is_complete:
            existing.submitted_at = datetime.now(timezone.utc)
        review = existing
    else:
        review = Review(
            application_id = application.id,
            reviewer_id    = current_user.id,
            comments       = data.get("comments"),
            recommendation = data.get("recommendation"),
            total_score    = data.get("total_score", 0.0),
            is_complete    = data.get("is_complete", False),
            submitted_at   = datetime.now(timezone.utc) if data.get("is_complete") else None,
        )
        db.session.add(review)

    if application.status == "submitted":
        application.status      = "under_review"
        application.reviewed_at = datetime.now(timezone.utc)

    application.calculate_scores()
    application.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "message":     "Review submitted.",
        "review_id":   review.id,
        "application": _app_to_dict(application, detail=True),
    }), 200


@bp.route("/<int:app_id>/approve", methods=["POST"])
@permission_required("applications:approve")
def approve_application(current_user, app_id):
    """Approve an application (council_admin or system_admin)."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404
    if not _can_access_application(current_user, application):
        return jsonify({"error": "Access denied."}), 403
    if application.status not in ("submitted", "under_review", "reviewed"):
        return jsonify({"error": "Application cannot be approved in its current state."}), 409

    application.status        = "approved"
    application.decision_date = datetime.now(timezone.utc)
    application.updated_at    = datetime.now(timezone.utc)
    db.session.commit()

    logger.info("Application approved: id=%d by user_id=%d", application.id, current_user.id)
    return jsonify({"message": "Application approved.", "application": _app_to_dict(application)}), 200


@bp.route("/<int:app_id>/reject", methods=["POST"])
@permission_required("applications:reject")
def reject_application(current_user, app_id):
    """Reject an application (council_admin or system_admin)."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404
    if not _can_access_application(current_user, application):
        return jsonify({"error": "Access denied."}), 403
    if application.status not in ("submitted", "under_review", "reviewed"):
        return jsonify({"error": "Application cannot be rejected in its current state."}), 409

    application.status        = "rejected"
    application.decision_date = datetime.now(timezone.utc)
    application.updated_at    = datetime.now(timezone.utc)
    db.session.commit()

    logger.info("Application rejected: id=%d by user_id=%d", application.id, current_user.id)
    return jsonify({"message": "Application rejected.", "application": _app_to_dict(application)}), 200


@bp.route("/<int:app_id>/status", methods=["PATCH"])
@permission_required("applications:update_status")
def update_application_status(current_user, app_id):
    """Update application status (council_staff+)."""
    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404
    if not _can_access_application(current_user, application):
        return jsonify({"error": "Access denied."}), 403

    data   = request.get_json(silent=True) or {}
    status = data.get("status")

    valid_statuses = ["draft", "submitted", "under_review", "reviewed",
                      "approved", "rejected", "withdrawn", "archived"]
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    if status in ("approved", "rejected") and not has_permission(current_user, "applications:approve"):
        return jsonify({"error": "Insufficient permissions to approve or reject applications."}), 403

    application.status     = status
    application.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"message": f"Status updated to '{status}'.", "application": _app_to_dict(application)}), 200
