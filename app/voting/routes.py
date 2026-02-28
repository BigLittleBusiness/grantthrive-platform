from flask import render_template, request, jsonify, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
from app import db
from app.models import Grant, Application, CommunityVote, VotingSession, VotingResult, User
from app.voting import voting
from app.voting.security import validate_vote_security, security_manager, log_vote_attempt, create_vote_fingerprint
from app.utils import admin_required, staff_required
import json

@voting.route('/public')
def public_voting():
    """Public voting page showing all active voting sessions"""
    # Get all active voting sessions
    active_sessions = VotingSession.query.filter(
        VotingSession.is_published == True,
        VotingSession.is_active == True,
        VotingSession.starts_at <= datetime.utcnow(),
        VotingSession.ends_at >= datetime.utcnow()
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
    session = VotingSession.query.get(session_id)
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
    application = Application.query.get(application_id)
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
            existing_vote.updated_at = datetime.utcnow()
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
    """Admin voting management dashboard"""
    # Get all voting sessions
    sessions = VotingSession.query.order_by(desc(VotingSession.created_at)).all()
    
    # Get voting statistics
    stats = {
        'total_sessions': VotingSession.query.count(),
        'active_sessions': VotingSession.query.filter(VotingSession.is_active == True).count(),
        'total_votes': CommunityVote.query.count(),
        'total_voters': db.session.query(func.count(func.distinct(CommunityVote.voter_id))).scalar()
    }
    
    return render_template('voting/admin_voting.html',
                         sessions=sessions,
                         stats=stats,
                         title='Voting Management')

@voting.route('/admin/session/create', methods=['GET', 'POST'])
@login_required
@staff_required
def create_voting_session():
    """Create new voting session"""
    if request.method == 'POST':
        data = request.form
        
        # Get the grant
        grant = Grant.query.get(data['grant_id'])
        if not grant:
            flash('Invalid grant selected.', 'error')
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
    
    # Get available grants
    grants = Grant.query.filter(Grant.status == 'published').all()
    
    return render_template('voting/create_session.html',
                         grants=grants,
                         title='Create Voting Session')

@voting.route('/admin/session/<int:session_id>')
@login_required
@staff_required
def manage_voting_session(session_id):
    """Manage individual voting session"""
    session = VotingSession.query.get_or_404(session_id)
    
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
    """Toggle voting session active status"""
    session = VotingSession.query.get_or_404(session_id)
    
    session.is_active = not session.is_active
    db.session.commit()
    
    status = 'activated' if session.is_active else 'deactivated'
    flash(f'Voting session {status} successfully!', 'success')
    
    return redirect(url_for('voting.manage_voting_session', session_id=session_id))

@voting.route('/admin/session/<int:session_id>/publish', methods=['POST'])
@login_required
@staff_required
def publish_voting_session(session_id):
    """Publish voting session to make it visible to public"""
    session = VotingSession.query.get_or_404(session_id)
    
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
    result.last_updated = datetime.utcnow()
    
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
    session = VotingSession.query.get(session_id)
    
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
