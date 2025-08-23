import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from src.models.user import db
from src.routes.user import user_bp
from src.routes.grants import grants_bp
from src.routes.applications import applications_bp
from src.routes.auth import auth_bp
from src.routes.analytics import analytics_bp
from src.middleware.security import validate_input, rate_limit, log_security_event
from src.utils.audit import AuditLogger

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'grantthrive-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload

# Enable CORS for all routes with security considerations
CORS(app, 
     origins=['http://localhost:3000', 'https://grantthrive.com', 'https://*.grantthrive.com'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(grants_bp, url_prefix='/api/grants')
app.register_blueprint(applications_bp, url_prefix='/api/applications')
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

# Initialize database
db.init_app(app)

# Security middleware
@app.before_request
def security_middleware():
    """Apply security middleware to all requests"""
    # Log all API requests for security monitoring
    if request.path.startswith('/api/') and request.endpoint not in ['health_check']:
        AuditLogger.log_event(
            event_type='API_REQUEST',
            resource_type='API',
            additional_data={
                'endpoint': request.endpoint,
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr
            }
        )

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Error handlers with audit logging
@app.errorhandler(400)
def bad_request(error):
    AuditLogger.log_security_event('BAD_REQUEST', str(error), 'WARNING')
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(401)
def unauthorized(error):
    AuditLogger.log_security_event('UNAUTHORIZED_ACCESS', str(error), 'WARNING')
    return jsonify({'error': 'Unauthorized'}), 401

@app.errorhandler(403)
def forbidden(error):
    AuditLogger.log_security_event('FORBIDDEN_ACCESS', str(error), 'WARNING')
    return jsonify({'error': 'Forbidden'}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    AuditLogger.log_security_event('RATE_LIMIT_EXCEEDED', 'Too many requests', 'WARNING')
    return jsonify({'error': 'Rate limit exceeded'}), 429

@app.errorhandler(500)
def internal_error(error):
    AuditLogger.log_security_event('INTERNAL_ERROR', str(error), 'ERROR')
    return jsonify({'error': 'Internal server error'}), 500

# Create tables and initial data
with app.app_context():
    db.create_all()
    
    # Log application startup
    AuditLogger.log_system_event('APPLICATION_START', {
        'version': '1.0.0',
        'environment': os.environ.get('FLASK_ENV', 'development')
    })

# Health check endpoint with rate limiting
@app.route('/api/health')
@rate_limit(max_requests=200, window_minutes=1)
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'service': 'GrantThrive API',
            'version': '1.0.0',
            'database': 'connected',
            'features': {
                'rate_limiting': True,
                'audit_logging': True,
                'encryption': True,
                'security_headers': True
            }
        })
    except Exception as e:
        AuditLogger.log_system_event('HEALTH_CHECK_FAILED', {'error': str(e)})
        return jsonify({
            'status': 'unhealthy',
            'service': 'GrantThrive API',
            'version': '1.0.0',
            'database': 'disconnected',
            'error': str(e)
        }), 503

# API status endpoint
@app.route('/api/status')
@rate_limit(max_requests=50, window_minutes=1)
def api_status():
    """API status endpoint with detailed information"""
    return jsonify({
        'api_version': '1.0.0',
        'endpoints': {
            'authentication': '/api/auth',
            'users': '/api/users',
            'grants': '/api/grants',
            'applications': '/api/applications',
            'analytics': '/api/analytics'
        },
        'features': {
            'rate_limiting': True,
            'audit_logging': True,
            'encryption': True,
            'security_headers': True,
            'cors_enabled': True
        },
        'status': 'operational'
    })

# Serve React frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return jsonify({
            'message': 'GrantThrive API is running',
            'frontend': 'Not deployed - use /api endpoints for API access',
            'version': '1.0.0'
        }), 200

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({
                'message': 'GrantThrive API is running',
                'frontend': 'Not deployed - use /api endpoints for API access',
                'version': '1.0.0',
                'api_docs': '/api/status'
            }), 200

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=debug_mode
    )
