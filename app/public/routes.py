"""
GrantThrive — Public Data API
==============================
Unauthenticated JSON endpoints (mounted at /api/public):

  GET /grants            — Published grants
  GET /statistics        — Headline platform statistics
  GET /engagement-data   — Monthly votes/applications for the last 12 months
  GET /transparency      — Transparency dashboard data
  GET /results           — Approved grant outcomes
"""
from datetime import datetime, timedelta, timezone

from flask import jsonify
from sqlalchemy import func, desc

from app import db
from app.models import Grant, Application, CommunityVote, VotingSession
from app.public import public


def _published_applications(status=None):
    query = Application.query.join(Grant).filter(Grant.is_published == True)  # noqa: E712
    if status is None:
        return query.filter(Application.status != 'draft')
    return query.filter(Application.status == status)


def _approved_funding():
    return float(
        db.session.query(func.sum(Application.amount_requested)).join(Grant).filter(
            Grant.is_published == True, Application.status == 'approved'  # noqa: E712
        ).scalar() or 0
    )


def _total_published_budget():
    return float(
        db.session.query(func.sum(Grant.total_budget)).filter(
            Grant.is_published == True  # noqa: E712
        ).scalar() or 0
    )


def _published_votes_count():
    return CommunityVote.query.join(VotingSession).join(Grant).filter(
        Grant.is_published == True  # noqa: E712
    ).count()


def _active_voting_sessions_count():
    return VotingSession.query.join(Grant).filter(
        Grant.is_published == True, VotingSession.is_active == True  # noqa: E712
    ).count()


def _month_range(months_ago, now):
    month_start = (now.replace(day=1) - timedelta(days=30 * months_ago)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(seconds=1)
    return month_start, month_end


@public.route('/grants')
def grants():
    published = Grant.query.filter(Grant.is_published == True).all()  # noqa: E712
    data = [{
        'id': g.id,
        'title': g.title,
        'description': g.description,
        'category': g.category,
        'total_budget': float(g.total_budget or 0),
        'status': g.status,
        'opens_at': g.opens_at.isoformat() if g.opens_at else None,
        'closes_at': g.closes_at.isoformat() if g.closes_at else None,
        'application_count': g.applications.filter(Application.status != 'draft').count(),
        'location': {
            'name': g.location_name,
            'latitude': g.latitude,
            'longitude': g.longitude,
            'address': g.address,
            'postcode': g.postcode,
            'state': g.state,
        } if g.latitude and g.longitude else None,
    } for g in published]

    return jsonify({
        'grants': data,
        'total': len(data),
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


@public.route('/statistics')
def statistics():
    return jsonify({
        'grants': {
            'total': Grant.query.filter(Grant.is_published == True).count(),  # noqa: E712
            'active': Grant.query.filter(Grant.is_published == True, Grant.status == 'open').count(),  # noqa: E712
            'total_budget': _total_published_budget(),
        },
        'applications': {
            'total': _published_applications().count(),
            'approved': _published_applications('approved').count(),
            'total_requested': float(
                db.session.query(func.sum(Application.amount_requested)).join(Grant).filter(
                    Grant.is_published == True, Application.status != 'draft'  # noqa: E712
                ).scalar() or 0
            ),
            'total_approved': _approved_funding(),
        },
        'community': {
            'total_votes': _published_votes_count(),
            'active_voting_sessions': _active_voting_sessions_count(),
        },
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


@public.route('/engagement-data')
def engagement_data():
    now = datetime.now(timezone.utc)
    monthly = []
    for i in range(11, -1, -1):
        month_start, month_end = _month_range(i, now)
        monthly.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%b %Y'),
            'votes': CommunityVote.query.join(VotingSession).join(Grant).filter(
                Grant.is_published == True,  # noqa: E712
                CommunityVote.voted_at >= month_start,
                CommunityVote.voted_at <= month_end,
            ).count(),
            'applications': _published_applications().filter(
                Application.submitted_at >= month_start,
                Application.submitted_at <= month_end,
            ).count(),
        })

    return jsonify({'monthly_engagement': monthly, 'timestamp': now.isoformat()})


@public.route('/transparency')
def transparency():
    now = datetime.now(timezone.utc)
    total_applications = _published_applications().count()
    approved_applications = _published_applications('approved').count()

    category_stats = db.session.query(
        Grant.category,
        func.count(Grant.id).label('count'),
        func.sum(Grant.total_budget).label('total_budget'),
    ).filter(Grant.is_published == True).group_by(Grant.category).all()  # noqa: E712

    monthly_trends = []
    for i in range(11, -1, -1):
        month_start, month_end = _month_range(i, now)
        count = _published_applications().filter(
            Application.submitted_at >= month_start,
            Application.submitted_at <= month_end,
        ).count()
        monthly_trends.append({'month': month_start.strftime('%b %Y'), 'applications': count})

    recent_grants = Grant.query.filter(
        Grant.is_published == True,  # noqa: E712
        Grant.created_at >= now - timedelta(days=30),
    ).order_by(desc(Grant.created_at)).limit(10).all()

    return jsonify({
        'summary': {
            'total_grants': Grant.query.filter_by(is_published=True).count(),
            'active_grants': Grant.query.filter(Grant.is_published == True, Grant.status == 'open').count(),  # noqa: E712
            'total_applications': total_applications,
            'approved_applications': approved_applications,
            'total_budget': _total_published_budget(),
            'total_approved_funding': _approved_funding(),
            'total_votes': _published_votes_count(),
            'active_voting_sessions': _active_voting_sessions_count(),
            'approval_rate': round(
                approved_applications / total_applications * 100 if total_applications else 0, 1
            ),
        },
        'category_stats': [{
            'category': c.category or 'Uncategorised',
            'count': c.count,
            'total_budget': float(c.total_budget or 0),
        } for c in category_stats],
        'monthly_trends': monthly_trends,
        'recent_grants': [{
            'id': g.id,
            'title': g.title,
            'category': g.category,
            'status': g.status,
            'total_budget': float(g.total_budget or 0),
            'closes_at': g.closes_at.isoformat() if g.closes_at else None,
        } for g in recent_grants],
        'timestamp': now.isoformat(),
    })


@public.route('/results')
def results():
    now = datetime.now(timezone.utc)

    impact_by_category = db.session.query(
        Grant.category,
        func.count(Application.id).label('projects'),
        func.sum(Application.amount_requested).label('funding'),
    ).join(Application).filter(
        Grant.is_published == True, Application.status == 'approved'  # noqa: E712
    ).group_by(Grant.category).all()

    recent_successes = _published_applications('approved').order_by(
        desc(Application.submitted_at)
    ).limit(20).all()

    completed_grants = Grant.query.filter(
        Grant.is_published == True, Grant.status == 'closed'  # noqa: E712
    ).order_by(desc(Grant.closes_at)).limit(20).all()

    return jsonify({
        'summary': {
            'total_funded': _approved_funding(),
            'total_projects': _published_applications('approved').count(),
        },
        'impact_by_category': [{
            'category': row.category or 'Uncategorised',
            'projects': row.projects,
            'funding': float(row.funding or 0),
        } for row in impact_by_category],
        'recent_successes': [{
            'id': a.id,
            'title': a.project_title or f'Application #{a.id}',
            'organisation': a.organization_name or '',
            'amount': float(a.amount_requested or 0),
            'grant_title': a.grant.title if a.grant else '',
            'category': a.grant.category if a.grant else '',
            'approved_at': a.submitted_at.isoformat() if a.submitted_at else None,
        } for a in recent_successes],
        'completed_grants': [{
            'id': g.id,
            'title': g.title,
            'category': g.category,
            'total_budget': float(g.total_budget or 0),
            'closes_at': g.closes_at.isoformat() if g.closes_at else None,
            'approved_count': Application.query.filter_by(grant_id=g.id, status='approved').count(),
        } for g in completed_grants],
        'timestamp': now.isoformat(),
    })
