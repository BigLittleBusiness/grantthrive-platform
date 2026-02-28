"""
Utility functions for GrantThrive platform
"""
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
from datetime import datetime, timedelta
import re
import hashlib
import secrets

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    """Decorator to require staff access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff():
            return jsonify({'error': 'Staff access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate Australian/NZ phone number"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Australian mobile: 04xx xxx xxx (10 digits starting with 04)
    # Australian landline: 0x xxxx xxxx (10 digits starting with 02, 03, 07, 08)
    # NZ mobile: 02x xxx xxxx (10 digits starting with 02)
    # NZ landline: 0x xxx xxxx (9-10 digits)
    
    if len(digits) == 10:
        # Australian numbers
        if digits.startswith(('02', '03', '04', '07', '08')):
            return True
    elif len(digits) == 9:
        # NZ landline
        if digits.startswith(('03', '04', '06', '07', '09')):
            return True
    
    return False

def format_currency(amount, currency='AUD'):
    """Format currency for display"""
    if amount is None:
        return 'N/A'
    
    symbol = '$' if currency in ['AUD', 'NZD'] else currency
    return f"{symbol}{amount:,.2f}"

def format_date(date, format='%d/%m/%Y'):
    """Format date for display"""
    if date is None:
        return 'N/A'
    
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            return date
    
    return date.strftime(format)

def format_datetime(dt, format='%d/%m/%Y %I:%M %p'):
    """Format datetime for display"""
    if dt is None:
        return 'N/A'
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    
    return dt.strftime(format)

def calculate_days_until(target_date):
    """Calculate days until target date"""
    if target_date is None:
        return None
    
    if isinstance(target_date, str):
        try:
            target_date = datetime.fromisoformat(target_date)
        except ValueError:
            return None
    
    delta = target_date - datetime.utcnow()
    return delta.days

def generate_secure_token(length=32):
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)

def hash_file_content(content):
    """Generate hash of file content for integrity checking"""
    return hashlib.sha256(content).hexdigest()

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limit length
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}.{ext}" if ext else name

def get_file_extension(filename):
    """Get file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def is_allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return get_file_extension(filename) in allowed_extensions

def calculate_file_size_mb(size_bytes):
    """Convert bytes to MB"""
    return round(size_bytes / (1024 * 1024), 2)

def truncate_text(text, max_length=100, suffix='...'):
    """Truncate text to specified length"""
    if text is None:
        return ''
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_client_ip():
    """Get client IP address"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

def log_user_action(action, details=None):
    """Log user action for audit trail"""
    from app.models import AuditLog
    from app import db
    
    try:
        log_entry = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            details=details,
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent', ''),
            timestamp=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to log user action: {e}")

def calculate_percentage(part, total):
    """Calculate percentage with safe division"""
    if total == 0:
        return 0
    return round((part / total) * 100, 1)

def get_status_badge_class(status):
    """Get Bootstrap badge class for status"""
    status_classes = {
        'draft': 'bg-secondary',
        'submitted': 'bg-primary',
        'under_review': 'bg-warning',
        'approved': 'bg-success',
        'rejected': 'bg-danger',
        'withdrawn': 'bg-dark',
        'open': 'bg-success',
        'closed': 'bg-danger',
        'pending': 'bg-warning',
        'completed': 'bg-success',
        'active': 'bg-success',
        'inactive': 'bg-secondary'
    }
    return status_classes.get(status.lower(), 'bg-secondary')

def format_status_display(status):
    """Format status for display"""
    return status.replace('_', ' ').title()

def generate_qr_code_data_url(data):
    """Generate QR code as data URL"""
    import qrcode
    import io
    import base64
    from PIL import Image
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to data URL
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_data = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_data}"

def paginate_results(query, page=1, per_page=20):
    """Paginate query results with error handling"""
    try:
        return query.paginate(
            page=page,
            per_page=min(per_page, 100),  # Limit max per page
            error_out=False
        )
    except Exception as e:
        current_app.logger.error(f"Pagination error: {e}")
        return query.paginate(page=1, per_page=20, error_out=False)

def build_search_query(model, search_term, search_fields):
    """Build search query for multiple fields"""
    from sqlalchemy import or_
    
    if not search_term:
        return model.query
    
    search_conditions = []
    for field in search_fields:
        if hasattr(model, field):
            attr = getattr(model, field)
            search_conditions.append(attr.ilike(f'%{search_term}%'))
    
    if search_conditions:
        return model.query.filter(or_(*search_conditions))
    
    return model.query

def validate_date_range(start_date, end_date):
    """Validate date range"""
    if start_date and end_date:
        if start_date > end_date:
            return False, "Start date must be before end date"
        
        # Check if range is reasonable (not more than 10 years)
        if (end_date - start_date).days > 3650:
            return False, "Date range cannot exceed 10 years"
    
    return True, None

def get_time_ago(dt):
    """Get human-readable time ago string"""
    if dt is None:
        return 'Never'
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

# Template filters
def register_template_filters(app):
    """Register custom template filters"""
    
    @app.template_filter('currency')
    def currency_filter(amount, currency='AUD'):
        return format_currency(amount, currency)
    
    @app.template_filter('date')
    def date_filter(date, format='%d/%m/%Y'):
        return format_date(date, format)
    
    @app.template_filter('datetime')
    def datetime_filter(dt, format='%d/%m/%Y %I:%M %p'):
        return format_datetime(dt, format)
    
    @app.template_filter('truncate')
    def truncate_filter(text, length=100):
        return truncate_text(text, length)
    
    @app.template_filter('percentage')
    def percentage_filter(part, total):
        return calculate_percentage(part, total)
    
    @app.template_filter('status_badge')
    def status_badge_filter(status):
        return get_status_badge_class(status)
    
    @app.template_filter('status_display')
    def status_display_filter(status):
        return format_status_display(status)
    
    @app.template_filter('time_ago')
    def time_ago_filter(dt):
        return get_time_ago(dt)
