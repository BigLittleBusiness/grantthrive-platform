from datetime import datetime
from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.grant import Grant
from src.routes.auth import verify_token

grants_bp = Blueprint('grants', __name__)

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

@grants_bp.route('', methods=['GET'])
def get_grants():
    """Get all grants with optional filtering"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Query parameters for filtering
        status = request.args.get('status')
        category = request.args.get('category')
        search = request.args.get('search')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build query
        query = Grant.query
        
        # Filter by council for council users
        if user.role in ['council_admin', 'council_staff']:
            query = query.filter_by(council_id=user.id)
        
        # Apply filters
        if status:
            query = query.filter_by(status=status)
        
        if category:
            query = query.filter_by(category=category)
        
        if search:
            query = query.filter(Grant.title.contains(search) | Grant.description.contains(search))
        
        # Order by creation date (newest first)
        query = query.order_by(Grant.created_at.desc())
        
        # Paginate
        grants = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'grants': [grant.to_dict() for grant in grants.items],
            'total': grants.total,
            'pages': grants.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grants_bp.route('/<int:grant_id>', methods=['GET'])
def get_grant(grant_id):
    """Get a specific grant"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check permissions
        if user.role in ['council_admin', 'council_staff'] and grant.council_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'grant': grant.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grants_bp.route('', methods=['POST'])
def create_grant():
    """Create a new grant"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        if user.role not in ['council_admin', 'council_staff']:
            return jsonify({'error': 'Only council users can create grants'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description', 'category', 'amount']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create grant
        grant = Grant(
            title=data['title'],
            description=data['description'],
            category=data['category'],
            amount=float(data['amount']),
            status=data.get('status', 'draft'),
            eligibility_criteria=data.get('eligibility_criteria'),
            required_documents=data.get('required_documents'),
            assessment_criteria=data.get('assessment_criteria'),
            council_id=user.id,
            contact_person=data.get('contact_person'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            max_applications=data.get('max_applications'),
            auto_approve=data.get('auto_approve', False),
            public_voting=data.get('public_voting', False)
        )
        
        # Parse dates if provided
        if data.get('opens_at'):
            grant.opens_at = datetime.fromisoformat(data['opens_at'].replace('Z', '+00:00'))
        
        if data.get('closes_at'):
            grant.closes_at = datetime.fromisoformat(data['closes_at'].replace('Z', '+00:00'))
        
        db.session.add(grant)
        db.session.commit()
        
        return jsonify({
            'message': 'Grant created successfully',
            'grant': grant.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@grants_bp.route('/<int:grant_id>', methods=['PUT'])
def update_grant(grant_id):
    """Update a grant"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check permissions
        if user.role in ['council_admin', 'council_staff'] and grant.council_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update fields
        updatable_fields = [
            'title', 'description', 'category', 'amount', 'status',
            'eligibility_criteria', 'required_documents', 'assessment_criteria',
            'contact_person', 'contact_email', 'contact_phone',
            'max_applications', 'auto_approve', 'public_voting'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'amount':
                    setattr(grant, field, float(data[field]))
                else:
                    setattr(grant, field, data[field])
        
        # Update dates if provided
        if 'opens_at' in data:
            if data['opens_at']:
                grant.opens_at = datetime.fromisoformat(data['opens_at'].replace('Z', '+00:00'))
            else:
                grant.opens_at = None
        
        if 'closes_at' in data:
            if data['closes_at']:
                grant.closes_at = datetime.fromisoformat(data['closes_at'].replace('Z', '+00:00'))
            else:
                grant.closes_at = None
        
        grant.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Grant updated successfully',
            'grant': grant.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@grants_bp.route('/<int:grant_id>', methods=['DELETE'])
def delete_grant(grant_id):
    """Delete a grant"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        grant = Grant.query.get(grant_id)
        if not grant:
            return jsonify({'error': 'Grant not found'}), 404
        
        # Check permissions
        if user.role in ['council_admin', 'council_staff'] and grant.council_id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if grant has applications
        if grant.applications:
            return jsonify({'error': 'Cannot delete grant with existing applications'}), 400
        
        db.session.delete(grant)
        db.session.commit()
        
        return jsonify({'message': 'Grant deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@grants_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get available grant categories"""
    categories = [
        'Community Development',
        'Arts and Culture',
        'Sports and Recreation',
        'Environment and Sustainability',
        'Education and Training',
        'Health and Wellbeing',
        'Infrastructure',
        'Economic Development',
        'Youth Programs',
        'Senior Services',
        'Disability Services',
        'Emergency Services',
        'Technology and Innovation',
        'Heritage and History',
        'Tourism and Events'
    ]
    
    return jsonify({'categories': categories}), 200

@grants_bp.route('/public', methods=['GET'])
def get_public_grants():
    """Get public grants (no authentication required)"""
    try:
        # Query parameters for filtering
        status = request.args.get('status', 'active')
        category = request.args.get('category')
        search = request.args.get('search')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build query for active grants only
        query = Grant.query.filter_by(status=status)
        
        # Apply filters
        if category:
            query = query.filter_by(category=category)
        
        if search:
            query = query.filter(Grant.title.contains(search) | Grant.description.contains(search))
        
        # Order by creation date (newest first)
        query = query.order_by(Grant.created_at.desc())
        
        # Paginate
        grants = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Return public information only
        public_grants = []
        for grant in grants.items:
            grant_dict = grant.to_dict()
            # Remove sensitive information
            grant_dict.pop('council_id', None)
            public_grants.append(grant_dict)
        
        return jsonify({
            'grants': public_grants,
            'total': grants.total,
            'pages': grants.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

