from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.workflows import bp
from app.models import Application, Grant, User, Review, WorkflowStep
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func

@bp.route('/')
@login_required
def list_workflows():
    """List workflow configurations (admin only)"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    # Get grants scoped to this council (system_admin sees all)
    if current_user.role == 'system_admin':
        grants = Grant.query.filter_by(is_published=True).all()
    else:
        grants = Grant.query.filter_by(
            is_published=True, council_id=current_user.council_id
        ).all()
    
    return render_template('workflows/list.html',
                         title='Workflow Management',
                         grants=grants)

@bp.route('/pending')
@login_required
def pending_approvals():
    """List applications pending approval"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    grant_id = request.args.get('grant_id', type=int)
    priority_filter = request.args.get('priority', '')
    
    # Build query scoped to this council
    if current_user.role == 'system_admin':
        query = Application.query.filter(
            Application.status.in_(['under_review', 'reviewed'])
        )
    elif current_user.is_admin():
        # council_admin sees all applications for their council
        query = Application.query.join(Grant).filter(
            Grant.council_id == current_user.council_id,
            Application.status.in_(['under_review', 'reviewed'])
        )
    else:
        # council_staff only see applications for grants they created, within their council
        query = Application.query.join(Grant).filter(
            Grant.council_id == current_user.council_id,
            Grant.created_by == current_user.id,
            Application.status.in_(['under_review', 'reviewed'])
        )
    
    # Apply filters
    if grant_id:
        query = query.filter(Application.grant_id == grant_id)
    
    # Priority filtering based on review completion and scores
    if priority_filter == 'high':
        # High priority: all reviews completed, high scores
        query = query.filter(Application.calculated_score >= 80)
    elif priority_filter == 'medium':
        # Medium priority: all reviews completed, medium scores
        query = query.filter(
            and_(Application.calculated_score >= 60, Application.calculated_score < 80)
        )
    elif priority_filter == 'low':
        # Low priority: low scores or incomplete reviews
        query = query.filter(
            or_(Application.calculated_score < 60, Application.calculated_score.is_(None))
        )
    
    applications = query.order_by(Application.submitted_at.asc())\
                       .paginate(page=page, per_page=20, error_out=False)
    
    # Get available grants for filter — scoped to council
    if current_user.role == 'system_admin':
        grants = Grant.query.filter_by(is_published=True).all()
    elif current_user.is_admin():
        grants = Grant.query.filter_by(
            is_published=True, council_id=current_user.council_id
        ).all()
    else:
        grants = Grant.query.filter_by(
            created_by=current_user.id, is_published=True, council_id=current_user.council_id
        ).all()
    
    return render_template('workflows/pending.html',
                         title='Pending Approvals',
                         applications=applications,
                         grants=grants,
                         grant_id=grant_id,
                         priority_filter=priority_filter)

@bp.route('/approve/<int:application_id>', methods=['GET', 'POST'])
@login_required
def approve_application(application_id):
    """Make approval decision for an application"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    application = Application.query.get_or_404(application_id)
    grant = db.session.get(Grant, application.grant_id)

    # Enforce council scope — council users cannot touch another council's applications
    if current_user.role != 'system_admin':
        if not grant or grant.council_id != current_user.council_id:
            flash('Access denied.', 'error')
            return redirect(url_for('workflows.pending_approvals'))

    # council_staff can only approve applications for grants they created
    if not current_user.is_admin() and current_user.role != 'system_admin':
        if grant.created_by != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('workflows.pending_approvals'))
    
    # Check if application is ready for approval decision
    if application.status not in ['under_review', 'reviewed']:
        flash('This application is not ready for approval decision.', 'error')
        return redirect(url_for('applications.view_application', id=application_id))
    
    if request.method == 'POST':
        decision = request.form.get('decision')
        notes = request.form.get('notes', '')
        amount_approved = request.form.get('amount_approved', type=float)
        
        # Update application status
        if decision == 'approve':
            application.status = 'approved'
            application.approved_at = datetime.now(timezone.utc)
            application.approved_by = current_user.id
            application.amount_approved = amount_approved or application.amount_requested
        elif decision == 'reject':
            application.status = 'rejected'
            application.rejected_at = datetime.now(timezone.utc)
            application.rejected_by = current_user.id
        elif decision == 'return':
            application.status = 'returned'
            application.updated_at = datetime.now(timezone.utc)
        
        # Add staff notes
        if notes:
            application.staff_notes = notes
        
        db.session.commit()
        
        flash(f'Application {decision}d successfully!', 'success')
        return redirect(url_for('workflows.pending_approvals'))
    
    # Get completed reviews
    completed_reviews = application.reviews.filter_by(status='completed').all()
    
    return render_template('workflows/approve.html',
                         title=f'Approval Decision - {application.project_title}',
                         application=application,
                         completed_reviews=completed_reviews)
