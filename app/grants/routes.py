"""
GrantThrive — Grants API
=========================
RBAC-protected REST endpoints for grant management.

Permission matrix:
  grants:list    — community_member, professional_consultant, council_staff,
                   council_admin, system_admin
  grants:read    — all authenticated users
  grants:create  — council_admin, system_admin
  grants:update  — council_admin, system_admin
  grants:delete  — council_admin, system_admin
  grants:publish — council_admin, system_admin

Tenant scoping:
  All council-scoped roles can only access grants belonging to their council.
  system_admin can access grants across all councils.

Endpoints:
  GET    /api/grants                   — List grants
  POST   /api/grants                   — Create a new grant
  GET    /api/grants/<id>              — Get grant detail
  PATCH  /api/grants/<id>              — Update a grant
  DELETE /api/grants/<id>              — Soft-delete a grant
  POST   /api/grants/<id>/publish      — Publish / unpublish a grant
  GET    /api/grants/<id>/applications — List applications for a grant
"""

import json
import logging
from datetime import datetime, timezone

from flask import request, jsonify

from app import db
from app.grants import bp
from app.models import Grant, Application, ApplicationAssignment, Council, User
from app.common.permissions import permission_required, has_permission
from app.common.plans import check_grant_limit, can_use_feature

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _grant_to_dict(grant: Grant, detail: bool = False) -> dict:
    d = {
        "id":             grant.id,
        "council_id":     grant.council_id,
        "title":          grant.title,
        "description":    grant.description,
        "category":       grant.category,
        "total_budget":   float(grant.total_budget) if grant.total_budget else None,
        "max_amount":     float(grant.max_amount_per_application) if grant.max_amount_per_application else None,
        "min_amount":     float(grant.min_amount_per_application) if grant.min_amount_per_application else None,
        "opens_at":       grant.opens_at.isoformat() if grant.opens_at else None,
        "closes_at":      grant.closes_at.isoformat() if grant.closes_at else None,
        "status":         grant.status,
        "is_published":   grant.is_published,
        "is_open":        grant.is_open,
        "days_remaining": grant.days_remaining,
        "created_at":     grant.created_at.isoformat() if grant.created_at else None,
    }
    if detail:
        d.update({
            "assessment_deadline":         grant.assessment_deadline.isoformat() if grant.assessment_deadline else None,
            "notification_date":           grant.notification_date.isoformat() if grant.notification_date else None,
            "allow_multiple_applications": grant.allow_multiple_applications,
            "require_community_voting":    grant.require_community_voting,
            "enable_mapping":              grant.enable_mapping,
            "location_name":               grant.location_name,
            "latitude":                    grant.latitude,
            "longitude":                   grant.longitude,
            "address":                     grant.address,
            "postcode":                    grant.postcode,
            "state":                       grant.state,
            "region":                      grant.region,
            "created_by":                  grant.created_by,
            "updated_at":                  grant.updated_at.isoformat() if grant.updated_at else None,
            "assigned_reviewer_ids":       json.loads(grant.assigned_reviewer_ids or "[]"),
            "required_approvals":          grant.required_approvals,
        })
    return d


def _assert_council_scope(user, grant: Grant):
    """Return 403 response tuple if user cannot access this grant, else None."""
    if user.role == "system_admin":
        return None
    if grant.council_id != user.council_id:
        return jsonify({"error": "Access restricted to your own council."}), 403
    return None


def _validate_reviewer_ids(raw_ids, council_id: int) -> list:
    """
    Validate a list of reviewer user IDs.
    - Accepts a list of integers (or strings that can be cast to int).
    - Filters out any IDs that do not belong to the given council as
      council_staff or council_admin.
    - Returns a de-duplicated list of valid integer IDs.
    """
    if not raw_ids or not isinstance(raw_ids, list):
        return []
    try:
        ids = list({int(i) for i in raw_ids})
    except (TypeError, ValueError):
        return []

    valid = (
        User.query
        .filter(
            User.id.in_(ids),
            User.council_id == council_id,
            User.role.in_(["council_admin", "council_staff"]),
            User.is_active == True,
        )
        .with_entities(User.id)
        .all()
    )
    return [row.id for row in valid]


# ── Routes ────────────────────────────────────────────────────────────────────

@bp.route("", methods=["GET"])
@bp.route("/", methods=["GET"])
@permission_required("grants:list")
def list_grants(current_user):
    """List grants, scoped to the user's council (or all for system_admin)."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    status = request.args.get("status")
    category = request.args.get("category")
    search = request.args.get("q", "").strip()

    query = Grant.query

    if current_user.role != "system_admin":
        query = query.filter_by(council_id=current_user.council_id)
        if current_user.role in ("community_member", "professional_consultant"):
            query = query.filter_by(is_published=True)

    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Grant.title.ilike(f"%{search}%"))

    query = query.order_by(Grant.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "grants": [_grant_to_dict(g) for g in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": pagination.pages,
    }), 200


@bp.route("/<int:grant_id>", methods=["GET"])
@permission_required("grants:read")
def get_grant(current_user, grant_id):
    """Get a single grant by ID."""
    grant = db.session.get(Grant, grant_id)
    if not grant:
        return jsonify({"error": "Grant not found."}), 404

    scope_error = _assert_council_scope(current_user, grant)
    if scope_error:
        return scope_error

    if current_user.role in ("community_member", "professional_consultant") and not grant.is_published:
        return jsonify({"error": "Grant not found."}), 404

    return jsonify(_grant_to_dict(grant, detail=True)), 200


@bp.route("", methods=["POST"])
@bp.route("/", methods=["POST"])
@permission_required("grants:create")
def create_grant(current_user):
    """Create a new grant (council_admin or system_admin only)."""
    data = request.get_json(silent=True) or {}

    required = ["title", "description", "category", "total_budget", "opens_at", "closes_at"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    council = None

    if current_user.role == "system_admin":
        council_id = data.get("council_id")
        if not council_id:
            return jsonify({"error": "council_id is required for system_admin."}), 400

        council = db.session.get(Council, council_id)
        if not council:
            return jsonify({"error": "Council not found."}), 404
    else:
        council_id = current_user.council_id
        if not council_id:
            return jsonify({
                "error": "Your account is not linked to a council. Please contact support or your system administrator."
            }), 400

        council = db.session.get(Council, council_id)
        if not council:
            return jsonify({"error": "Council not found for this user."}), 404

        ok, msg = check_grant_limit(council)
        if not ok:
            return jsonify({"error": msg}), 403

        if data.get("require_community_voting"):
            if not can_use_feature(council, "community_voting"):
                return jsonify({
                    "error": "Community Voting is not included in your plan. "
                             "Upgrade to Medium Council or add the Community Voting add-on (+$50/mo)."
                }), 403

        if data.get("enable_mapping"):
            if not can_use_feature(council, "grant_mapping"):
                return jsonify({
                    "error": "Grant Mapping is not included in your plan. "
                             "Upgrade to Large Council or add the Grant Mapping add-on (+$100/mo)."
                }), 403

    try:
        opens_at = datetime.fromisoformat(data["opens_at"])
        closes_at = datetime.fromisoformat(data["closes_at"])
        assessment_deadline = (
            datetime.fromisoformat(data["assessment_deadline"])
            if data.get("assessment_deadline") else None
        )
        notification_date = (
            datetime.fromisoformat(data["notification_date"])
            if data.get("notification_date") else None
        )
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO-8601."}), 400

    grant = Grant(
        council_id=council_id,
        title=data["title"].strip(),
        description=data["description"].strip(),
        category=data["category"].strip(),
        total_budget=data["total_budget"],
        max_amount_per_application=data.get("max_amount_per_application"),
        min_amount_per_application=data.get("min_amount_per_application"),
        opens_at=opens_at,
        closes_at=closes_at,
        assessment_deadline=assessment_deadline,
        notification_date=notification_date,
        status=data.get("status", "draft"),
        is_published=bool(data.get("is_published", False)),
        allow_multiple_applications=bool(data.get("allow_multiple_applications", False)),
        require_community_voting=bool(data.get("require_community_voting", False)),
        enable_mapping=bool(data.get("enable_mapping", False)),
        location_name=data.get("location_name"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        address=data.get("address"),
        postcode=data.get("postcode"),
        state=data.get("state"),
        region=data.get("region"),
        created_by=current_user.id,
        assigned_reviewer_ids=json.dumps(
            _validate_reviewer_ids(data.get("assigned_reviewer_ids", []), council_id)
        ),
        required_approvals=max(1, int(data.get("required_approvals", 1))),
    )
    db.session.add(grant)
    db.session.commit()

    logger.info("Grant created: id=%d title=%s by user_id=%d", grant.id, grant.title, current_user.id)
    return jsonify(_grant_to_dict(grant, detail=True)), 201


@bp.route("/<int:grant_id>", methods=["PATCH"])
@permission_required("grants:update")
def update_grant(current_user, grant_id):
    """Update a grant."""
    grant = db.session.get(Grant, grant_id)
    if not grant:
        return jsonify({"error": "Grant not found."}), 404

    scope_error = _assert_council_scope(current_user, grant)
    if scope_error:
        return scope_error

    data = request.get_json(silent=True) or {}
    updatable = [
        "title", "description", "category", "total_budget",
        "max_amount_per_application", "min_amount_per_application",
        "opens_at", "closes_at", "assessment_deadline", "notification_date",
        "status", "allow_multiple_applications", "require_community_voting",
        "enable_mapping", "location_name", "latitude", "longitude",
        "address", "postcode", "state", "region",
    ]

    for field in updatable:
        if field in data:
            val = data[field]
            if field in ("opens_at", "closes_at", "assessment_deadline", "notification_date") and val:
                try:
                    val = datetime.fromisoformat(val)
                except ValueError:
                    return jsonify({"error": f"Invalid date for {field}."}), 400
            setattr(grant, field, val)

    if "assigned_reviewer_ids" in data:
        grant.assigned_reviewer_ids = json.dumps(
            _validate_reviewer_ids(data["assigned_reviewer_ids"], grant.council_id)
        )
    if "required_approvals" in data:
        grant.required_approvals = max(1, int(data["required_approvals"]))

    grant.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info("Grant updated: id=%d by user_id=%d", grant.id, current_user.id)
    return jsonify(_grant_to_dict(grant, detail=True)), 200


@bp.route("/<int:grant_id>", methods=["DELETE"])
@permission_required("grants:delete")
def delete_grant(current_user, grant_id):
    """Soft-delete a grant by setting status to 'archived'."""
    grant = db.session.get(Grant, grant_id)
    if not grant:
        return jsonify({"error": "Grant not found."}), 404

    scope_error = _assert_council_scope(current_user, grant)
    if scope_error:
        return scope_error

    grant.status = "archived"
    grant.is_published = False
    grant.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info("Grant archived: id=%d by user_id=%d", grant.id, current_user.id)
    return jsonify({"message": "Grant archived successfully."}), 200


@bp.route("/<int:grant_id>/publish", methods=["POST"])
@permission_required("grants:publish")
def publish_grant(current_user, grant_id):
    """Toggle published state of a grant."""
    grant = db.session.get(Grant, grant_id)
    if not grant:
        return jsonify({"error": "Grant not found."}), 404

    scope_error = _assert_council_scope(current_user, grant)
    if scope_error:
        return scope_error

    data = request.get_json(silent=True) or {}
    publish = data.get("publish", True)

    grant.is_published = bool(publish)
    if publish and grant.status == "draft":
        grant.status = "open"
    elif not publish:
        grant.status = "draft"

    grant.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    action = "published" if publish else "unpublished"
    logger.info("Grant %s: id=%d by user_id=%d", action, grant.id, current_user.id)
    return jsonify({"message": f"Grant {action}.", "grant": _grant_to_dict(grant)}), 200


@bp.route("/<int:grant_id>/applications", methods=["GET"])
@permission_required("applications:read")
def list_grant_applications(current_user, grant_id):
    """List applications for a grant (staff and above)."""
    grant = db.session.get(Grant, grant_id)
    if not grant:
        return jsonify({"error": "Grant not found."}), 404

    scope_error = _assert_council_scope(current_user, grant)
    if scope_error:
        return scope_error

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    status = request.args.get("status")

    query = Application.query.filter_by(grant_id=grant_id)
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Application.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    def _app_summary(a):
        return {
            "id": a.id,
            "organization_name": a.organization_name,
            "project_title": a.project_title,
            "amount_requested": float(a.amount_requested) if a.amount_requested else None,
            "status": a.status,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            "average_score": a.average_score,
        }

    return jsonify({
        "applications": [_app_summary(a) for a in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": pagination.pages,
    }), 200


@bp.route("/<int:grant_id>/reviewers", methods=["GET"])
@permission_required("grants:read")
def list_grant_reviewers(current_user, grant_id):
    """
    Return the list of staff members available to be assigned as reviewers
    for this grant.
    """
    grant = db.session.get(Grant, grant_id)
    if not grant:
        return jsonify({"error": "Grant not found."}), 404

    scope_error = _assert_council_scope(current_user, grant)
    if scope_error:
        return scope_error

    assigned_ids = set(json.loads(grant.assigned_reviewer_ids or "[]"))

    reviewers = (
        User.query
        .filter(
            User.council_id == grant.council_id,
            User.role.in_(["council_admin", "council_staff"]),
            User.is_active == True,
        )
        .order_by(User.first_name.asc(), User.last_name.asc())
        .all()
    )

    return jsonify({
        "reviewers": [
            {
                "id": u.id,
                "name": u.full_name,
                "email": u.email,
                "role": u.role,
                "assigned": u.id in assigned_ids,
            }
            for u in reviewers
        ]
    }), 200