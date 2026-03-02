from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import User, Grant, Application, Review
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

@bp.route('/')
def index():
    """Homepage"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Get some public statistics
    total_grants = Grant.query.filter_by(is_published=True).count()
    total_applications = Application.query.filter(Application.status != 'draft').count()
    active_grants = Grant.query.filter(
        Grant.is_published == True,
        Grant.status == 'open',
        Grant.opens_at <= datetime.now(timezone.utc),
        Grant.closes_at >= datetime.now(timezone.utc)
    ).count()
    
    return render_template('main/index.html', 
                         title='Welcome',
                         total_grants=total_grants,
                         total_applications=total_applications,
                         active_grants=active_grants)

@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get user-specific statistics
    if current_user.is_staff():
        # Staff dashboard
        recent_grants = Grant.query.filter_by(created_by=current_user.id)\
                                 .order_by(Grant.created_at.desc())\
                                 .limit(5).all()
        
        pending_reviews = Review.query.join(Application)\
                               .filter(Review.reviewer_id == current_user.id,
                                     Review.is_complete == False)\
                               .count()
        
        total_applications = Application.query.join(Grant)\
                                           .filter(Grant.created_by == current_user.id)\
                                           .count()
        
        # Create stats dictionary for template
        stats = {
            'total_grants': Grant.query.filter_by(created_by=current_user.id).count(),
            'active_grants': Grant.query.filter_by(created_by=current_user.id, status='published').count(),
            'total_applications': total_applications,
            'pending_reviews': pending_reviews
        }
        
        return render_template('main/staff_dashboard.html',
                             title='Dashboard',
                             stats=stats,
                             recent_grants=recent_grants,
                             pending_reviews=pending_reviews,
                             my_applications=[])
    else:
        # Community user dashboard
        my_applications = Application.query.filter_by(applicant_id=current_user.id)\
                                        .order_by(Application.created_at.desc())\
                                        .limit(5).all()
        
        available_grants = Grant.query.filter(
            Grant.is_published == True,
            Grant.status == 'open',
            Grant.opens_at <= datetime.now(timezone.utc),
            Grant.closes_at >= datetime.now(timezone.utc)
        ).limit(5).all()
        
        return render_template('main/community_dashboard.html',
                             title='Dashboard',
                             my_applications=my_applications,
                             available_grants=available_grants)

@bp.route('/grants')
def public_grants():
    """Public grants listing"""
    page = request.args.get('page', 1, type=int)
    
    grants = Grant.query.filter(
        Grant.is_published == True,
        Grant.status.in_(['open', 'closed'])
    ).order_by(Grant.created_at.desc())\
     .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('main/public_grants.html',
                         title='Available Grants',
                         grants=grants)

@bp.route('/grant/<int:id>')
def view_grant(id):
    """View individual grant details"""
    grant = Grant.query.get_or_404(id)
    
    # Check if grant is public or user has access
    if not grant.is_published and not (current_user.is_authenticated and current_user.is_staff()):
        return redirect(url_for('main.public_grants'))
    
    # Get application statistics
    total_applications = grant.applications.filter(Application.status != 'draft').count()
    
    # Check if current user has applied
    user_application = None
    if current_user.is_authenticated:
        user_application = grant.applications.filter_by(applicant_id=current_user.id).first()
    
    return render_template('main/view_grant.html',
                         title=grant.title,
                         grant=grant,
                         total_applications=total_applications,
                         user_application=user_application)

@bp.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    stats = {}
    
    if current_user.is_admin():
        # Admin statistics
        stats = {
            'total_users': User.query.count(),
            'total_grants': Grant.query.count(),
            'total_applications': Application.query.count(),
            'pending_reviews': Review.query.filter_by(is_complete=False).count(),
            'active_grants': Grant.query.filter(
                Grant.status == 'open',
                Grant.is_published == True
            ).count()
        }
    elif current_user.is_staff():
        # Staff statistics
        stats = {
            'my_grants': Grant.query.filter_by(created_by=current_user.id).count(),
            'my_applications': Application.query.join(Grant)\
                                            .filter(Grant.created_by == current_user.id)\
                                            .count(),
            'pending_reviews': Review.query.filter_by(
                reviewer_id=current_user.id,
                is_complete=False
            ).count()
        }
    else:
        # Community user statistics
        stats = {
            'my_applications': Application.query.filter_by(applicant_id=current_user.id).count(),
            'available_grants': Grant.query.filter(
                Grant.is_published == True,
                Grant.status == 'open'
            ).count()
        }
    
    return jsonify(stats)

@bp.route('/search')
def search():
    """Search grants and applications"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    
    if not query:
        return redirect(url_for('main.public_grants'))
    
    # Search grants
    grants_query = Grant.query.filter(Grant.is_published == True)
    
    if query:
        grants_query = grants_query.filter(
            Grant.title.contains(query) | 
            Grant.description.contains(query)
        )
    
    if category:
        grants_query = grants_query.filter(Grant.category == category)
    
    if status:
        grants_query = grants_query.filter(Grant.status == status)
    
    grants = grants_query.order_by(Grant.created_at.desc()).all()
    
    return render_template('main/search_results.html',
                         title=f'Search Results for "{query}"',
                         grants=grants,
                         query=query,
                         category=category,
                         status=status)
