from flask import render_template, redirect, url_for, flash, request, jsonify, make_response, current_app
from flask_login import login_required, current_user
from app import db
from app.reports import bp
from app.models import Application, Grant, User, Review
from app.reports.forms import ReportFilterForm, CustomReportForm, ExportForm
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, extract, case
from decimal import Decimal
import json
import csv
import io

@bp.route('/')
@login_required
def dashboard():
    """Main reporting dashboard"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    # Get date range for filtering (default: last 12 months)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    
    # Build base query based on user permissions
    if current_user.is_admin():
        applications_query = Application.query
        grants_query = Grant.query
    else:
        # Non-admin staff only see their grants
        applications_query = Application.query.join(Grant).filter(Grant.created_by == current_user.id)
        grants_query = Grant.query.filter_by(created_by=current_user.id)
    
    # Key metrics
    total_applications = applications_query.count()
    total_grants = grants_query.filter_by(is_published=True).count()
    
    # Application status breakdown
    status_counts = db.session.query(
        Application.status,
        func.count(Application.id).label('count')
    ).filter(
        Application.submitted_at >= start_date,
        Application.submitted_at <= end_date
    )
    
    if not current_user.is_admin():
        status_counts = status_counts.join(Grant).filter(Grant.created_by == current_user.id)
    
    status_counts = status_counts.group_by(Application.status).all()
    
    # Financial summary
    financial_summary = db.session.query(
        func.sum(Application.amount_requested).label('total_requested'),
        func.count(case([(Application.status == 'approved', 1)])).label('approved_count'),
        func.count(case([(Application.status == 'rejected', 1)])).label('rejected_count')
    ).filter(
        Application.submitted_at >= start_date,
        Application.submitted_at <= end_date
    )
    
    if not current_user.is_admin():
        financial_summary = financial_summary.join(Grant).filter(Grant.created_by == current_user.id)
    
    financial_summary = financial_summary.first()
    
    # Monthly trends (last 12 months)
    monthly_trends = db.session.query(
        extract('year', Application.submitted_at).label('year'),
        extract('month', Application.submitted_at).label('month'),
        func.count(Application.id).label('applications'),
        func.sum(Application.amount_requested).label('amount_requested'),
        func.sum(Application.amount_approved).label('amount_approved')
    ).filter(
        Application.submitted_at >= start_date,
        Application.submitted_at <= end_date
    )
    
    if not current_user.is_admin():
        monthly_trends = monthly_trends.join(Grant).filter(Grant.created_by == current_user.id)
    
    monthly_trends = monthly_trends.group_by(
        extract('year', Application.submitted_at),
        extract('month', Application.submitted_at)
    ).order_by(
        extract('year', Application.submitted_at),
        extract('month', Application.submitted_at)
    ).all()
    
    # Top performing grants
    top_grants = db.session.query(
        Grant.id,
        Grant.title,
        func.count(Application.id).label('application_count'),
        func.sum(Application.amount_requested).label('total_requested'),
        func.sum(Application.amount_approved).label('total_approved'),
        func.avg(Application.calculated_score).label('avg_score')
    ).join(Application).filter(
        Application.submitted_at >= start_date,
        Application.submitted_at <= end_date
    )
    
    if not current_user.is_admin():
        top_grants = top_grants.filter(Grant.created_by == current_user.id)
    
    top_grants = top_grants.group_by(Grant.id, Grant.title)\
                          .order_by(func.count(Application.id).desc())\
                          .limit(10).all()
    
    # Review performance
    review_stats = db.session.query(
        func.count(Review.id).label('total_reviews'),
        func.count(case([(Review.status == 'completed', 1)])).label('completed_reviews'),
        func.avg(Review.overall_score).label('avg_score'),
        func.avg(
            func.extract('epoch', Review.completed_at - Review.created_at) / 86400
        ).label('avg_days_to_complete')
    ).filter(
        Review.created_at >= start_date,
        Review.created_at <= end_date
    )
    
    if not current_user.is_admin():
        review_stats = review_stats.join(Application).join(Grant)\
                                  .filter(Grant.created_by == current_user.id)
    
    review_stats = review_stats.first()
    
    return render_template('reports/dashboard.html',
                         title='Analytics Dashboard',
                         total_applications=total_applications,
                         total_grants=total_grants,
                         status_counts=status_counts,
                         financial_summary=financial_summary,
                         monthly_trends=monthly_trends,
                         top_grants=top_grants,
                         review_stats=review_stats,
                         start_date=start_date,
                         end_date=end_date)

@bp.route('/grant-performance')
@login_required
def grant_performance():
    """Grant program performance report"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    grant_id = request.args.get('grant_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Date range defaults
    if not date_from:
        date_from = (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Build query
    if current_user.is_admin():
        grants_query = Grant.query.filter_by(is_published=True)
    else:
        grants_query = Grant.query.filter_by(created_by=current_user.id, is_published=True)
    
    if grant_id:
        grants_query = grants_query.filter_by(id=grant_id)
    
    # Get grant performance data
    grant_performance = db.session.query(
        Grant.id,
        Grant.title,
        Grant.budget_total,
        Grant.opens_at,
        Grant.closes_at,
        func.count(Application.id).label('total_applications'),
        func.count(case([(Application.status == 'approved', 1)])).label('approved_applications'),
        func.count(case([(Application.status == 'rejected', 1)])).label('rejected_applications'),
        func.sum(Application.amount_requested).label('total_requested'),
        func.sum(Application.amount_approved).label('total_approved'),
        func.avg(Application.calculated_score).label('avg_score'),
        func.avg(
            func.extract('epoch', Application.approved_at - Application.submitted_at) / 86400
        ).label('avg_processing_days')
    ).outerjoin(Application).filter(
        Grant.is_published == True
    )
    
    if not current_user.is_admin():
        grant_performance = grant_performance.filter(Grant.created_by == current_user.id)
    
    if date_from:
        grant_performance = grant_performance.filter(
            or_(Application.submitted_at >= datetime.strptime(date_from, '%Y-%m-%d'),
                Application.submitted_at.is_(None))
        )
    
    if date_to:
        grant_performance = grant_performance.filter(
            or_(Application.submitted_at <= datetime.strptime(date_to, '%Y-%m-%d'),
                Application.submitted_at.is_(None))
        )
    
    if grant_id:
        grant_performance = grant_performance.filter(Grant.id == grant_id)
    
    grant_performance = grant_performance.group_by(
        Grant.id, Grant.title, Grant.budget_total, Grant.opens_at, Grant.closes_at
    ).order_by(func.count(Application.id).desc())
    
    grants_paginated = grant_performance.paginate(page=page, per_page=20, error_out=False)
    
    # Get all grants for filter dropdown
    if current_user.is_admin():
        all_grants = Grant.query.filter_by(is_published=True).all()
    else:
        all_grants = Grant.query.filter_by(created_by=current_user.id, is_published=True).all()
    
    return render_template('reports/grant_performance.html',
                         title='Grant Performance Report',
                         grants=grants_paginated,
                         all_grants=all_grants,
                         grant_id=grant_id,
                         date_from=date_from,
                         date_to=date_to)

@bp.route('/application-analytics')
@login_required
def application_analytics():
    """Application statistics and trends"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    # Get filter parameters
    grant_id = request.args.get('grant_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Date range defaults
    if not date_from:
        date_from = (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Build base query
    if current_user.is_admin():
        applications_query = Application.query
    else:
        applications_query = Application.query.join(Grant).filter(Grant.created_by == current_user.id)
    
    # Apply filters
    if grant_id:
        applications_query = applications_query.filter(Application.grant_id == grant_id)
    
    if date_from:
        applications_query = applications_query.filter(
            Application.submitted_at >= datetime.strptime(date_from, '%Y-%m-%d')
        )
    
    if date_to:
        applications_query = applications_query.filter(
            Application.submitted_at <= datetime.strptime(date_to, '%Y-%m-%d')
        )
    
    # Application status distribution
    status_distribution = db.session.query(
        Application.status,
        func.count(Application.id).label('count'),
        func.sum(Application.amount_requested).label('total_amount')
    ).filter(
        Application.submitted_at >= datetime.strptime(date_from, '%Y-%m-%d'),
        Application.submitted_at <= datetime.strptime(date_to, '%Y-%m-%d')
    )
    
    if not current_user.is_admin():
        status_distribution = status_distribution.join(Grant).filter(Grant.created_by == current_user.id)
    
    if grant_id:
        status_distribution = status_distribution.filter(Application.grant_id == grant_id)
    
    status_distribution = status_distribution.group_by(Application.status).all()
    
    # Score distribution
    score_ranges = [
        (0, 20, 'Very Low'),
        (20, 40, 'Low'),
        (40, 60, 'Medium'),
        (60, 80, 'High'),
        (80, 100, 'Very High')
    ]
    
    score_distribution = []
    for min_score, max_score, label in score_ranges:
        count = applications_query.filter(
            Application.calculated_score >= min_score,
            Application.calculated_score < max_score
        ).count()
        score_distribution.append({
            'range': label,
            'min_score': min_score,
            'max_score': max_score,
            'count': count
        })
    
    # Weekly submission trends
    weekly_trends = db.session.query(
        func.date_trunc('week', Application.submitted_at).label('week'),
        func.count(Application.id).label('applications'),
        func.sum(Application.amount_requested).label('amount_requested')
    ).filter(
        Application.submitted_at >= datetime.strptime(date_from, '%Y-%m-%d'),
        Application.submitted_at <= datetime.strptime(date_to, '%Y-%m-%d')
    )
    
    if not current_user.is_admin():
        weekly_trends = weekly_trends.join(Grant).filter(Grant.created_by == current_user.id)
    
    if grant_id:
        weekly_trends = weekly_trends.filter(Application.grant_id == grant_id)
    
    weekly_trends = weekly_trends.group_by(
        func.date_trunc('week', Application.submitted_at)
    ).order_by(
        func.date_trunc('week', Application.submitted_at)
    ).all()
    
    # Top applicant organizations
    top_organizations = db.session.query(
        Application.organization_name,
        func.count(Application.id).label('application_count'),
        func.sum(Application.amount_requested).label('total_requested'),
        func.sum(Application.amount_approved).label('total_approved'),
        func.avg(Application.calculated_score).label('avg_score')
    ).filter(
        Application.submitted_at >= datetime.strptime(date_from, '%Y-%m-%d'),
        Application.submitted_at <= datetime.strptime(date_to, '%Y-%m-%d')
    )
    
    if not current_user.is_admin():
        top_organizations = top_organizations.join(Grant).filter(Grant.created_by == current_user.id)
    
    if grant_id:
        top_organizations = top_organizations.filter(Application.grant_id == grant_id)
    
    top_organizations = top_organizations.group_by(Application.organization_name)\
                                       .order_by(func.count(Application.id).desc())\
                                       .limit(10).all()
    
    # Get all grants for filter
    if current_user.is_admin():
        all_grants = Grant.query.filter_by(is_published=True).all()
    else:
        all_grants = Grant.query.filter_by(created_by=current_user.id, is_published=True).all()
    
    return render_template('reports/application_analytics.html',
                         title='Application Analytics',
                         status_distribution=status_distribution,
                         score_distribution=score_distribution,
                         weekly_trends=weekly_trends,
                         top_organizations=top_organizations,
                         all_grants=all_grants,
                         grant_id=grant_id,
                         date_from=date_from,
                         date_to=date_to)

@bp.route('/financial-report')
@login_required
def financial_report():
    """Financial reporting and budget analysis"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    # Get filter parameters
    grant_id = request.args.get('grant_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Date range defaults
    if not date_from:
        date_from = (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Financial summary by grant
    financial_by_grant = db.session.query(
        Grant.id,
        Grant.title,
        Grant.budget_total,
        func.count(Application.id).label('total_applications'),
        func.sum(Application.amount_requested).label('total_requested'),
        func.sum(case([(Application.status == 'approved', Application.amount_approved)])).label('total_approved'),
        func.sum(case([(Application.status == 'rejected', Application.amount_requested)])).label('total_rejected'),
        func.count(case([(Application.status == 'approved', 1)])).label('approved_count'),
        func.count(case([(Application.status == 'rejected', 1)])).label('rejected_count')
    ).outerjoin(Application).filter(
        Grant.is_published == True
    )
    
    if not current_user.is_admin():
        financial_by_grant = financial_by_grant.filter(Grant.created_by == current_user.id)
    
    if date_from:
        financial_by_grant = financial_by_grant.filter(
            or_(Application.submitted_at >= datetime.strptime(date_from, '%Y-%m-%d'),
                Application.submitted_at.is_(None))
        )
    
    if date_to:
        financial_by_grant = financial_by_grant.filter(
            or_(Application.submitted_at <= datetime.strptime(date_to, '%Y-%m-%d'),
                Application.submitted_at.is_(None))
        )
    
    if grant_id:
        financial_by_grant = financial_by_grant.filter(Grant.id == grant_id)
    
    financial_by_grant = financial_by_grant.group_by(
        Grant.id, Grant.title, Grant.budget_total
    ).order_by(Grant.title).all()
    
    # Monthly financial trends
    monthly_financial = db.session.query(
        extract('year', Application.submitted_at).label('year'),
        extract('month', Application.submitted_at).label('month'),
        func.sum(Application.amount_requested).label('requested'),
        func.sum(case([(Application.status == 'approved', Application.amount_approved)])).label('approved'),
        func.count(Application.id).label('applications')
    ).filter(
        Application.submitted_at >= datetime.strptime(date_from, '%Y-%m-%d'),
        Application.submitted_at <= datetime.strptime(date_to, '%Y-%m-%d')
    )
    
    if not current_user.is_admin():
        monthly_financial = monthly_financial.join(Grant).filter(Grant.created_by == current_user.id)
    
    if grant_id:
        monthly_financial = monthly_financial.filter(Application.grant_id == grant_id)
    
    monthly_financial = monthly_financial.group_by(
        extract('year', Application.submitted_at),
        extract('month', Application.submitted_at)
    ).order_by(
        extract('year', Application.submitted_at),
        extract('month', Application.submitted_at)
    ).all()
    
    # Budget utilization
    budget_utilization = []
    for grant_data in financial_by_grant:
        if grant_data.budget_total and grant_data.total_approved:
            utilization_rate = (float(grant_data.total_approved) / float(grant_data.budget_total)) * 100
        else:
            utilization_rate = 0
        
        budget_utilization.append({
            'grant_id': grant_data.id,
            'grant_title': grant_data.title,
            'budget_total': grant_data.budget_total,
            'total_approved': grant_data.total_approved,
            'utilization_rate': utilization_rate,
            'remaining_budget': float(grant_data.budget_total or 0) - float(grant_data.total_approved or 0)
        })
    
    # Get all grants for filter
    if current_user.is_admin():
        all_grants = Grant.query.filter_by(is_published=True).all()
    else:
        all_grants = Grant.query.filter_by(created_by=current_user.id, is_published=True).all()
    
    return render_template('reports/financial_report.html',
                         title='Financial Report',
                         financial_by_grant=financial_by_grant,
                         monthly_financial=monthly_financial,
                         budget_utilization=budget_utilization,
                         all_grants=all_grants,
                         grant_id=grant_id,
                         date_from=date_from,
                         date_to=date_to)

@bp.route('/reviewer-performance')
@login_required
def reviewer_performance():
    """Reviewer performance analytics"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    # Get filter parameters
    reviewer_id = request.args.get('reviewer_id', type=int)
    grant_id = request.args.get('grant_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Date range defaults
    if not date_from:
        date_from = (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Reviewer performance summary
    reviewer_stats = db.session.query(
        User.id,
        User.full_name,
        User.email,
        func.count(Review.id).label('total_reviews'),
        func.count(case([(Review.status == 'completed', 1)])).label('completed_reviews'),
        func.avg(Review.overall_score).label('avg_score'),
        func.avg(
            func.extract('epoch', Review.completed_at - Review.created_at) / 86400
        ).label('avg_days_to_complete'),
        func.stddev(Review.overall_score).label('score_variance')
    ).join(Review).filter(
        User.role.in_(['staff', 'admin']),
        Review.created_at >= datetime.strptime(date_from, '%Y-%m-%d'),
        Review.created_at <= datetime.strptime(date_to, '%Y-%m-%d')
    )
    
    if not current_user.is_admin():
        reviewer_stats = reviewer_stats.join(Application).join(Grant)\
                                      .filter(Grant.created_by == current_user.id)
    
    if reviewer_id:
        reviewer_stats = reviewer_stats.filter(User.id == reviewer_id)
    
    if grant_id:
        reviewer_stats = reviewer_stats.join(Application).filter(Application.grant_id == grant_id)
    
    reviewer_stats = reviewer_stats.group_by(User.id, User.full_name, User.email)\
                                  .order_by(func.count(Review.id).desc()).all()
    
    # Review completion trends
    completion_trends = db.session.query(
        func.date_trunc('week', Review.completed_at).label('week'),
        func.count(Review.id).label('completed_reviews'),
        func.avg(Review.overall_score).label('avg_score')
    ).filter(
        Review.status == 'completed',
        Review.completed_at >= datetime.strptime(date_from, '%Y-%m-%d'),
        Review.completed_at <= datetime.strptime(date_to, '%Y-%m-%d')
    )
    
    if not current_user.is_admin():
        completion_trends = completion_trends.join(Application).join(Grant)\
                                           .filter(Grant.created_by == current_user.id)
    
    if reviewer_id:
        completion_trends = completion_trends.filter(Review.reviewer_id == reviewer_id)
    
    if grant_id:
        completion_trends = completion_trends.join(Application).filter(Application.grant_id == grant_id)
    
    completion_trends = completion_trends.group_by(
        func.date_trunc('week', Review.completed_at)
    ).order_by(
        func.date_trunc('week', Review.completed_at)
    ).all()
    
    # Get all reviewers and grants for filters
    if current_user.is_admin():
        all_reviewers = User.query.filter(User.role.in_(['staff', 'admin'])).all()
        all_grants = Grant.query.filter_by(is_published=True).all()
    else:
        # For non-admin staff, show reviewers who have reviewed their grants
        all_reviewers = User.query.join(Review).join(Application).join(Grant)\
                                 .filter(Grant.created_by == current_user.id,
                                        User.role.in_(['staff', 'admin']))\
                                 .distinct().all()
        all_grants = Grant.query.filter_by(created_by=current_user.id, is_published=True).all()
    
    return render_template('reports/reviewer_performance.html',
                         title='Reviewer Performance',
                         reviewer_stats=reviewer_stats,
                         completion_trends=completion_trends,
                         all_reviewers=all_reviewers,
                         all_grants=all_grants,
                         reviewer_id=reviewer_id,
                         grant_id=grant_id,
                         date_from=date_from,
                         date_to=date_to)

# Export routes
@bp.route('/export/<report_type>')
@login_required
def export_report(report_type):
    """Export reports in various formats"""
    if not current_user.is_staff():
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    format_type = request.args.get('format', 'csv')
    
    if report_type == 'applications':
        return _export_applications(format_type)
    elif report_type == 'grants':
        return _export_grants(format_type)
    elif report_type == 'financial':
        return _export_financial(format_type)
    elif report_type == 'reviews':
        return _export_reviews(format_type)
    else:
        flash('Invalid report type.', 'error')
        return redirect(url_for('reports.dashboard'))

def _export_applications(format_type):
    """Export applications data"""
    # Build query based on user permissions
    if current_user.is_admin():
        applications = Application.query.join(Grant).all()
    else:
        applications = Application.query.join(Grant).filter(Grant.created_by == current_user.id).all()
    
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Application ID', 'Project Title', 'Organization', 'Grant Program',
            'Amount Requested', 'Amount Approved', 'Status', 'Score',
            'Submitted Date', 'Approved Date'
        ])
        
        # Write data
        for app in applications:
            writer.writerow([
                app.id,
                app.project_title,
                app.organization_name,
                app.grant.title,
                app.amount_requested,
                app.amount_approved or '',
                app.status,
                app.calculated_score or '',
                app.submitted_at.strftime('%Y-%m-%d') if app.submitted_at else '',
                app.approved_at.strftime('%Y-%m-%d') if app.approved_at else ''
            ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=applications_export.csv'
        return response
    
    # Add other format types (JSON, Excel) as needed
    flash('Export format not supported yet.', 'warning')
    return redirect(url_for('reports.dashboard'))

def _export_grants(format_type):
    """Export grants data"""
    # Implementation for grants export
    pass

def _export_financial(format_type):
    """Export financial data"""
    # Implementation for financial export
    pass

def _export_reviews(format_type):
    """Export reviews data"""
    # Implementation for reviews export
    pass

# API Routes for charts and data
@bp.route('/api/dashboard-data')
@login_required
def api_dashboard_data():
    """API endpoint for dashboard chart data"""
    if not current_user.is_staff():
        return jsonify({'error': 'Access denied'}), 403
    
    # Get the same data as dashboard but return as JSON
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    
    # Build base query based on user permissions
    if current_user.is_admin():
        applications_query = Application.query
    else:
        applications_query = Application.query.join(Grant).filter(Grant.created_by == current_user.id)
    
    # Monthly trends data
    monthly_trends = db.session.query(
        extract('year', Application.submitted_at).label('year'),
        extract('month', Application.submitted_at).label('month'),
        func.count(Application.id).label('applications'),
        func.sum(Application.amount_requested).label('amount_requested')
    ).filter(
        Application.submitted_at >= start_date,
        Application.submitted_at <= end_date
    )
    
    if not current_user.is_admin():
        monthly_trends = monthly_trends.join(Grant).filter(Grant.created_by == current_user.id)
    
    monthly_trends = monthly_trends.group_by(
        extract('year', Application.submitted_at),
        extract('month', Application.submitted_at)
    ).order_by(
        extract('year', Application.submitted_at),
        extract('month', Application.submitted_at)
    ).all()
    
    # Status distribution
    status_counts = db.session.query(
        Application.status,
        func.count(Application.id).label('count')
    ).filter(
        Application.submitted_at >= start_date,
        Application.submitted_at <= end_date
    )
    
    if not current_user.is_admin():
        status_counts = status_counts.join(Grant).filter(Grant.created_by == current_user.id)
    
    status_counts = status_counts.group_by(Application.status).all()
    
    return jsonify({
        'monthly_trends': [{
            'year': int(trend.year),
            'month': int(trend.month),
            'applications': trend.applications,
            'amount_requested': float(trend.amount_requested or 0)
        } for trend in monthly_trends],
        'status_distribution': [{
            'status': status.status,
            'count': status.count
        } for status in status_counts]
    })
