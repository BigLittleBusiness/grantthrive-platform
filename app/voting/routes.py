from flask import render_template, request, jsonify, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, desc, and_, or_
from app import db
from app.models import Grant, Application, CommunityVote, VotingSession, VotingResult, User
from app.voting import voting
from app.voting.security import validate_vote_security, security_manager, log_vote_attempt, create_vote_fingerprint
from app.utils import admin_required, staff_required
import json


def _assert_voting_scope(user, voting_session):
    """Return a 403 abort if user cannot access this voting session.
    system_admin may access any session; council roles are scoped to their own council.
    """
    if user.role == 'system_admin':
        return
    grant = db.session.get(Grant, voting_session.grant_id)
    if not grant or grant.council_id != user.council_id:
        abort(403)

@voting.route('/public')
def public_voting():
    """Public voting page showing all active voting sessions"""
    # Get all active voting sessions
    active_sessions = VotingSession.query.filter(
        VotingSession.is_published == True,
        VotingSession.is_active == True,
        VotingSession.starts_at <= datetime.now(timezone.utc),
        VotingSession.ends_at >= datetime.now(timezone.utc)
    ).all()
    
    return render_template('voting/public_voting.html', 
                         voting_sessions=active_sessions,
                         title='Community Voting')

@voting.route('/session/<int:session_id>')
def voting_session(session_id):
    """Individual voting session page"""
    session = VotingSession.query.get_or_404(session_id)
    
    # Check if session is open for voting
    if not session.is_open:
        flash('This voting session is not currently open.', 'warning')
        return redirect(url_for('voting.public_voting'))
    
    # Get applications for this voting session
    applications = Application.query.filter(
        Application.grant_id == session.grant_id,
        Application.status == 'submitted'
    ).all()
    
    # Get user's existing votes if logged in
    user_votes = {}
    if current_user.is_authenticated:
        votes = CommunityVote.query.filter(
            CommunityVote.voting_session_id == session_id,
            CommunityVote.voter_id == current_user.id
        ).all()
        user_votes = {vote.application_id: vote for vote in votes}
    
    return render_template('voting/voting_session.html',
                         session=session,
                         applications=applications,
                         user_votes=user_votes,
                         title=f'Vote: {session.title}')

@voting.route('/api/vote', methods=['POST'])
def submit_vote():
    """API endpoint for submitting votes with comprehensive security validation"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['application_id', 'voting_session_id', 'vote_value']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    application_id = data['application_id']
    session_id = data['voting_session_id']
    vote_value = data['vote_value']
    comments = data.get('comments', '')
    
    # Get voting session and validate
    session = db.session.get(VotingSession, session_id)
    if not session or not session.is_open:
        log_vote_attempt(current_user.id if current_user.is_authenticated else None, 
                        application_id, session_id, False, "Session not open")
        return jsonify({'error': 'Voting session is not open'}), 400
    
    # Validate vote value
    if not (session.min_vote_value <= vote_value <= session.max_vote_value):
        log_vote_attempt(current_user.id if current_user.is_authenticated else None, 
                        application_id, session_id, False, "Invalid vote value")
        return jsonify({'error': 'Invalid vote value'}), 400
    
    # Get application and validate
    application = db.session.get(Application, application_id)
    if not application or application.grant_id != session.grant_id:
        log_vote_attempt(current_user.id if current_user.is_authenticated else None, 
                        application_id, session_id, False, "Invalid application")
        return jsonify({'error': 'Invalid application'}), 400
    
    # Security validation for authenticated users
    if current_user.is_authenticated:
        is_eligible, reason = validate_vote_security(current_user.id, application_id, session_id)
        if not is_eligible:
            log_vote_attempt(current_user.id, application_id, session_id, False, reason)
            return jsonify({'error': reason}), 403
    
    # Check for existing vote
    existing_vote = None
    voter_id = None
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
    user_agent = request.environ.get('HTTP_USER_AGENT', '')
    
    if current_user.is_authenticated:
        voter_id = current_user.id
        existing_vote = CommunityVote.query.filter(
            CommunityVote.application_id == application_id,
            CommunityVote.voting_session_id == session_id,
            CommunityVote.voter_id == voter_id
        ).first()
    else:
        # For anonymous voting, check by IP and email if provided
        voter_email = data.get('voter_email')
        if voter_email:
            existing_vote = CommunityVote.query.filter(
                CommunityVote.application_id == application_id,
                CommunityVote.voting_session_id == session_id,
                CommunityVote.voter_email == voter_email
            ).first()
        else:
            # Check by IP address (allow one vote per IP per application)
            existing_vote = CommunityVote.query.filter(
                CommunityVote.application_id == application_id,
                CommunityVote.voting_session_id == session_id,
                CommunityVote.ip_address == ip_address,
                CommunityVote.voter_id.is_(None)
            ).first()
    
    try:
        # Create vote fingerprint for tracking
        fingerprint = create_vote_fingerprint(
            voter_id or 0, ip_address, user_agent
        )
        
        if existing_vote:
            # Update existing vote
            existing_vote.vote_value = vote_value
            existing_vote.comments = comments
            existing_vote.updated_at = datetime.now(timezone.utc)
            existing_vote.user_agent = user_agent
            existing_vote.fingerprint = fingerprint
            vote_id = existing_vote.id
        else:
            # Create new vote
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
                is_verified=True  # Will be validated by security system
            )
            db.session.add(vote)
            db.session.flush()  # Get the ID
            vote_id = vote.id
        
        db.session.commit()
        
        # Log successful vote
        log_vote_attempt(voter_id, application_id, session_id, True, "Vote submitted successfully")
        
        # Run post-vote security analysis
        if not existing_vote:  # Only for new votes
            security_analysis = security_manager.validate_vote_eligibility(
                voter_id or 0, application_id, session_id, ip_address, user_agent
            )
            
            if not security_analysis[0]:
                # Flag the vote for review but don't reject it
                security_manager.flag_suspicious_vote(vote_id, security_analysis[1], 'medium')
        
        # Update voting results
        update_voting_results(application_id, session_id)
        
        return jsonify({
            'success': True,
            'message': 'Vote submitted successfully',
            'vote_id': vote_id
        })
        
    except Exception as e:
        db.session.rollback()
        log_vote_attempt(voter_id, application_id, session_id, False, f"Database error: {str(e)}")
        return jsonify({'error': 'Failed to submit vote'}), 500

@voting.route('/api/results/<int:session_id>')
def get_voting_results(session_id):
    """API endpoint for getting voting results"""
    session = VotingSession.query.get_or_404(session_id)
    
    # Get aggregated results
    results = VotingResult.query.filter(
        VotingResult.voting_session_id == session_id
    ).join(Application).all()
    
    results_data = []
    for result in results:
        results_data.append({
            'application_id': result.application_id,
            'application_title': result.application.project_title,
            'organization': result.application.organization_name,
            'total_votes': result.total_votes,
            'average_score': round(result.average_score, 2),
            'community_rank': result.community_rank,
            'percentile': result.percentile,
            'engagement_score': result.engagement_score,
            'score_distribution': {
                '1': result.votes_1_star,
                '2': result.votes_2_star,
                '3': result.votes_3_star,
                '4': result.votes_4_star,
                '5': result.votes_5_star
            }
        })
    
    return jsonify({
        'session': {
            'id': session.id,
            'title': session.title,
            'status': session.status,
            'total_votes': session.total_votes,
            'total_voters': session.total_voters
        },
        'results': results_data
    })

@voting.route('/admin')
@login_required
@staff_required
def admin_voting():
    """Admin voting management dashboard — scoped to user's council."""
    if current_user.role == 'system_admin':
        sessions = VotingSession.query.order_by(desc(VotingSession.created_at)).all()
        base_q = VotingSession.query
    else:
        sessions = VotingSession.query.join(Grant).filter(
            Grant.council_id == current_user.council_id
        ).order_by(desc(VotingSession.created_at)).all()
        base_q = VotingSession.query.join(Grant).filter(
            Grant.council_id == current_user.council_id
        )

    stats = {
        'total_sessions':  base_q.count(),
        'active_sessions': base_q.filter(VotingSession.is_active == True).count(),
        'total_votes':     CommunityVote.query.join(VotingSession).join(Grant).filter(
            Grant.council_id == current_user.council_id
        ).count() if current_user.role != 'system_admin' else CommunityVote.query.count(),
        'total_voters':    db.session.query(func.count(func.distinct(CommunityVote.voter_id))).scalar()
    }
    
    return render_template('voting/admin_voting.html',
                         sessions=sessions,
                         stats=stats,
                         title='Voting Management')

@voting.route('/admin/session/create', methods=['GET', 'POST'])
@login_required
@staff_required
def create_voting_session():
    """Create new voting session — grant must belong to user's council."""
    if request.method == 'POST':
        data = request.form
        
        # Get the grant
        grant = db.session.get(Grant, data['grant_id'])
        if not grant:
            flash('Invalid grant selected.', 'error')
            return redirect(url_for('voting.create_voting_session'))
        # Enforce council scope
        if current_user.role != 'system_admin' and grant.council_id != current_user.council_id:
            flash('Access denied — you cannot create a voting session for another council\'s grant.', 'error')
            return redirect(url_for('voting.create_voting_session'))
        
        try:
            # Create voting session
            session = VotingSession(
                grant_id=data['grant_id'],
                title=data['title'],
                description=data['description'],
                voting_type=data['voting_type'],
                min_vote_value=int(data['min_vote_value']),
                max_vote_value=int(data['max_vote_value']),
                allow_comments=bool(data.get('allow_comments')),
                require_registration=bool(data.get('require_registration')),
                starts_at=datetime.strptime(data['starts_at'], '%Y-%m-%dT%H:%M'),
                ends_at=datetime.strptime(data['ends_at'], '%Y-%m-%dT%H:%M'),
                voting_weight=float(data.get('voting_weight', 0.2)),
                created_by=current_user.id
            )
            
            db.session.add(session)
            db.session.commit()
            
            flash('Voting session created successfully!', 'success')
            return redirect(url_for('voting.admin_voting'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error creating voting session.', 'error')
    
    # Get available grants — scoped to this council
    grants_query = Grant.query.filter(Grant.status == 'published')
    if current_user.role != 'system_admin':
        grants_query = grants_query.filter(Grant.council_id == current_user.council_id)
    grants = grants_query.all()
    
    return render_template('voting/create_session.html',
                         grants=grants,
                         title='Create Voting Session')

@voting.route('/admin/session/<int:session_id>')
@login_required
@staff_required
def manage_voting_session(session_id):
    """Manage individual voting session — council-scoped."""
    session = VotingSession.query.get_or_404(session_id)
    _assert_voting_scope(current_user, session)
    
    # Get voting analytics
    analytics = get_session_analytics(session_id)
    
    return render_template('voting/manage_session.html',
                         session=session,
                         analytics=analytics,
                         title=f'Manage: {session.title}')

@voting.route('/admin/session/<int:session_id>/toggle', methods=['POST'])
@login_required
@staff_required
def toggle_voting_session(session_id):
    """Toggle voting session active status — council-scoped."""
    session = VotingSession.query.get_or_404(session_id)
    _assert_voting_scope(current_user, session)
    
    session.is_active = not session.is_active
    db.session.commit()

    status = 'activated' if session.is_active else 'deactivated'
    flash(f'Voting session {status} successfully!', 'success')

    # ── Notifications: alert opted-in community members when voting opens ──
    if session.is_active:
        try:
            from app.common.notifications import notify
            from app.common import email_service
            grant = db.session.get(Grant, session.grant_id)
            council_id = grant.council_id if grant else None
            if council_id:
                members = User.query.filter_by(
                    council_id=council_id,
                    role='community_member',
                    is_active=True,
                ).filter(User.email_opt_in.is_(True)).all()
                for member in members:
                    notify(
                        user_id=member.id,
                        ntype='voting_opened',
                        title=f'Voting is now open: {session.title}',
                        message=f'A new community voting session "{session.title}" is now open. Cast your vote today!',
                        link='portal/community/voting',
                        send_email_fn=lambda m=member: email_service.send_voting_opened(
                            m.email, m.first_name, session.title, session.id
                        ),
                    )
        except Exception as _ne:
            import logging as _log
            _log.getLogger(__name__).warning('Voting opened notifications failed: %s', _ne)

    return redirect(url_for('voting.manage_voting_session', session_id=session_id))

@voting.route('/admin/session/<int:session_id>/publish', methods=['POST'])
@login_required
@staff_required
def publish_voting_session(session_id):
    """Publish voting session — council-scoped."""
    session = VotingSession.query.get_or_404(session_id)
    _assert_voting_scope(current_user, session)
    
    session.is_published = True
    db.session.commit()
    
    flash('Voting session published successfully!', 'success')
    return redirect(url_for('voting.manage_voting_session', session_id=session_id))

def update_voting_results(application_id, session_id):
    """Update aggregated voting results for an application"""
    # Get all votes for this application in this session
    votes = CommunityVote.query.filter(
        CommunityVote.application_id == application_id,
        CommunityVote.voting_session_id == session_id,
        CommunityVote.is_verified == True
    ).all()
    
    if not votes:
        return
    
    # Calculate aggregated results
    total_votes = len(votes)
    total_score = sum(vote.vote_value for vote in votes)
    average_score = total_score / total_votes if total_votes > 0 else 0
    
    # Count score distribution
    score_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for vote in votes:
        if vote.vote_value in score_counts:
            score_counts[vote.vote_value] += 1
    
    # Count comments
    total_comments = sum(1 for vote in votes if vote.comments and vote.comments.strip())
    
    # Calculate engagement score (based on votes and comments)
    engagement_score = total_votes + (total_comments * 0.5)
    
    # Get or create voting result record
    result = VotingResult.query.filter(
        VotingResult.application_id == application_id,
        VotingResult.voting_session_id == session_id
    ).first()
    
    if not result:
        result = VotingResult(
            application_id=application_id,
            voting_session_id=session_id
        )
        db.session.add(result)
    
    # Update result data
    result.total_votes = total_votes
    result.average_score = average_score
    result.total_score = total_score
    result.votes_1_star = score_counts[1]
    result.votes_2_star = score_counts[2]
    result.votes_3_star = score_counts[3]
    result.votes_4_star = score_counts[4]
    result.votes_5_star = score_counts[5]
    result.total_comments = total_comments
    result.engagement_score = engagement_score
    result.last_updated = datetime.now(timezone.utc)
    
    db.session.commit()
    
    # Update rankings for all applications in this session
    update_session_rankings(session_id)

def update_session_rankings(session_id):
    """Update community rankings for all applications in a voting session"""
    # Get all results for this session, ordered by average score
    results = VotingResult.query.filter(
        VotingResult.voting_session_id == session_id
    ).order_by(desc(VotingResult.average_score)).all()
    
    total_results = len(results)
    
    for i, result in enumerate(results):
        result.community_rank = i + 1
        result.percentile = ((total_results - i) / total_results) * 100 if total_results > 0 else 0
    
    db.session.commit()

def get_session_analytics(session_id):
    """Get comprehensive analytics for a voting session"""
    session = db.session.get(VotingSession, session_id)
    
    # Basic stats
    total_votes = CommunityVote.query.filter(
        CommunityVote.voting_session_id == session_id
    ).count()
    
    total_voters = db.session.query(
        func.count(func.distinct(CommunityVote.voter_id))
    ).filter(CommunityVote.voting_session_id == session_id).scalar()
    
    # Get applications count
    applications_count = Application.query.filter(
        Application.grant_id == session.grant_id
    ).count()
    
    # Participation rate
    participation_rate = (total_voters / applications_count * 100) if applications_count > 0 else 0
    
    # Vote distribution
    vote_distribution = db.session.query(
        CommunityVote.vote_value,
        func.count(CommunityVote.id)
    ).filter(
        CommunityVote.voting_session_id == session_id
    ).group_by(CommunityVote.vote_value).all()
    
    # Top applications by votes
    top_applications = db.session.query(
        Application.project_title,
        Application.organization_name,
        func.count(CommunityVote.id).label('vote_count'),
        func.avg(CommunityVote.vote_value).label('avg_score')
    ).join(CommunityVote).filter(
        CommunityVote.voting_session_id == session_id
    ).group_by(
        Application.id, Application.project_title, Application.organization_name
    ).order_by(desc('vote_count')).limit(10).all()
    
    return {
        'total_votes': total_votes,
        'total_voters': total_voters,
        'applications_count': applications_count,
        'participation_rate': round(participation_rate, 1),
        'vote_distribution': dict(vote_distribution),
        'top_applications': top_applications
    }


# ---------------------------------------------------------------------------
# JSON API endpoints consumed by the React frontend
# ---------------------------------------------------------------------------

@voting.route('/api/sessions', methods=['GET'])
def api_list_sessions():
    """Return all published voting sessions as JSON.
    Public endpoint — no authentication required.
    Optional query params: status=open|closed|scheduled|all (default: open)
    """
    status_filter = request.args.get('status', 'open')
    now = datetime.now(timezone.utc)

    query = VotingSession.query.filter(VotingSession.is_published == True)

    if status_filter == 'open':
        query = query.filter(
            VotingSession.is_active == True,
            VotingSession.starts_at <= now,
            VotingSession.ends_at >= now,
        )
    elif status_filter == 'closed':
        query = query.filter(VotingSession.ends_at < now)
    elif status_filter == 'scheduled':
        query = query.filter(VotingSession.starts_at > now)
    # 'all' returns every published session

    sessions = query.order_by(VotingSession.starts_at.desc()).all()

    def _session_to_dict(s):
        grant = db.session.get(Grant, s.grant_id)
        # Build list of applications eligible for voting
        apps = Application.query.filter(
            Application.grant_id == s.grant_id,
            Application.status.in_(['submitted', 'under_review', 'approved'])
        ).all()
        options = []
        for app in apps:
            result = VotingResult.query.filter_by(
                application_id=app.id,
                voting_session_id=s.id
            ).first()
            options.append({
                'id': app.id,
                'title': getattr(app, 'project_title', None) or getattr(app, 'title', None) or f'Application #{app.id}',
                'description': getattr(app, 'project_description', None) or getattr(app, 'description', '') or '',
                'category': getattr(app, 'category', None) or (grant.category if grant else ''),
                'estimated_budget': getattr(app, 'amount_requested', None) or 0,
                'vote_count': result.total_votes if result else 0,
                'average_score': round(result.average_score, 2) if result else 0.0,
                'percentage': 0,  # calculated client-side
            })
        # Compute percentages
        total_votes = sum(o['vote_count'] for o in options)
        for o in options:
            o['percentage'] = round((o['vote_count'] / total_votes * 100), 1) if total_votes > 0 else 0

        return {
            'id': s.id,
            'title': s.title,
            'description': s.description or '',
            'grant_title': grant.title if grant else '',
            'voting_type': s.voting_type,
            'min_vote_value': s.min_vote_value,
            'max_vote_value': s.max_vote_value,
            'allow_comments': s.allow_comments,
            'require_registration': s.require_registration,
            'starts_at': s.starts_at.isoformat(),
            'ends_at': s.ends_at.isoformat(),
            'status': s.status,
            'total_votes': s.total_votes,
            'unique_voters': s.total_voters,
            'options': options,
        }

    return jsonify({
        'sessions': [_session_to_dict(s) for s in sessions],
        'total': len(sessions),
    })


@voting.route('/api/sessions/<int:session_id>', methods=['GET'])
def api_get_session(session_id):
    """Return a single voting session with full application options as JSON."""
    s = VotingSession.query.get_or_404(session_id)
    if not s.is_published:
        return jsonify({'error': 'Voting session not found'}), 404

    grant = db.session.get(Grant, s.grant_id)
    apps = Application.query.filter(
        Application.grant_id == s.grant_id,
        Application.status.in_(['submitted', 'under_review', 'approved'])
    ).all()

    options = []
    for app in apps:
        result = VotingResult.query.filter_by(
            application_id=app.id, voting_session_id=s.id
        ).first()
        options.append({
            'id': app.id,
            'title': getattr(app, 'project_title', None) or f'Application #{app.id}',
            'description': getattr(app, 'project_description', '') or '',
            'category': getattr(app, 'category', '') or '',
            'estimated_budget': getattr(app, 'amount_requested', 0) or 0,
            'vote_count': result.total_votes if result else 0,
            'average_score': round(result.average_score, 2) if result else 0.0,
        })

    # User's existing votes (if authenticated)
    user_votes = {}
    if current_user.is_authenticated:
        votes = CommunityVote.query.filter_by(
            voting_session_id=session_id, voter_id=current_user.id
        ).all()
        user_votes = {str(v.application_id): v.vote_value for v in votes}

    return jsonify({
        'id': s.id,
        'title': s.title,
        'description': s.description or '',
        'grant_title': grant.title if grant else '',
        'voting_type': s.voting_type,
        'min_vote_value': s.min_vote_value,
        'max_vote_value': s.max_vote_value,
        'allow_comments': s.allow_comments,
        'require_registration': s.require_registration,
        'starts_at': s.starts_at.isoformat(),
        'ends_at': s.ends_at.isoformat(),
        'status': s.status,
        'total_votes': s.total_votes,
        'unique_voters': s.total_voters,
        'options': options,
        'user_votes': user_votes,
    })


@voting.route('/api/sessions/<int:session_id>/vote', methods=['POST'])
def api_submit_vote(session_id):
    """Submit a vote for an application in a session via the React frontend.
    Delegates to the existing submit_vote security pipeline.
    """
    data = request.get_json() or {}
    data['voting_session_id'] = session_id
    # Re-use the existing submit_vote logic by forwarding to it
    from flask import current_app
    with current_app.test_request_context(
        '/voting/api/vote',
        method='POST',
        json=data,
        headers=dict(request.headers),
    ):
        return submit_vote()
