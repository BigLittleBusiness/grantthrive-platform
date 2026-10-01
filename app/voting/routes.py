"""
GrantThrive — Community Voting API
===================================
Public JSON endpoints (mounted at /api/voting):

  GET  /sessions                    — Published voting sessions (?status=open|closed|scheduled|all)
  GET  /sessions/<id>               — One session, plus the caller's existing votes
  POST /sessions/<id>/vote          — Cast or update a vote
  GET  /results/<id>                — Aggregated results for a session

Voting is open to anonymous users; when a valid JWT is supplied the vote is
attributed to that user and per-user security checks apply.
"""
from datetime import datetime, timezone

from flask import request, jsonify
from sqlalchemy import desc

from app import db
from app.common.decorators import get_optional_user
from app.models import Grant, Application, CommunityVote, VotingSession, VotingResult
from app.voting import voting
from app.voting.security import (
    validate_vote_security, security_manager, log_vote_attempt, create_vote_fingerprint,
)

VOTABLE_STATUSES = ('submitted', 'under_review', 'approved')


def _session_to_dict(session):
    grant = db.session.get(Grant, session.grant_id)
    applications = Application.query.filter(
        Application.grant_id == session.grant_id,
        Application.status.in_(VOTABLE_STATUSES),
    ).all()

    options = []
    for app in applications:
        result = VotingResult.query.filter_by(
            application_id=app.id, voting_session_id=session.id
        ).first()
        options.append({
            'id': app.id,
            'title': app.project_title or f'Application #{app.id}',
            'description': app.project_description or '',
            'category': grant.category if grant else '',
            'estimated_budget': app.amount_requested or 0,
            'vote_count': result.total_votes if result else 0,
            'average_score': round(result.average_score, 2) if result else 0.0,
        })

    total_votes = sum(o['vote_count'] for o in options)
    for o in options:
        o['percentage'] = round(o['vote_count'] / total_votes * 100, 1) if total_votes else 0

    return {
        'id': session.id,
        'title': session.title,
        'description': session.description or '',
        'grant_title': grant.title if grant else '',
        'voting_type': session.voting_type,
        'min_vote_value': session.min_vote_value,
        'max_vote_value': session.max_vote_value,
        'allow_comments': session.allow_comments,
        'require_registration': session.require_registration,
        'starts_at': session.starts_at.isoformat(),
        'ends_at': session.ends_at.isoformat(),
        'status': session.status,
        'total_votes': session.total_votes,
        'unique_voters': session.total_voters,
        'options': options,
    }


@voting.route('/sessions', methods=['GET'])
def list_sessions():
    status_filter = request.args.get('status', 'open')
    now = datetime.now(timezone.utc)

    query = VotingSession.query.filter(VotingSession.is_published == True)  # noqa: E712
    if status_filter == 'open':
        query = query.filter(
            VotingSession.is_active == True,  # noqa: E712
            VotingSession.starts_at <= now,
            VotingSession.ends_at >= now,
        )
    elif status_filter == 'closed':
        query = query.filter(VotingSession.ends_at < now)
    elif status_filter == 'scheduled':
        query = query.filter(VotingSession.starts_at > now)

    sessions = query.order_by(VotingSession.starts_at.desc()).all()
    return jsonify({
        'sessions': [_session_to_dict(s) for s in sessions],
        'total': len(sessions),
    })


@voting.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    session = db.session.get(VotingSession, session_id)
    if not session or not session.is_published:
        return jsonify({'error': 'Voting session not found'}), 404

    data = _session_to_dict(session)
    user = get_optional_user()
    data['user_votes'] = {}
    if user:
        votes = CommunityVote.query.filter_by(voting_session_id=session_id, voter_id=user.id).all()
        data['user_votes'] = {str(v.application_id): v.vote_value for v in votes}
    return jsonify(data)


@voting.route('/sessions/<int:session_id>/vote', methods=['POST'])
def submit_vote(session_id):
    data = request.get_json(silent=True) or {}
    application_id = data.get('application_id')
    vote_value = data.get('vote_value')
    if application_id is None or vote_value is None:
        return jsonify({'error': 'Missing required fields'}), 400

    user = get_optional_user()
    voter_id = user.id if user else None
    comments = data.get('comments', '')

    session = db.session.get(VotingSession, session_id)
    if not session or not session.is_open:
        log_vote_attempt(voter_id, application_id, session_id, False, "Session not open")
        return jsonify({'error': 'Voting session is not open'}), 400

    if not (session.min_vote_value <= vote_value <= session.max_vote_value):
        log_vote_attempt(voter_id, application_id, session_id, False, "Invalid vote value")
        return jsonify({'error': 'Invalid vote value'}), 400

    application = db.session.get(Application, application_id)
    if not application or application.grant_id != session.grant_id:
        log_vote_attempt(voter_id, application_id, session_id, False, "Invalid application")
        return jsonify({'error': 'Invalid application'}), 400

    if user:
        is_eligible, reason = validate_vote_security(user.id, application_id, session_id)
        if not is_eligible:
            log_vote_attempt(user.id, application_id, session_id, False, reason)
            return jsonify({'error': reason}), 403

    ip_address = request.remote_addr or ''
    user_agent = request.headers.get('User-Agent', '')

    existing = CommunityVote.query.filter(
        CommunityVote.application_id == application_id,
        CommunityVote.voting_session_id == session_id,
    )
    if user:
        existing = existing.filter(CommunityVote.voter_id == user.id)
    elif data.get('voter_email'):
        existing = existing.filter(CommunityVote.voter_email == data['voter_email'])
    else:
        # Anonymous without email: one vote per IP per application
        existing = existing.filter(
            CommunityVote.ip_address == ip_address,
            CommunityVote.voter_id.is_(None),
        )
    existing_vote = existing.first()

    try:
        fingerprint = create_vote_fingerprint(voter_id or 0, ip_address, user_agent)
        if existing_vote:
            existing_vote.vote_value = vote_value
            existing_vote.comments = comments
            existing_vote.updated_at = datetime.now(timezone.utc)
            existing_vote.user_agent = user_agent
            existing_vote.fingerprint = fingerprint
            vote_id = existing_vote.id
        else:
            vote = CommunityVote(
                application_id=application_id,
                voting_session_id=session_id,
                voter_id=voter_id,
                vote_value=vote_value,
                vote_type=session.voting_type,
                comments=comments,
                voter_email=data.get('voter_email'),
                voter_postcode=data.get('voter_postcode'),
                voter_name=data.get('voter_name'),
                ip_address=ip_address,
                user_agent=user_agent,
                fingerprint=fingerprint,
                is_verified=True,
            )
            db.session.add(vote)
            db.session.flush()
            vote_id = vote.id
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log_vote_attempt(voter_id, application_id, session_id, False, f"Database error: {e}")
        return jsonify({'error': 'Failed to submit vote'}), 500

    log_vote_attempt(voter_id, application_id, session_id, True, "Vote submitted successfully")

    if not existing_vote:
        # Post-vote analysis flags suspicious votes for review without rejecting them
        is_ok, reason = security_manager.validate_vote_eligibility(
            voter_id or 0, application_id, session_id, ip_address, user_agent
        )
        if not is_ok:
            security_manager.flag_suspicious_vote(vote_id, reason, 'medium')

    update_voting_results(application_id, session_id)

    return jsonify({
        'success': True,
        'message': 'Vote submitted successfully',
        'vote_id': vote_id,
    })


@voting.route('/results/<int:session_id>', methods=['GET'])
def get_results(session_id):
    session = db.session.get(VotingSession, session_id)
    if not session:
        return jsonify({'error': 'Voting session not found'}), 404

    results = VotingResult.query.filter(
        VotingResult.voting_session_id == session_id
    ).join(Application).all()

    return jsonify({
        'session': {
            'id': session.id,
            'title': session.title,
            'status': session.status,
            'total_votes': session.total_votes,
            'total_voters': session.total_voters,
        },
        'results': [{
            'application_id': r.application_id,
            'application_title': r.application.project_title,
            'organization': r.application.organization_name,
            'total_votes': r.total_votes,
            'average_score': round(r.average_score, 2),
            'community_rank': r.community_rank,
            'percentile': r.percentile,
            'engagement_score': r.engagement_score,
            'score_distribution': {
                '1': r.votes_1_star,
                '2': r.votes_2_star,
                '3': r.votes_3_star,
                '4': r.votes_4_star,
                '5': r.votes_5_star,
            },
        } for r in results],
    })


def update_voting_results(application_id, session_id):
    """Recalculate the aggregated VotingResult for one application in a session."""
    votes = CommunityVote.query.filter(
        CommunityVote.application_id == application_id,
        CommunityVote.voting_session_id == session_id,
        CommunityVote.is_verified == True,  # noqa: E712
    ).all()
    if not votes:
        return

    total_votes = len(votes)
    total_score = sum(v.vote_value for v in votes)
    score_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for v in votes:
        if v.vote_value in score_counts:
            score_counts[v.vote_value] += 1
    total_comments = sum(1 for v in votes if v.comments and v.comments.strip())

    result = VotingResult.query.filter_by(
        application_id=application_id, voting_session_id=session_id
    ).first()
    if not result:
        result = VotingResult(application_id=application_id, voting_session_id=session_id)
        db.session.add(result)

    result.total_votes = total_votes
    result.average_score = total_score / total_votes
    result.total_score = total_score
    result.votes_1_star = score_counts[1]
    result.votes_2_star = score_counts[2]
    result.votes_3_star = score_counts[3]
    result.votes_4_star = score_counts[4]
    result.votes_5_star = score_counts[5]
    result.total_comments = total_comments
    result.engagement_score = total_votes + total_comments * 0.5
    result.last_updated = datetime.now(timezone.utc)
    db.session.commit()

    _update_session_rankings(session_id)


def _update_session_rankings(session_id):
    results = VotingResult.query.filter(
        VotingResult.voting_session_id == session_id
    ).order_by(desc(VotingResult.average_score)).all()
    total = len(results)
    for i, result in enumerate(results):
        result.community_rank = i + 1
        result.percentile = (total - i) / total * 100
    db.session.commit()
