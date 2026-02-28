from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Numeric
import qrcode
import io
import base64
from app import db

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False, default='staff')  # admin, staff, community
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    created_grants = db.relationship('Grant', backref='creator', lazy='dynamic')
    applications = db.relationship('Application', backref='applicant', lazy='dynamic')
    reviews = db.relationship('Review', backref='reviewer', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_staff(self):
        """Check if user is staff or admin"""
        return self.role in ['admin', 'staff']
    
    def __repr__(self):
        return f'<User {self.username}>'

class Grant(db.Model):
    """Grant program model"""
    __tablename__ = 'grants'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    total_budget = db.Column(Numeric(12, 2), nullable=False)
    max_amount_per_application = db.Column(Numeric(10, 2))
    min_amount_per_application = db.Column(Numeric(10, 2))
    
    # Dates
    opens_at = db.Column(db.DateTime, nullable=False)
    closes_at = db.Column(db.DateTime, nullable=False)
    assessment_deadline = db.Column(db.DateTime)
    notification_date = db.Column(db.DateTime)
    
    # Status and settings
    status = db.Column(db.String(20), default='draft')  # draft, open, closed, completed
    is_published = db.Column(db.Boolean, default=False)
    allow_multiple_applications = db.Column(db.Boolean, default=False)
    require_community_voting = db.Column(db.Boolean, default=False)
    enable_mapping = db.Column(db.Boolean, default=False)
    
    # Location fields for mapping
    location_name = db.Column(db.String(200))  # Human-readable location
    latitude = db.Column(db.Float)  # Geographic coordinates
    longitude = db.Column(db.Float)
    address = db.Column(db.String(500))  # Full address
    postcode = db.Column(db.String(10))  # Postal code
    state = db.Column(db.String(50))  # State/Territory
    region = db.Column(db.String(100))  # Region/Area
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # QR Code
    qr_code_data = db.Column(db.Text)  # Base64 encoded QR code image
    
    # Relationships
    applications = db.relationship('Application', backref='grant', lazy='dynamic', cascade='all, delete-orphan')
    criteria = db.relationship('GrantCriteria', backref='grant', lazy='dynamic', cascade='all, delete-orphan')
    
    def generate_qr_code(self):
        """Generate QR code for the grant"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_data = f"https://grantthrive.com.au/grants/{self.id}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Encode as base64 for storage
        self.qr_code_data = base64.b64encode(buffer.getvalue()).decode()
    
    @property
    def is_open(self):
        """Check if grant is currently open for applications"""
        now = datetime.utcnow()
        return (self.status == 'open' and 
                self.is_published and 
                self.opens_at <= now <= self.closes_at)
    
    @property
    def days_remaining(self):
        """Calculate days remaining until close"""
        if not self.is_open:
            return 0
        delta = self.closes_at - datetime.utcnow()
        return max(0, delta.days)
    
    def __repr__(self):
        return f'<Grant {self.title}>'

class GrantCriteria(db.Model):
    """Grant assessment criteria"""
    __tablename__ = 'grant_criteria'
    
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    weight = db.Column(db.Integer, default=1)  # Weighting for scoring
    max_score = db.Column(db.Integer, default=10)
    order = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<GrantCriteria {self.name}>'

class Application(db.Model):
    """Grant application model"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Application details
    organization_name = db.Column(db.String(200), nullable=False)
    project_title = db.Column(db.String(200), nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    amount_requested = db.Column(Numeric(10, 2), nullable=False)
    
    # Contact information
    contact_person = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20))
    
    # Location (for mapping)
    address = db.Column(db.String(500))
    postcode = db.Column(db.String(10))  # Applicant postcode for demographics
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Status and workflow
    status = db.Column(db.String(20), default='draft')  # draft, submitted, under_review, approved, rejected
    submitted_at = db.Column(db.DateTime)
    reviewed_at = db.Column(db.DateTime)
    decision_date = db.Column(db.DateTime)
    
    # Scoring
    total_score = db.Column(db.Float)
    average_score = db.Column(db.Float)
    
    # Community voting
    community_votes = db.Column(db.Integer, default=0)
    community_score = db.Column(db.Float, default=0.0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship('Review', backref='application', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('ApplicationDocument', backref='application', lazy='dynamic', cascade='all, delete-orphan')
    votes = db.relationship('CommunityVote', backref='application', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_scores(self):
        """Calculate total and average scores from reviews"""
        reviews = self.reviews.filter_by(is_complete=True).all()
        if not reviews:
            self.total_score = 0
            self.average_score = 0
            return
        
        total = sum(review.total_score for review in reviews)
        self.total_score = total
        self.average_score = total / len(reviews)
    
    @property
    def is_submitted(self):
        """Check if application has been submitted"""
        return self.status != 'draft'
    
    def __repr__(self):
        return f'<Application {self.project_title}>'

class ApplicationDocument(db.Model):
    """Documents attached to applications"""
    __tablename__ = 'application_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ApplicationDocument {self.original_filename}>'

class Review(db.Model):
    """Application review and scoring"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Review status
    is_complete = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime)
    
    # Overall assessment
    total_score = db.Column(db.Float, default=0.0)
    recommendation = db.Column(db.String(20))  # approve, reject, conditional
    comments = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scores = db.relationship('ReviewScore', backref='review', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_total_score(self):
        """Calculate total weighted score"""
        total = 0
        for score in self.scores:
            if score.score is not None:
                weight = score.criteria.weight if score.criteria else 1
                total += score.score * weight
        self.total_score = total
    
    def __repr__(self):
        return f'<Review {self.id}>'

class ReviewScore(db.Model):
    """Individual criterion scores within a review"""
    __tablename__ = 'review_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    criteria_id = db.Column(db.Integer, db.ForeignKey('grant_criteria.id'), nullable=False)
    score = db.Column(db.Float)
    comments = db.Column(db.Text)
    
    # Relationships
    criteria = db.relationship('GrantCriteria', backref='scores')
    
    def __repr__(self):
        return f'<ReviewScore {self.score}>'

class CommunityVote(db.Model):
    """Community voting on applications"""
    __tablename__ = 'community_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for anonymous voting
    voting_session_id = db.Column(db.Integer, db.ForeignKey('voting_sessions.id'), nullable=False)
    
    # Vote details
    vote_value = db.Column(db.Integer, nullable=False)  # 1-5 rating or simple 1/0
    vote_type = db.Column(db.String(20), default='rating')  # 'rating', 'approval', 'priority'
    comments = db.Column(db.Text)
    
    # Voter information (for anonymous votes)
    voter_email = db.Column(db.String(120))
    voter_postcode = db.Column(db.String(10))
    voter_name = db.Column(db.String(100))
    
    # Security and fraud prevention
    ip_address = db.Column(db.String(45))  # For preventing duplicate votes
    user_agent = db.Column(db.String(500))  # Browser fingerprinting
    is_verified = db.Column(db.Boolean, default=True)
    is_flagged = db.Column(db.Boolean, default=False)
    flagged_reason = db.Column(db.String(200))
    
    # Metadata
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = db.relationship('Application', backref='community_votes')
    voter = db.relationship('User', backref='community_votes')
    
    def __repr__(self):
        return f'<CommunityVote {self.vote_value}>'

class VotingSession(db.Model):
    """Voting sessions for managing community voting periods"""
    __tablename__ = 'voting_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    
    # Session details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Voting configuration
    voting_type = db.Column(db.String(20), default='rating')  # 'rating', 'approval', 'priority', 'ranking'
    min_vote_value = db.Column(db.Integer, default=1)
    max_vote_value = db.Column(db.Integer, default=5)
    allow_comments = db.Column(db.Boolean, default=True)
    require_registration = db.Column(db.Boolean, default=False)
    
    # Timing
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)
    
    # Results and analytics
    total_votes = db.Column(db.Integer, default=0)
    total_voters = db.Column(db.Integer, default=0)
    average_participation = db.Column(db.Float, default=0.0)
    
    # Influence on final decisions
    voting_weight = db.Column(db.Float, default=0.2)  # 0.0-1.0, how much community votes influence final decision
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    grant = db.relationship('Grant', backref='voting_sessions')
    creator = db.relationship('User', backref='created_voting_sessions')
    votes = db.relationship('CommunityVote', backref='voting_session', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<VotingSession {self.title}>'
    
    @property
    def is_open(self):
        """Check if voting session is currently open"""
        now = datetime.utcnow()
        return self.is_active and self.starts_at <= now <= self.ends_at
    
    @property
    def status(self):
        """Get current status of voting session"""
        now = datetime.utcnow()
        if not self.is_published:
            return 'draft'
        elif now < self.starts_at:
            return 'scheduled'
        elif now > self.ends_at:
            return 'closed'
        elif self.is_active:
            return 'open'
        else:
            return 'paused'

class VotingResult(db.Model):
    """Aggregated voting results for applications"""
    __tablename__ = 'voting_results'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    voting_session_id = db.Column(db.Integer, db.ForeignKey('voting_sessions.id'), nullable=False)
    
    # Aggregated results
    total_votes = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    total_score = db.Column(db.Float, default=0.0)
    
    # Score distribution
    votes_1_star = db.Column(db.Integer, default=0)
    votes_2_star = db.Column(db.Integer, default=0)
    votes_3_star = db.Column(db.Integer, default=0)
    votes_4_star = db.Column(db.Integer, default=0)
    votes_5_star = db.Column(db.Integer, default=0)
    
    # Rankings
    community_rank = db.Column(db.Integer)  # Rank among all applications in this voting session
    percentile = db.Column(db.Float)  # Percentile ranking (0-100)
    
    # Engagement metrics
    total_comments = db.Column(db.Integer, default=0)
    engagement_score = db.Column(db.Float, default=0.0)  # Based on votes, comments, and interaction
    
    # Metadata
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = db.relationship('Application', backref='voting_results')
    voting_session = db.relationship('VotingSession', backref='results')
    
    def __repr__(self):
        return f'<VotingResult App:{self.application_id} Score:{self.average_score}>'

class WorkflowStep(db.Model):
    """Workflow steps for grant processing"""
    __tablename__ = 'workflow_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False)
    
    # Step configuration
    requires_review = db.Column(db.Boolean, default=False)
    requires_approval = db.Column(db.Boolean, default=False)
    auto_advance = db.Column(db.Boolean, default=False)
    
    # Assigned users
    assigned_users = db.Column(db.Text)  # JSON list of user IDs
    
    # Relationships
    grant = db.relationship('Grant', backref='workflow_steps')
    
    def __repr__(self):
        return f'<WorkflowStep {self.name}>'

class AuditLog(db.Model):
    """Audit trail for all system actions"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)  # grant, application, user, etc.
    entity_id = db.Column(db.Integer, nullable=False)
    old_values = db.Column(db.Text)  # JSON
    new_values = db.Column(db.Text)  # JSON
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action}>'
