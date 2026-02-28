from flask import render_template, jsonify, request, current_app
from app.public import public
from app.models import Grant, Application, CommunityVote, VotingSession, User, Review
from app import db
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
import json

@public.route('/transparency')
def transparency_dashboard():
    """Public transparency dashboard showing all grants and community engagement"""
    
    # Get grant statistics
    total_grants = Grant.query.filter_by(is_published=True).count()
    active_grants = Grant.query.filter(
        Grant.is_published == True,
        Grant.status == 'open'
    ).count()
    
    # Get application statistics
    total_applications = Application.query.join(Grant).filter(
        Grant.is_published == True,
        Application.status != 'draft'
    ).count()
    
    approved_applications = Application.query.join(Grant).filter(
        Grant.is_published == True,
        Application.status == 'approved'
    ).count()
    
    # Calculate total funding
    total_budget = db.session.query(func.sum(Grant.total_budget)).filter(
        Grant.is_published == True
    ).scalar() or 0
    
    total_requested = db.session.query(func.sum(Application.amount_requested)).join(Grant).filter(
        Grant.is_published == True,
        Application.status != 'draft'
    ).scalar() or 0
    
    total_approved = db.session.query(func.sum(Application.amount_requested)).join(Grant).filter(
        Grant.is_published == True,
        Application.status == 'approved'
    ).scalar() or 0
    
    # Get community voting statistics
    total_votes = CommunityVote.query.join(VotingSession).join(Grant).filter(
        Grant.is_published == True
    ).count()
    
    active_voting_sessions = VotingSession.query.join(Grant).filter(
        Grant.is_published == True,
        VotingSession.is_active == True,
        VotingSession.starts_at <= datetime.utcnow(),
        VotingSession.ends_at >= datetime.utcnow()
    ).count()
    
    # Get recent grants (last 30 days)
    recent_grants = Grant.query.filter(
        Grant.is_published == True,
        Grant.created_at >= datetime.utcnow() - timedelta(days=30)
    ).order_by(desc(Grant.created_at)).limit(10).all()
    
    # Get grant categories with counts
    category_stats = db.session.query(
        Grant.category,
        func.count(Grant.id).label('count'),
        func.sum(Grant.total_budget).label('total_budget')
    ).filter(Grant.is_published == True).group_by(Grant.category).all()
    
    # Get monthly application trends (last 12 months)
    monthly_trends = []
    for i in range(12):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_applications = Application.query.join(Grant).filter(
            Grant.is_published == True,
            Application.submitted_at >= month_start,
            Application.submitted_at <= month_end
        ).count()
        
        monthly_trends.append({
            'month': month_start.strftime('%b %Y'),
            'applications': month_applications
        })
    
    monthly_trends.reverse()
    
    # Get success stories (approved applications with high scores)
    success_stories = Application.query.join(Grant).filter(
        Grant.is_published == True,
        Application.status == 'approved',
        Application.total_score.isnot(None)
    ).order_by(desc(Application.total_score)).limit(5).all()
    
    return render_template('public/transparency_dashboard.html',
                         total_grants=total_grants,
                         active_grants=active_grants,
                         total_applications=total_applications,
                         approved_applications=approved_applications,
                         total_budget=total_budget,
                         total_requested=total_requested,
                         total_approved=total_approved,
                         total_votes=total_votes,
                         active_voting_sessions=active_voting_sessions,
                         recent_grants=recent_grants,
                         category_stats=category_stats,
                         monthly_trends=monthly_trends,
                         success_stories=success_stories)

@public.route('/grants')
def public_grants():
    """Public listing of all published grants"""
    
    # Get filter parameters
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # Base query for published grants
    query = Grant.query.filter(Grant.is_published == True)
    
    # Apply filters
    if category:
        query = query.filter(Grant.category == category)
    
    if status:
        if status == 'open':
            query = query.filter(Grant.status == 'open')
        elif status == 'closed':
            query = query.filter(Grant.status == 'closed')
    
    if search:
        query = query.filter(
            db.or_(
                Grant.title.contains(search),
                Grant.description.contains(search)
            )
        )
    
    # Get grants with pagination
    page = request.args.get('page', 1, type=int)
    grants = query.order_by(desc(Grant.created_at)).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Get categories for filter dropdown
    categories = db.session.query(Grant.category).filter(
        Grant.is_published == True
    ).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('public/public_grants.html',
                         grants=grants,
                         categories=categories,
                         current_category=category,
                         current_status=status,
                         current_search=search)

@public.route('/grant/<int:grant_id>')
def public_grant_detail(grant_id):
    """Public detailed view of a specific grant"""
    
    grant = Grant.query.filter(
        Grant.id == grant_id,
        Grant.is_published == True
    ).first_or_404()
    
    # Get application statistics for this grant
    total_applications = grant.applications.filter(
        Application.status != 'draft'
    ).count()
    
    approved_applications = grant.applications.filter(
        Application.status == 'approved'
    ).count()
    
    total_requested = db.session.query(func.sum(Application.amount_requested)).filter(
        Application.grant_id == grant_id,
        Application.status != 'draft'
    ).scalar() or 0
    
    # Get community voting information if enabled
    voting_session = None
    community_stats = None
    if grant.require_community_voting:
        voting_session = VotingSession.query.filter_by(
            grant_id=grant_id,
            is_published=True
        ).first()
        
        if voting_session:
            community_stats = {
                'total_votes': voting_session.total_votes,
                'total_voters': voting_session.total_voters,
                'is_open': voting_session.is_open
            }
    
    # Get assessment criteria
    criteria = grant.criteria.all()
    
    return render_template('public/public_grant_detail.html',
                         grant=grant,
                         total_applications=total_applications,
                         approved_applications=approved_applications,
                         total_requested=total_requested,
                         voting_session=voting_session,
                         community_stats=community_stats,
                         criteria=criteria)

@public.route('/results')
def public_results():
    """Public results page showing grant outcomes and impact"""
    
    # Get completed grants with results
    completed_grants = Grant.query.filter(
        Grant.is_published == True,
        Grant.status == 'closed'
    ).order_by(desc(Grant.closes_at)).limit(20).all()
    
    # Get success metrics
    total_funded = db.session.query(func.sum(Application.amount_requested)).join(Grant).filter(
        Grant.is_published == True,
        Application.status == 'approved'
    ).scalar() or 0
    
    total_projects = Application.query.join(Grant).filter(
        Grant.is_published == True,
        Application.status == 'approved'
    ).count()
    
    # Get impact by category
    impact_by_category = db.session.query(
        Grant.category,
        func.count(Application.id).label('projects'),
        func.sum(Application.amount_requested).label('funding')
    ).join(Application).filter(
        Grant.is_published == True,
        Application.status == 'approved'
    ).group_by(Grant.category).all()
    
    # Get recent success stories
    recent_successes = Application.query.join(Grant).filter(
        Grant.is_published == True,
        Application.status == 'approved',
        Application.decision_date >= datetime.utcnow() - timedelta(days=90)
    ).order_by(desc(Application.decision_date)).limit(10).all()
    
    return render_template('public/public_results.html',
                         completed_grants=completed_grants,
                         total_funded=total_funded,
                         total_projects=total_projects,
                         impact_by_category=impact_by_category,
                         recent_successes=recent_successes)

@public.route('/community-engagement')
def community_engagement():
    """Public community engagement metrics and participation data"""
    
    # Get voting participation statistics
    voting_stats = db.session.query(
        func.count(CommunityVote.id).label('total_votes'),
        func.count(func.distinct(CommunityVote.voter_id)).label('unique_voters'),
        func.count(func.distinct(CommunityVote.application_id)).label('applications_voted')
    ).join(VotingSession).join(Grant).filter(
        Grant.is_published == True
    ).first()
    
    # Get participation by postcode (top 10)
    postcode_participation = db.session.query(
        CommunityVote.voter_postcode,
        func.count(CommunityVote.id).label('votes')
    ).join(VotingSession).join(Grant).filter(
        Grant.is_published == True,
        CommunityVote.voter_postcode.isnot(None)
    ).group_by(CommunityVote.voter_postcode).order_by(
        desc(func.count(CommunityVote.id))
    ).limit(10).all()
    
    # Get engagement trends (last 6 months)
    engagement_trends = []
    for i in range(6):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_votes = CommunityVote.query.join(VotingSession).join(Grant).filter(
            Grant.is_published == True,
            CommunityVote.voted_at >= month_start,
            CommunityVote.voted_at <= month_end
        ).count()
        
        engagement_trends.append({
            'month': month_start.strftime('%b %Y'),
            'votes': month_votes
        })
    
    engagement_trends.reverse()
    
    # Get most engaged applications (by vote count)
    popular_applications = db.session.query(
        Application,
        func.count(CommunityVote.id).label('vote_count'),
        func.avg(CommunityVote.vote_value).label('avg_score')
    ).join(CommunityVote).join(Grant).filter(
        Grant.is_published == True
    ).group_by(Application.id).order_by(
        desc(func.count(CommunityVote.id))
    ).limit(10).all()
    
    return render_template('public/community_engagement.html',
                         voting_stats=voting_stats,
                         postcode_participation=postcode_participation,
                         engagement_trends=engagement_trends,
                         popular_applications=popular_applications)

# API Endpoints for public data access

@public.route('/api/grants')
def api_public_grants():
    """API endpoint for public grant data"""
    
    grants = Grant.query.filter(Grant.is_published == True).all()
    
    grants_data = []
    for grant in grants:
        grants_data.append({
            'id': grant.id,
            'title': grant.title,
            'description': grant.description,
            'category': grant.category,
            'total_budget': float(grant.total_budget),
            'status': grant.status,
            'opens_at': grant.opens_at.isoformat() if grant.opens_at else None,
            'closes_at': grant.closes_at.isoformat() if grant.closes_at else None,
            'application_count': grant.applications.filter(Application.status != 'draft').count(),
            'location': {
                'name': grant.location_name,
                'latitude': grant.latitude,
                'longitude': grant.longitude,
                'address': grant.address,
                'postcode': grant.postcode,
                'state': grant.state
            } if grant.latitude and grant.longitude else None
        })
    
    return jsonify({
        'grants': grants_data,
        'total': len(grants_data),
        'timestamp': datetime.utcnow().isoformat()
    })

@public.route('/api/statistics')
def api_public_statistics():
    """API endpoint for public statistics"""
    
    # Calculate key statistics
    stats = {
        'grants': {
            'total': Grant.query.filter(Grant.is_published == True).count(),
            'active': Grant.query.filter(Grant.is_published == True, Grant.status == 'open').count(),
            'total_budget': float(db.session.query(func.sum(Grant.total_budget)).filter(Grant.is_published == True).scalar() or 0)
        },
        'applications': {
            'total': Application.query.join(Grant).filter(Grant.is_published == True, Application.status != 'draft').count(),
            'approved': Application.query.join(Grant).filter(Grant.is_published == True, Application.status == 'approved').count(),
            'total_requested': float(db.session.query(func.sum(Application.amount_requested)).join(Grant).filter(Grant.is_published == True, Application.status != 'draft').scalar() or 0),
            'total_approved': float(db.session.query(func.sum(Application.amount_requested)).join(Grant).filter(Grant.is_published == True, Application.status == 'approved').scalar() or 0)
        },
        'community': {
            'total_votes': CommunityVote.query.join(VotingSession).join(Grant).filter(Grant.is_published == True).count(),
            'active_voting_sessions': VotingSession.query.join(Grant).filter(Grant.is_published == True, VotingSession.is_active == True).count()
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(stats)

@public.route('/api/engagement-data')
def api_engagement_data():
    """API endpoint for community engagement data"""
    
    # Get monthly engagement data
    monthly_data = []
    for i in range(12):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        votes = CommunityVote.query.join(VotingSession).join(Grant).filter(
            Grant.is_published == True,
            CommunityVote.voted_at >= month_start,
            CommunityVote.voted_at <= month_end
        ).count()
        
        applications = Application.query.join(Grant).filter(
            Grant.is_published == True,
            Application.submitted_at >= month_start,
            Application.submitted_at <= month_end
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%b %Y'),
            'votes': votes,
            'applications': applications
        })
    
    monthly_data.reverse()
    
    return jsonify({
        'monthly_engagement': monthly_data,
        'timestamp': datetime.utcnow().isoformat()
    })
