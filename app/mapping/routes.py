"""Grant mapping API with public-data safeguards.

The public map exposes only published grants and aggregate, non-identifying
outcome data. Detailed application information stays behind tenant/RBAC routes.
"""
from flask import jsonify, request
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim
from sqlalchemy import func, or_

from app import db
from app.common.decorators import role_required
from app.mapping import mapping
from app.models import Application, CommunityVote, Grant

geolocator = Nominatim(user_agent="grantthrive_mapping")
PUBLIC_APPLICATION_STATUSES = ("approved",)


@mapping.route("/grants-geojson")
def grants_geojson():
    application_stats = (
        db.session.query(
            Application.grant_id,
            func.count(Application.id).label("approved_project_count"),
            func.sum(Application.amount_requested).label("approved_funding"),
        )
        .filter(Application.status.in_(PUBLIC_APPLICATION_STATUSES))
        .group_by(Application.grant_id)
        .subquery()
    )
    vote_stats = (
        db.session.query(Application.grant_id, func.count(CommunityVote.id).label("community_votes"))
        .join(CommunityVote, CommunityVote.application_id == Application.id)
        .group_by(Application.grant_id)
        .subquery()
    )
    query = (
        db.session.query(Grant, application_stats.c.approved_project_count, application_stats.c.approved_funding, vote_stats.c.community_votes)
        .outerjoin(application_stats, application_stats.c.grant_id == Grant.id)
        .outerjoin(vote_stats, vote_stats.c.grant_id == Grant.id)
        .filter(
            Grant.is_published.is_(True),
            Grant.enable_mapping.is_(True),
            Grant.latitude.isnot(None),
            Grant.longitude.isnot(None),
        )
    )
    council_id = request.args.get("council_id", type=int)
    if council_id is not None:
        query = query.filter(Grant.council_id == council_id)
    if request.args.get("category"):
        query = query.filter(Grant.category == request.args["category"])
    if request.args.get("status"):
        query = query.filter(Grant.status == request.args["status"])
    min_budget = request.args.get("min_budget", type=float)
    max_budget = request.args.get("max_budget", type=float)
    if min_budget is not None:
        query = query.filter(Grant.total_budget >= min_budget)
    if max_budget is not None:
        query = query.filter(Grant.total_budget <= max_budget)

    limit = min(max(request.args.get("limit", 200, type=int) or 200, 1), 500)
    offset = max(request.args.get("offset", 0, type=int) or 0, 0)
    features = []
    for grant, project_count, approved_funding, community_votes in query.order_by(Grant.id.desc()).offset(offset).limit(limit).all():
        description = grant.description or ""
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(grant.longitude), float(grant.latitude)]},
            "properties": {
                "id": grant.id,
                "title": grant.title,
                "category": grant.category,
                "total_budget": float(grant.total_budget or 0),
                "status": grant.status,
                "location_name": grant.location_name,
                "description": description[:200] + "…" if len(description) > 200 else description,
                "opens_at": grant.opens_at.isoformat() if grant.opens_at else None,
                "closes_at": grant.closes_at.isoformat() if grant.closes_at else None,
                "approved_project_count": project_count or 0,
                "approved_funding": float(approved_funding or 0),
                "community_votes": community_votes or 0,
            },
        })
    return jsonify({"type": "FeatureCollection", "features": features, "limit": limit, "offset": offset})


@mapping.route("/grant-impact/<int:grant_id>")
def grant_impact(grant_id):
    grant = Grant.query.filter_by(id=grant_id, is_published=True, enable_mapping=True).first()
    if not grant:
        return jsonify({"error": "Grant not found"}), 404

    approved = Application.query.filter_by(grant_id=grant.id, status="approved")
    project_count = approved.count()
    approved_funding = db.session.query(func.sum(Application.amount_requested)).filter_by(grant_id=grant.id, status="approved").scalar() or 0
    voting_data = (
        db.session.query(
            CommunityVote.voter_postcode,
            func.count(CommunityVote.id).label("vote_count"),
            func.avg(CommunityVote.vote_value).label("avg_rating"),
        )
        .join(Application, Application.id == CommunityVote.application_id)
        .filter(Application.grant_id == grant.id, Application.status == "approved")
        .group_by(CommunityVote.voter_postcode)
        .order_by(func.count(CommunityVote.id).desc())
        .limit(200)
        .all()
    )
    return jsonify({
        "grant": {"id": grant.id, "title": grant.title, "total_budget": float(grant.total_budget or 0), "location": grant.location_name},
        "application_summary": {"approved_project_count": project_count, "approved_funding": float(approved_funding)},
        "community_engagement": [
            {"postcode": row.voter_postcode, "vote_count": row.vote_count, "avg_rating": float(row.avg_rating or 0)}
            for row in voting_data if row.voter_postcode
        ],
    })


@mapping.route("/admin/geocode-grants", methods=["POST"])
@role_required("system_admin")
def geocode_grants(current_user):
    batch_size = min(max((request.get_json(silent=True) or {}).get("batch_size", 50), 1), 100)
    grants_to_geocode = Grant.query.filter(or_(Grant.latitude.is_(None), Grant.longitude.is_(None))).order_by(Grant.id).limit(batch_size).all()
    geocoded_count = failed_count = 0
    for grant in grants_to_geocode:
        try:
            location = geolocator.geocode(grant.location_name or "Australia", timeout=10)
        except (GeocoderTimedOut, GeocoderServiceError):
            location = None
        if location:
            grant.latitude, grant.longitude = location.latitude, location.longitude
            geocoded_count += 1
        else:
            failed_count += 1
    db.session.commit()
    return jsonify({"success": True, "geocoded_count": geocoded_count, "failed_count": failed_count})
