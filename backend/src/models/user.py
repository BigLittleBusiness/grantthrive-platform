from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic information
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile information
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    
    # Role and permissions
    role = db.Column(db.String(50), nullable=False, default='council_staff')  # council_admin, council_staff, community_member, system_admin
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Council information (for council users)
    council_name = db.Column(db.String(200), nullable=True)
    council_tier = db.Column(db.String(20), nullable=True)  # tier_1, tier_2, tier_3, tier_4
    council_state = db.Column(db.String(50), nullable=True)
    council_population = db.Column(db.Integer, nullable=True)
    department = db.Column(db.String(100), nullable=True)
    position = db.Column(db.String(100), nullable=True)
    
    # Subscription and billing (for council accounts)
    subscription_status = db.Column(db.String(50), default='trial')  # trial, active, suspended, cancelled
    subscription_tier = db.Column(db.String(20), nullable=True)
    subscription_start = db.Column(db.DateTime, nullable=True)
    subscription_end = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Settings and preferences
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    theme_preference = db.Column(db.String(20), default='light')  # light, dark, auto
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'avatar_url': self.avatar_url,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'council_name': self.council_name,
            'council_tier': self.council_tier,
            'council_state': self.council_state,
            'council_population': self.council_population,
            'department': self.department,
            'position': self.position,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'email_notifications': self.email_notifications,
            'sms_notifications': self.sms_notifications,
            'theme_preference': self.theme_preference
        }
        
        if include_sensitive:
            data.update({
                'subscription_status': self.subscription_status,
                'subscription_tier': self.subscription_tier,
                'subscription_start': self.subscription_start.isoformat() if self.subscription_start else None,
                'subscription_end': self.subscription_end.isoformat() if self.subscription_end else None,
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'
