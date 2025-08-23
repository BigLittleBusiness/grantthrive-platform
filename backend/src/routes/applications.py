from datetime import datetime, date
from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.grant import Grant
from src.models.application import Application
from src.routes.auth import verify_token

applications_bp = Blueprint('applications', __name__)

def get_current_user():
    """Get current user from JWT token"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    user_id = verify_token(token)
    
    if not user_id:
        return None
    
    return User.query.get(user_id)

@applications_bp.route('', methods=['GET'])
def get_applications():
    """Get applications with optional filtering"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Query parameters for filtering
        status = request.args.get('status')
        grant_id = request.args.get('grant_id')
        search = request.args.get('search')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build query based on user role
        if user.role in ['council_admin', 'council_staff']:
            # Council users see applications for their grants
            grant_ids = [g.id for g in Grant.query.filter_by(council_id=user.id).all()]
            query = Application.query.filter(Application.grant_id.in_(grant_ids))
        else:
            # Community members see their own applications
            query = Application.query.filter_by(applicant_email=user.email)
        
        # Apply filters
        if status:
            query = query.filter_by(status=status)
        
        if grant_id:
            query = query.filter_by(grant_id=grant_id)
        
        if search:
            query = query.filter(
                Application.project_title.contains(search) |
                Application.applicant_name.contains(search) |
                Application.organization_name.contains(search)
            )
        
        # Order by submission date (newest first)
        query = query.order_by(Application.submitted_at.desc())
        
        # Paginate
        applications = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'applications': [app.to_dict() for app in applications.items],
            'total': applications.total,
            'pages': applications.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@applications_bp.route('/<int:application_id>', methods=['GET'])
def get_application(application_id):
    """Get a specific application"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check permissions
        if user.role in ['council_admin', 'council_staff']:
            # Council users can see applications for their grants
            grant = Grant.query.get(application.grant_id)
            if not grant or grant.council_id != user.id:
                return jsonify({'error': 'Access denied'}), 403
        else:
            # Community members can only see their own applications
            if application.applicant_email != user.email:
                return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'application': application.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@applications_bp.route('', methods=['POST'])
def create_application():
    """Submit a new application"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'grant_id', 'applicant_name', 'applicant_email',
            'project_title', 'project_description', 'requested_amount'
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate grant exists and is active
        grant = Grant.query.get(data['grant_id'])
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        if grant.status != 'active':
            return jsonify({'error': 'Grant is not currently accepting applications'}), 400
        
        # Check if grant has closed
        if grant.closes_at and grant.closes_at < datetime.utcnow():
            return jsonify({'error': 'Grant application period has closed'}), 400
        
        # Check maximum applications limit
        if grant.max_applications:
            current_count = Application.query.filter_by(grant_id=grant.id).count()
            if current_count >= grant.max_applications:
                return jsonify({'error': 'Grant has reached maximum number of applications'}), 400
        
        # Create application
        application = Application(
            grant_id=data['grant_id'],
            applicant_name=data['applicant_name'],
            applicant_email=data['applicant_email'],
            applicant_phone=data.get('applicant_phone'),
            organization_name=data.get('organization_name'),
            organization_type=data.get('organization_type'),
            abn_acn=data.get('abn_acn'),
            project_title=data['project_title'],
            project_description=data['project_description'],
            requested_amount=float(data['requested_amount']),
            project_budget=data.get('project_budget'),
            documents=data.get('documents'),
            public_comments=data.get('public_comments')
        )
        
        # Parse dates if provided
        if data.get('project_start_date'):
            application.project_start_date = datetime.strptime(data['project_start_date'], '%Y-%m-%d').date()
        
        if data.get('project_end_date'):
            application.project_end_date = datetime.strptime(data['project_end_date'], '%Y-%m-%d').date()
        
        # Auto-approve if enabled
        if grant.auto_approve:
            application.status = 'approved'
            application.approved_amount = application.requested_amount
            application.decision_date = datetime.utcnow()
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'message': 'Application submitted successfully',
            'application': application.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@applications_bp.route('/<int:application_id>/status', methods=['PUT'])
def update_application_status(application_id):
    """Update application status (council users only)"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        if user.role not in ['council_admin', 'council_staff']:
            return jsonify({'error': 'Only council users can update application status'}), 403
        
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check permissions
        grant = Grant.query.get(application.grant_id)
        if not grant or grant.council_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        if not data.get('status'):
            return jsonify({'error': 'Status is required'}), 400
        
        valid_statuses = ['submitted', 'under_review', 'approved', 'rejected', 'withdrawn']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Update application
        application.status = data['status']
        application.reviewer_notes = data.get('reviewer_notes')
        application.public_notes = data.get('public_notes')
        application.score = data.get('score')
        application.reviewed_at = datetime.utcnow()
        
        if data['status'] in ['approved', 'rejected']:
            application.decision_date = datetime.utcnow()
            
            if data['status'] == 'approved':
                application.approved_amount = data.get('approved_amount', application.requested_amount)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Application status updated successfully',
            'application': application.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@applications_bp.route('/<int:application_id>', methods=['PUT'])
def update_application(application_id):
    """Update application details"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check permissions
        if user.role in ['council_admin', 'council_staff']:
            # Council users can update applications for their grants
            grant = Grant.query.get(application.grant_id)
            if not grant or grant.council_id != user.id:
                return jsonify({'error': 'Access denied'}), 403
        else:
            # Community members can only update their own applications if still in draft/submitted status
            if application.applicant_email != user.email:
                return jsonify({'error': 'Access denied'}), 403
            
            if application.status not in ['submitted']:
                return jsonify({'error': 'Cannot update application after review has started'}), 400
        
        data = request.get_json()
        
        # Update fields based on user role
        if user.role in ['council_admin', 'council_staff']:
            # Council users can update assessment fields
            updatable_fields = [
                'priority', 'score', 'reviewer_notes', 'public_notes',
                'approved_amount', 'payment_schedule', 'reporting_requirements',
                'compliance_status'
            ]
        else:
            # Community members can update application details
            updatable_fields = [
                'applicant_name', 'applicant_phone', 'organization_name',
                'organization_type', 'abn_acn', 'project_title',
                'project_description', 'requested_amount', 'project_budget',
                'documents', 'public_comments'
            ]
        
        for field in updatable_fields:
            if field in data:
                if field in ['requested_amount', 'approved_amount', 'score']:
                    setattr(application, field, float(data[field]) if data[field] is not None else None)
                else:
                    setattr(application, field, data[field])
        
        # Update dates if provided
        if 'project_start_date' in data and data['project_start_date']:
            application.project_start_date = datetime.strptime(data['project_start_date'], '%Y-%m-%d').date()
        
        if 'project_end_date' in data and data['project_end_date']:
            application.project_end_date = datetime.strptime(data['project_end_date'], '%Y-%m-%d').date()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Application updated successfully',
            'application': application.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@applications_bp.route('/<int:application_id>', methods=['DELETE'])
def delete_application(application_id):
    """Delete/withdraw an application"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check permissions
        if user.role in ['council_admin', 'council_staff']:
            # Council users can delete applications for their grants
            grant = Grant.query.get(application.grant_id)
            if not grant or grant.council_id != user.id:
                return jsonify({'error': 'Access denied'}), 403
        else:
            # Community members can only withdraw their own applications
            if application.applicant_email != user.email:
                return jsonify({'error': 'Access denied'}), 403
            
            if application.status not in ['submitted', 'under_review']:
                return jsonify({'error': 'Cannot withdraw application after decision has been made'}), 400
        
        if user.role in ['council_admin', 'council_staff']:
            # Council users can permanently delete
            db.session.delete(application)
        else:
            # Community members withdraw (change status)
            application.status = 'withdrawn'
        
        db.session.commit()
        
        message = 'Application deleted successfully' if user.role in ['council_admin', 'council_staff'] else 'Application withdrawn successfully'
        
        return jsonify({'message': message}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@applications_bp.route('/stats', methods=['GET'])
def get_application_stats():
    """Get application statistics (council users only)"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        if user.role not in ['council_admin', 'council_staff']:
            return jsonify({'error': 'Only council users can view statistics'}), 403
        
        # Get applications for user's grants
        grant_ids = [g.id for g in Grant.query.filter_by(council_id=user.id).all()]
        applications = Application.query.filter(Application.grant_id.in_(grant_ids)).all()
        
        # Calculate statistics
        total_applications = len(applications)
        status_counts = {}
        total_requested = 0
        total_approved = 0
        
        for app in applications:
            status_counts[app.status] = status_counts.get(app.status, 0) + 1
            total_requested += app.requested_amount or 0
            if app.approved_amount:
                total_approved += app.approved_amount
        
        return jsonify({
            'total_applications': total_applications,
            'status_counts': status_counts,
            'total_requested_amount': total_requested,
            'total_approved_amount': total_approved,
            'approval_rate': (status_counts.get('approved', 0) / total_applications * 100) if total_applications > 0 else 0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

