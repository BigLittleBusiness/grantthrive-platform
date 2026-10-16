"""Community voting API. Voting is advisory and never makes funding decisions."""
from datetime import datetime, timezone

from flask import jsonify, request
from sqlalchemy import case, desc, func

from app import db
from app.common.decorators import get_optional_user
from app.models import Application, CommunityVote, Grant, VotingResult, VotingSession
from app.voting import voting
from app.voting.security import create_vote_fingerprint, log_vote_attempt, security_manager, validate_vote_security

VOTABLE_STATUSES = ("submitted", "under_review", "approved")
VOTER_ROLES = {"community_member", "professional_consultant"}


def _session_to_dict(session):
    grant = session.grant
    applications = Application.query.filter(Application.grant_id == session.grant_id, Application.status.in_(VOTABLE_STATUSES)).all()
    results = {result.application_id: result for result in VotingResult.query.filter_by(voting_session_id=session.id).all()}
    options = []
    for application in applications:
        result = results.get(application.id)
        options.append({
            "id": application.id,
            "title": application.project_title or f"Application #{application.id}",
            "description": application.project_description or "",
            "category": grant.category,
            "estimated_budget": float(application.amount_requested or 0),
            "vote_count": result.total_votes if result else 0,
            "average_score": round(result.average_score, 2) if result else 0.0,
        })
    total_votes = sum(option["vote_count"] for option in options)
    for option in options:
        option["percentage"] = round(option["vote_count"] / total_votes * 100, 1) if total_votes else 0
    return {
        "id": session.id, "title": session.title, "description": session.description or "", "grant_title": grant.title,
        "voting_type": session.voting_type, "min_vote_value": session.min_vote_value, "max_vote_value": session.max_vote_value,
        "allow_comments": session.allow_comments, "require_registration": session.require_registration,
        "starts_at": session.starts_at.isoformat(), "ends_at": session.ends_at.isoformat(), "status": session.status,
        "total_votes": session.total_votes, "unique_voters": session.total_voters, "options": options,
        "advisory_notice": "Community voting is advisory only and does not approve, reject, rank, or allocate grants.",
    }


def _public_session_query():
    return VotingSession.query.join(Grant).filter(VotingSession.is_published.is_(True), Grant.is_published.is_(True))


@voting.route("/sessions", methods=["GET"])
def list_sessions():
    status_filter = request.args.get("status", "open")
    now = datetime.now(timezone.utc)
    query = _public_session_query()
    if status_filter == "open":
        query = query.filter(VotingSession.is_active.is_(True), VotingSession.starts_at <= now, VotingSession.ends_at >= now)
    elif status_filter == "closed":
        query = query.filter(VotingSession.ends_at < now)
    elif status_filter == "scheduled":
        query = query.filter(VotingSession.starts_at > now)
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    per_page = min(max(request.args.get("per_page", 20, type=int) or 20, 1), 50)
    pagination = query.order_by(VotingSession.starts_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"sessions": [_session_to_dict(session) for session in pagination.items], "total": pagination.total, "page": pagination.page, "per_page": pagination.per_page, "total_pages": pagination.pages})


@voting.route("/sessions/<int:session_id>", methods=["GET"])
def get_session(session_id):
    session = _public_session_query().filter(VotingSession.id == session_id).first()
    if not session:
        return jsonify({"error": "Voting session not found"}), 404
    data = _session_to_dict(session)
    user = get_optional_user()
    data["user_votes"] = {}
    if user:
        votes = CommunityVote.query.filter_by(voting_session_id=session_id, voter_id=user.id).all()
        data["user_votes"] = {str(vote.application_id): vote.vote_value for vote in votes}
    return jsonify(data)


@voting.route("/sessions/<int:session_id>/vote", methods=["POST"])
def submit_vote(session_id):
    data = request.get_json(silent=True) or {}
    application_id, vote_value = data.get("application_id"), data.get("vote_value")
    if application_id is None or vote_value is None:
        return jsonify({"error": "Missing required fields"}), 400
    session = _public_session_query().filter(VotingSession.id == session_id).first()
    user = get_optional_user()
    voter_id = user.id if user else None
    if not session or not session.is_open:
        log_vote_attempt(voter_id, application_id, session_id, False, "Session not open")
        return jsonify({"error": "Voting session is not open"}), 400
    if session.require_registration:
        if not user:
            return jsonify({"error": "Sign in with an approved community account to vote in this session."}), 401
        if user.role not in VOTER_ROLES or not user.is_approved or user.council_id != session.council_id:
            return jsonify({"error": "This account is not eligible to vote in this council session."}), 403
    if not isinstance(vote_value, int) or not session.min_vote_value <= vote_value <= session.max_vote_value:
        return jsonify({"error": "Invalid vote value"}), 400
    application = Application.query.join(Grant).filter(Application.id == application_id, Application.grant_id == session.grant_id, Grant.is_published.is_(True), Application.status.in_(VOTABLE_STATUSES)).first()
    if not application:
        return jsonify({"error": "Invalid application"}), 400
    if user:
        eligible, reason = validate_vote_security(user.id, application_id, session_id)
        if not eligible:
            log_vote_attempt(user.id, application_id, session_id, False, reason)
            return jsonify({"error": reason}), 403
    comments = (data.get("comments") or "").strip()
    if comments and not session.allow_comments:
        return jsonify({"error": "Comments are not enabled for this session."}), 400
    ip_address, user_agent = request.remote_addr or "", request.headers.get("User-Agent", "")[:500]
    existing = CommunityVote.query.filter_by(application_id=application_id, voting_session_id=session_id, voter_id=voter_id).first() if user else CommunityVote.query.filter_by(application_id=application_id, voting_session_id=session_id, ip_address=ip_address, voter_id=None).first()
    try:
        fingerprint = create_vote_fingerprint(voter_id or 0, ip_address, user_agent)
        if existing:
            existing.vote_value, existing.comments, existing.updated_at, existing.user_agent, existing.fingerprint = vote_value, comments, datetime.now(timezone.utc), user_agent, fingerprint
            vote_id = existing.id
        else:
            vote = CommunityVote(application_id=application_id, voting_session_id=session_id, voter_id=voter_id, vote_value=vote_value, vote_type=session.voting_type, comments=comments, ip_address=ip_address, user_agent=user_agent, fingerprint=fingerprint, is_verified=bool(user))
            db.session.add(vote)
            db.session.flush()
            vote_id = vote.id
        db.session.commit()
    except Exception:
        db.session.rollback()
        log_vote_attempt(voter_id, application_id, session_id, False, "Database error")
        return jsonify({"error": "Failed to submit vote"}), 500
    log_vote_attempt(voter_id, application_id, session_id, True, "Vote submitted")
    if not existing:
        valid, reason = security_manager.validate_vote_eligibility(voter_id or 0, application_id, session_id, ip_address, user_agent)
        if not valid:
            security_manager.flag_suspicious_vote(vote_id, reason, "medium")
    update_voting_results(application_id, session_id)
    return jsonify({"success": True, "message": "Vote submitted successfully", "vote_id": vote_id})


@voting.route("/results/<int:session_id>", methods=["GET"])
def get_results(session_id):
    session = _public_session_query().filter(VotingSession.id == session_id).first()
    if not session:
        return jsonify({"error": "Voting session not found"}), 404
    results = VotingResult.query.join(Application).filter(VotingResult.voting_session_id == session_id, Application.status.in_(VOTABLE_STATUSES)).order_by(desc(VotingResult.average_score)).limit(200).all()
    return jsonify({"session": {"id": session.id, "title": session.title, "status": session.status, "total_votes": session.total_votes, "total_voters": session.total_voters, "advisory_notice": "Community voting is advisory and non-binding."}, "results": [{"application_id": result.application_id, "application_title": result.application.project_title, "total_votes": result.total_votes, "average_score": round(result.average_score, 2), "community_rank": result.community_rank, "percentile": result.percentile, "engagement_score": result.engagement_score, "score_distribution": {"1": result.votes_1_star, "2": result.votes_2_star, "3": result.votes_3_star, "4": result.votes_4_star, "5": result.votes_5_star}} for result in results]})


def update_voting_results(application_id, session_id):
    aggregate = db.session.query(func.count(CommunityVote.id), func.coalesce(func.sum(CommunityVote.vote_value), 0), func.sum(case((CommunityVote.comments.isnot(None), 1), else_=0))).filter(CommunityVote.application_id == application_id, CommunityVote.voting_session_id == session_id, CommunityVote.is_verified.is_(True)).one()
    total_votes, total_score, total_comments = aggregate
    if not total_votes:
        return
    counts = {value: 0 for value in range(1, 6)}
    counts.update(dict(db.session.query(CommunityVote.vote_value, func.count(CommunityVote.id)).filter_by(application_id=application_id, voting_session_id=session_id, is_verified=True).group_by(CommunityVote.vote_value).all()))
    result = VotingResult.query.filter_by(application_id=application_id, voting_session_id=session_id).first() or VotingResult(application_id=application_id, voting_session_id=session_id)
    if result.id is None:
        db.session.add(result)
    result.total_votes, result.total_score, result.average_score, result.total_comments = total_votes, total_score, total_score / total_votes, total_comments or 0
    result.votes_1_star, result.votes_2_star, result.votes_3_star, result.votes_4_star, result.votes_5_star = (counts[i] for i in range(1, 6))
    result.engagement_score, result.last_updated = total_votes + (total_comments or 0) * 0.5, datetime.now(timezone.utc)
    db.session.flush()
    _update_session_rankings(session_id)
    db.session.commit()


def _update_session_rankings(session_id):
    results = VotingResult.query.filter_by(voting_session_id=session_id).order_by(desc(VotingResult.average_score)).all()
    for index, result in enumerate(results, start=1):
        result.community_rank = index
        result.percentile = (len(results) - index + 1) / len(results) * 100
