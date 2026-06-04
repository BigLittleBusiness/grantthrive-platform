"""
GrantThrive — Health Check Endpoint
====================================
Provides a simple /api/health endpoint used by the CI/CD pipeline to verify
the backend is running correctly after a deployment.
"""
from flask import Blueprint, jsonify
from app import db
import sqlalchemy

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Returns 200 OK with status information if the app is running correctly.
    Checks database connectivity as part of the health check.
    """
    status = {
        'status': 'ok',
        'service': 'grantthrive-backend',
        'domain': 'grantthrive.com',
        'deployment_marker': 'ci-cd-branch-validation-2026-06-04',
    }

    # Check database connectivity
    try:
        db.session.execute(sqlalchemy.text('SELECT 1'))
        status['database'] = 'ok'
    except Exception as e:
        status['status'] = 'degraded'
        status['database'] = f'error: {str(e)}'

    http_status = 200 if status['status'] == 'ok' else 503
    return jsonify(status), http_status
