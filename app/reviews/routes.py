from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.reviews import bp
from app.models import Application, Grant, User, Review, GrantCriteria, ReviewScore
from app.reviews.forms import ReviewForm, ReviewAssignmentForm, CriteriaScoreForm
from datetime import datetime
from sqlalchemy import func, and_, or_
from decimal import Decimal

@bp.route('/')
@login_required
def list_reviews():
    """List reviews (staff only)"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    grant_id = request.args.get('grant_id', type=int)
    status_filter = request.args.get('status', '')
    reviewer_filter = request.args.get('reviewer', type=int)
    
    # Build base query
    if current_user.is_admin():
        query = Review.query.join(Application).join(Grant)
    else:
        # Non-admin staff only see reviews for their grants
        query = Review.query.join(Application).join(Grant).filter(Grant.created_by == current_user.id)
    
    # Apply filters
    if grant_id:
        query = query.filter(Grant.id == grant_id)
    
    if status_filter:
        query = query.filter(Review.status == status_filter)
    
    if reviewer_filter:
        query = query.filter(Review.reviewer_id == reviewer_filter)
    
    reviews = query.order_by(Review.created_at.desc())\
                  .paginate(page=page, per_page=20, error_out=False)
    
    # Get available grants and reviewers for filters
    if current_user.is_admin():
        grants = Grant.query.filter_by(is_published=True).all()
        reviewers = User.query.filter_by(role='staff').all()
    else:
        grants = Grant.query.filter_by(created_by=current_user.id, is_published=True).all()
        # For non-admin staff, show all staff as potential reviewers
        reviewers = User.query.filter_by(role='staff').all()
    
    return render_template('reviews/list.html',
                         title='Application Reviews',
                         reviews=reviews,
                         grants=grants,
                         reviewers=reviewers,
                         grant_id=grant_id,
                         status_filter=status_filter,
                         reviewer_filter=reviewer_filter)

@bp.route('/pending')
@login_required
def pending_reviews():
    """List pending reviews for current user"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    
    # Get reviews assigned to current user that are pending
    reviews = Review.query.filter_by(
        reviewer_id=current_user.id,
        status='pending'
    ).join(Application).order_by(Application.submitted_at.asc())\
     .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('reviews/pending.html',
                         title='My Pending Reviews',
                         reviews=reviews)

@bp.route('/application/<int:application_id>')
@login_required
def review_application(application_id):
    """Review an application"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    application = Application.query.get_or_404(application_id)
    
    # Check permissions for non-admin staff
    if not current_user.is_admin() and application.grant.created_by != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('reviews.list_reviews'))
    
    # Get or create review for current user
    review = Review.query.filter_by(
        application_id=application_id,
        reviewer_id=current_user.id
    ).first()
    
    if not review:
        # Create new review
        review = Review(
            application_id=application_id,
            reviewer_id=current_user.id,
            status='pending'
        )
        db.session.add(review)
        db.session.commit()
    
    # Get grant criteria for scoring
    criteria = application.grant.criteria.order_by(GrantCriteria.order).all()
    
    # Get existing criteria scores
    criteria_scores = {cs.criteria_id: cs for cs in review.criteria_scores.all()}
    
    form = ReviewForm()
    
    if form.validate_on_submit():
        # Update review
        review.overall_score = form.overall_score.data
        review.strengths = form.strengths.data
        review.weaknesses = form.weaknesses.data
        review.recommendation = form.recommendation.data
        review.comments = form.comments.data
        review.status = 'completed'
        review.completed_at = datetime.utcnow()
        
        # Update criteria scores
        for criteria_item in criteria:
            score_field = f'criteria_{criteria_item.id}'
            if hasattr(form, score_field):
                score_value = getattr(form, score_field).data
                
                if criteria_item.id in criteria_scores:
                    # Update existing score
                    criteria_scores[criteria_item.id].score = score_value
                else:
                    # Create new score
                    criteria_score = ReviewCriteria(
                        review_id=review.id,
                        criteria_id=criteria_item.id,
                        score=score_value
                    )
                    db.session.add(criteria_score)
        
        db.session.commit()
        
        # Calculate application's overall score
        _calculate_application_score(application)
        
        flash('Review submitted successfully!', 'success')
        return redirect(url_for('reviews.view_review', id=review.id))
    
    # Pre-populate form if review exists
    if review.status == 'completed':
        form.overall_score.data = review.overall_score
        form.strengths.data = review.strengths
        form.weaknesses.data = review.weaknesses
        form.recommendation.data = review.recommendation
        form.comments.data = review.comments
        
        # Pre-populate criteria scores
        for criteria_item in criteria:
            score_field = f'criteria_{criteria_item.id}'
            if criteria_item.id in criteria_scores and hasattr(form, score_field):
                getattr(form, score_field).data = criteria_scores[criteria_item.id].score
    
    return render_template('reviews/review_application.html',
                         title=f'Review Application - {application.project_title}',
                         application=application,
                         review=review,
                         criteria=criteria,
                         criteria_scores=criteria_scores,
                         form=form)

@bp.route('/<int:id>')
@login_required
def view_review(id):
    """View review details"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    review = Review.query.get_or_404(id)
    
    # Check permissions for non-admin staff
    if not current_user.is_admin() and review.application.grant.created_by != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('reviews.list_reviews'))
    
    # Get criteria scores
    criteria_scores = review.criteria_scores.join(GrantCriteria)\
                           .order_by(GrantCriteria.order).all()
    
    return render_template('reviews/view.html',
                         title=f'Review - {review.application.project_title}',
                         review=review,
                         criteria_scores=criteria_scores)

@bp.route('/assign/<int:application_id>', methods=['GET', 'POST'])
@login_required
def assign_reviewers(application_id):
    """Assign reviewers to an application (admin only)"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('reviews.list_reviews'))
    
    application = Application.query.get_or_404(application_id)
    
    # Get all staff users as potential reviewers
    staff_users = User.query.filter_by(role='staff').all()
    
    # Get currently assigned reviewers
    assigned_reviewers = [r.reviewer_id for r in application.reviews.all()]
    
    form = ReviewAssignmentForm()
    form.reviewers.choices = [(u.id, f"{u.full_name} ({u.email})") for u in staff_users]
    
    if form.validate_on_submit():
        selected_reviewers = form.reviewers.data
        
        # Remove reviewers that are no longer selected
        for review in application.reviews.all():
            if review.reviewer_id not in selected_reviewers:
                if review.status == 'pending':
                    db.session.delete(review)
                else:
                    flash(f'Cannot remove {review.reviewer.full_name} - review already completed.', 'warning')
        
        # Add new reviewers
        for reviewer_id in selected_reviewers:
            if reviewer_id not in assigned_reviewers:
                review = Review(
                    application_id=application_id,
                    reviewer_id=reviewer_id,
                    status='pending'
                )
                db.session.add(review)
        
        db.session.commit()
        flash('Reviewers assigned successfully!', 'success')
        return redirect(url_for('applications.view_application', id=application_id))
    
    # Pre-populate form with current assignments
    form.reviewers.data = assigned_reviewers
    
    return render_template('reviews/assign.html',
                         title=f'Assign Reviewers - {application.project_title}',
                         application=application,
                         form=form,
                         staff_users=staff_users,
                         assigned_reviewers=assigned_reviewers)

@bp.route('/summary/<int:application_id>')
@login_required
def review_summary(application_id):
    """View review summary for an application"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    application = Application.query.get_or_404(application_id)
    
    # Check permissions for non-admin staff
    if not current_user.is_admin() and application.grant.created_by != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('applications.view_application', id=application_id))
    
    # Get all reviews for this application
    reviews = application.reviews.filter_by(status='completed').all()
    
    if not reviews:
        flash('No completed reviews found for this application.', 'info')
        return redirect(url_for('applications.view_application', id=application_id))
    
    # Calculate summary statistics
    overall_scores = [r.overall_score for r in reviews if r.overall_score]
    avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
    
    # Get criteria breakdown
    criteria_breakdown = {}
    for criteria in application.grant.criteria.all():
        scores = []
        for review in reviews:
            criteria_score = review.criteria_scores.filter_by(criteria_id=criteria.id).first()
            if criteria_score:
                scores.append(criteria_score.score)
        
        if scores:
            criteria_breakdown[criteria.name] = {
                'scores': scores,
                'average': sum(scores) / len(scores),
                'weight': criteria.weight,
                'max_score': criteria.max_score
            }
    
    # Count recommendations
    recommendations = {}
    for review in reviews:
        rec = review.recommendation
        recommendations[rec] = recommendations.get(rec, 0) + 1
    
    return render_template('reviews/summary.html',
                         title=f'Review Summary - {application.project_title}',
                         application=application,
                         reviews=reviews,
                         avg_score=avg_score,
                         criteria_breakdown=criteria_breakdown,
                         recommendations=recommendations)

@bp.route('/bulk-assign', methods=['GET', 'POST'])
@login_required
def bulk_assign_reviewers():
    """Bulk assign reviewers to multiple applications (admin only)"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('reviews.list_reviews'))
    
    grant_id = request.args.get('grant_id', type=int)
    
    if request.method == 'POST':
        application_ids = request.form.getlist('applications')
        reviewer_ids = request.form.getlist('reviewers')
        
        if not application_ids or not reviewer_ids:
            flash('Please select both applications and reviewers.', 'error')
            return redirect(request.url)
        
        assigned_count = 0
        for app_id in application_ids:
            application = Application.query.get(app_id)
            if application:
                for reviewer_id in reviewer_ids:
                    # Check if review already exists
                    existing = Review.query.filter_by(
                        application_id=app_id,
                        reviewer_id=reviewer_id
                    ).first()
                    
                    if not existing:
                        review = Review(
                            application_id=app_id,
                            reviewer_id=reviewer_id,
                            status='pending'
                        )
                        db.session.add(review)
                        assigned_count += 1
        
        db.session.commit()
        flash(f'Successfully assigned {assigned_count} reviews.', 'success')
        return redirect(url_for('reviews.list_reviews'))
    
    # Get applications for bulk assignment
    query = Application.query.filter_by(status='submitted')
    if grant_id:
        query = query.filter_by(grant_id=grant_id)
    
    applications = query.order_by(Application.submitted_at.asc()).all()
    
    # Get staff users
    staff_users = User.query.filter_by(role='staff').all()
    
    # Get grants for filter
    grants = Grant.query.filter_by(is_published=True).all()
    
    return render_template('reviews/bulk_assign.html',
                         title='Bulk Assign Reviewers',
                         applications=applications,
                         staff_users=staff_users,
                         grants=grants,
                         grant_id=grant_id)

# Helper functions
def _calculate_application_score(application):
    """Calculate weighted average score for an application"""
    completed_reviews = application.reviews.filter_by(status='completed').all()
    
    if not completed_reviews:
        application.calculated_score = None
        db.session.commit()
        return
    
    # Calculate weighted average based on criteria
    total_weighted_score = Decimal('0')
    total_weight = Decimal('0')
    
    for criteria in application.grant.criteria.all():
        criteria_scores = []
        for review in completed_reviews:
            criteria_score = review.criteria_scores.filter_by(criteria_id=criteria.id).first()
            if criteria_score:
                criteria_scores.append(criteria_score.score)
        
        if criteria_scores:
            avg_criteria_score = sum(criteria_scores) / len(criteria_scores)
            weighted_score = Decimal(str(avg_criteria_score)) * Decimal(str(criteria.weight))
            total_weighted_score += weighted_score
            total_weight += Decimal(str(criteria.weight))
    
    if total_weight > 0:
        application.calculated_score = float(total_weighted_score / total_weight)
    else:
        # Fallback to simple average of overall scores
        overall_scores = [r.overall_score for r in completed_reviews if r.overall_score]
        if overall_scores:
            application.calculated_score = sum(overall_scores) / len(overall_scores)
    
    db.session.commit()

# API Routes
@bp.route('/api/reviews/<int:application_id>')
@login_required
def api_get_reviews(application_id):
    """API endpoint for application reviews"""
    if not current_user.is_staff():
        return jsonify({'error': 'Access denied'}), 403
    
    application = Application.query.get_or_404(application_id)
    
    # Check permissions for non-admin staff
    if not current_user.is_admin() and application.grant.created_by != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    reviews = application.reviews.all()
    
    return jsonify({
        'reviews': [{
            'id': review.id,
            'reviewer': {
                'id': review.reviewer.id,
                'name': review.reviewer.full_name
            },
            'overall_score': float(review.overall_score) if review.overall_score else None,
            'recommendation': review.recommendation,
            'status': review.status,
            'completed_at': review.completed_at.isoformat() if review.completed_at else None
        } for review in reviews]
    })

@bp.route('/api/reviews/<int:id>/criteria')
@login_required
def api_get_review_criteria(id):
    """API endpoint for review criteria scores"""
    if not current_user.is_staff():
        return jsonify({'error': 'Access denied'}), 403
    
    review = Review.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and review.application.grant.created_by != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    criteria_scores = review.criteria_scores.join(GrantCriteria)\
                           .order_by(GrantCriteria.order).all()
    
    return jsonify({
        'criteria_scores': [{
            'criteria_name': cs.criteria.name,
            'score': float(cs.score),
            'max_score': cs.criteria.max_score,
            'weight': cs.criteria.weight
        } for cs in criteria_scores]
    })
