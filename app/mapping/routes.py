"""
GrantThrive — Grant Mapping API
================================
JSON endpoints (mounted at /api/mapping):

  GET  /grants-geojson            — Grants with coordinates as a GeoJSON FeatureCollection
                                    (?category=&status=&min_budget=&max_budget=)
  GET  /grant-impact/<id>         — Applications and community engagement for one grant
  POST /admin/geocode-grants      — Fill in missing grant coordinates (system_admin)
"""
from flask import request, jsonify
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.geocoders import Nominatim
from sqlalchemy import func, or_

from app import db
from app.common.decorators import role_required
from app.mapping import mapping
from app.models import Grant, Application, CommunityVote

geolocator = Nominatim(user_agent="grantthrive_mapping")


@mapping.route('/grants-geojson')
def grants_geojson():
    application_stats = db.session.query(
        Application.grant_id,
        func.count(Application.id).label('application_count'),
        func.sum(Application.amount_requested).label('total_requested'),
    ).group_by(Application.grant_id).subquery()

    vote_stats = db.session.query(
        Application.grant_id,
        func.count(CommunityVote.id).label('community_votes'),
    ).join(CommunityVote, CommunityVote.application_id == Application.id).group_by(
        Application.grant_id
    ).subquery()

    query = db.session.query(
        Grant,
        application_stats.c.application_count,
        application_stats.c.total_requested,
        vote_stats.c.community_votes,
    ).outerjoin(application_stats, application_stats.c.grant_id == Grant.id).outerjoin(
        vote_stats, vote_stats.c.grant_id == Grant.id
    ).filter(Grant.latitude.isnot(None), Grant.longitude.isnot(None))

    if request.args.get('category'):
        query = query.filter(Grant.category == request.args['category'])
    if request.args.get('status'):
        query = query.filter(Grant.status == request.args['status'])
    min_budget = request.args.get('min_budget', type=float)
    max_budget = request.args.get('max_budget', type=float)
    if min_budget is not None:
        query = query.filter(Grant.total_budget >= min_budget)
    if max_budget is not None:
        query = query.filter(Grant.total_budget <= max_budget)

    features = []
    for grant, application_count, total_requested, community_votes in query.all():
        description = grant.description or ''
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(grant.longitude), float(grant.latitude)],
            },
            "properties": {
                "id": grant.id,
                "title": grant.title,
                "category": grant.category,
                "total_budget": float(grant.total_budget or 0),
                "status": grant.status,
                "location_name": grant.location_name,
                "description": description[:200] + "..." if len(description) > 200 else description,
                "opens_at": grant.opens_at.isoformat() if grant.opens_at else None,
                "closes_at": grant.closes_at.isoformat() if grant.closes_at else None,
                "application_count": application_count or 0,
                "total_requested": float(total_requested or 0),
                "community_votes": community_votes or 0,
            },
        })

    return jsonify({"type": "FeatureCollection", "features": features})


@mapping.route('/grant-impact/<int:grant_id>')
def grant_impact(grant_id):
    grant = db.session.get(Grant, grant_id)
    if not grant:
        return jsonify({'error': 'Grant not found'}), 404

    applications = Application.query.filter_by(grant_id=grant_id).all()
    voting_data = db.session.query(
        CommunityVote.voter_postcode,
        func.count(CommunityVote.id).label('vote_count'),
        func.avg(CommunityVote.vote_value).label('avg_rating'),
    ).filter(
        CommunityVote.application_id.in_([a.id for a in applications])
    ).group_by(CommunityVote.voter_postcode).all()

    return jsonify({
        'grant': {
            'id': grant.id,
            'title': grant.title,
            'total_budget': float(grant.total_budget or 0),
            'location': grant.location_name,
        },
        'applications': [{
            'id': a.id,
            'organization': a.organization_name,
            'amount_requested': float(a.amount_requested or 0),
            'status': a.status,
            'postcode': a.postcode,
        } for a in applications],
        'community_engagement': [{
            'postcode': v.voter_postcode,
            'vote_count': v.vote_count,
            'avg_rating': float(v.avg_rating or 0),
        } for v in voting_data if v.voter_postcode],
    })


@mapping.route('/admin/geocode-grants', methods=['POST'])
@role_required('system_admin')
def geocode_grants(current_user):
    grants_to_geocode = Grant.query.filter(
        or_(Grant.latitude.is_(None), Grant.longitude.is_(None))
    ).all()

    geocoded_count = 0
    failed_count = 0
    for grant in grants_to_geocode:
        try:
            location = geolocator.geocode(grant.location_name or "Australia", timeout=10)
        except (GeocoderTimedOut, GeocoderServiceError):
            location = None
        if location:
            grant.latitude = location.latitude
            grant.longitude = location.longitude
            geocoded_count += 1
        else:
            failed_count += 1

    db.session.commit()
    return jsonify({
        'success': True,
        'geocoded_count': geocoded_count,
        'failed_count': failed_count,
        'message': f'Geocoded {geocoded_count} grants, {failed_count} failed',
    })
