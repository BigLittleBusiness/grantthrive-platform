from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app.common.password import hash_password, verify_password
from app.common.encryption import EncryptedString, hmac_index
from sqlalchemy import Numeric
import qrcode
import io
import base64
import re
from app import db


# ── Council (Tenant) ──────────────────────────────────────────────────────────

class Council(db.Model):
    """
    A council is the top-level tenant in GrantThrive.

    Every grant, user, voting session, and audit log belongs to exactly one
    council.  The ``subdomain`` field drives the URL routing:

        cityofmelbourne.grantthrive.com  →  Council(subdomain='cityofmelbourne')

    The system_admin role (GrantThrive staff) is NOT scoped to any council
    (council_id = NULL on their User record).
    """
    __tablename__ = 'councils'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)          # "City of Melbourne"
    subdomain   = db.Column(db.String(100), unique=True, nullable=False, index=True)  # "cityofmelbourne"
    slug        = db.Column(db.String(100), unique=True, nullable=False, index=True)  # "city-of-melbourne"
    lga_code    = db.Column(db.String(20))                           # ABS LGA code e.g. "24600"
    state       = db.Column(db.String(50))                           # "VIC"
    country     = db.Column(db.String(50), default='Australia')

    # Branding
    logo_url        = db.Column(db.String(500))
    primary_colour  = db.Column(db.String(7), default='#15803d')     # Hex, defaults to GT green
    secondary_colour= db.Column(db.String(7), default='#166534')

    # Contact — PII fields stored encrypted
    contact_email   = db.Column(EncryptedString(500))
    contact_phone   = db.Column(EncryptedString(200))
    website_url     = db.Column(db.String(500))      # not PII — public URL
    address         = db.Column(EncryptedString(700))
    postcode        = db.Column(db.String(10))

    # Subscription / billing
    plan                   = db.Column(db.String(20), default='small')   # small, medium, large, trial
    is_active              = db.Column(db.Boolean, default=True)
    trial_ends_at          = db.Column(db.DateTime)
    # Add-ons (purchasable by Small Council only)
    addon_community_voting = db.Column(db.Boolean, default=False)
    addon_grant_mapping    = db.Column(db.Boolean, default=False)

    # Metadata
    created_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                onupdate=lambda: datetime.now(timezone.utc))
    created_by      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    users           = db.relationship('User',          foreign_keys='User.council_id',
                                      backref='council', lazy='dynamic')
    grants          = db.relationship('Grant',         backref='council', lazy='dynamic',
                                      cascade='all, delete-orphan')
    voting_sessions = db.relationship('VotingSession', backref='council', lazy='dynamic')
    audit_logs      = db.relationship('AuditLog',      backref='council', lazy='dynamic')

    @staticmethod
    def make_subdomain(name: str) -> str:
        """Derive a URL-safe subdomain from a council name."""
        s = name.lower()
        s = re.sub(r'[^a-z0-9\s-]', '', s)
        s = re.sub(r'[\s-]+', '-', s).strip('-')
        return s

    @staticmethod
    def make_slug(name: str) -> str:
        """Derive a URL-safe slug from a council name (same as subdomain for now)."""
        return Council.make_subdomain(name)

    def portal_url(self, scheme: str = 'https') -> str:
        """Return the full portal URL for this council."""
        return f"{scheme}://{self.subdomain}.grantthrive.com"

    def to_dict(self) -> dict:
        """Serialise to a safe dict for API responses."""
        return {
            'id':               self.id,
            'name':             self.name,
            'subdomain':        self.subdomain,
            'slug':             self.slug,
            'lga_code':         self.lga_code,
            'state':            self.state,
            'country':          self.country,
            'logo_url':         self.logo_url,
            'primary_colour':   self.primary_colour,
            'secondary_colour': self.secondary_colour,
            'contact_email':    self.contact_email,
            'contact_phone':    self.contact_phone,
            'website_url':      self.website_url,
            'plan':             self.plan,
            'is_active':        self.is_active,
            'addon_community_voting': self.addon_community_voting,
            'addon_grant_mapping':    self.addon_grant_mapping,
            'portal_url':       self.portal_url(),
            'created_at':       self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Council {self.subdomain}>'


# ── User ──────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    """User model for authentication and authorization.

    ``council_id`` is NULL for system_admin users (GrantThrive staff) who
    operate across all tenants.  All other roles must belong to a council.
    """
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False, index=True)
    # email is stored encrypted; email_hmac is a keyed HMAC-SHA256 index
    # used for login lookups (equality search on encrypted fields is not possible)
    email         = db.Column(EncryptedString(500), nullable=False)
    email_hmac    = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name    = db.Column(db.String(50), nullable=False)
    last_name     = db.Column(db.String(50), nullable=False)
    phone         = db.Column(EncryptedString(200))

    # Role: system_admin | council_admin | council_staff | community_member | professional_consultant
    role          = db.Column(db.String(30), nullable=False, default='community_member')

    # Tenant FK — NULL for system_admin only
    council_id    = db.Column(db.Integer, db.ForeignKey('councils.id'), nullable=True, index=True)

    is_active     = db.Column(db.Boolean, default=True)
    # Approval state for self-registered community_member / professional_consultant accounts
    is_approved   = db.Column(db.Boolean, default=False)
    # Optional profile fields collected during registration
    organisation  = db.Column(EncryptedString(300))
    abn           = db.Column(EncryptedString(100))   # Australian Business Number (consultants)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login    = db.Column(db.DateTime)

    # Relationships
    created_grants = db.relationship('Grant', foreign_keys='Grant.created_by',
                                     backref='creator', lazy='dynamic')
    applications   = db.relationship('Application', backref='applicant', lazy='dynamic')
    reviews        = db.relationship('Review', backref='reviewer', lazy='dynamic')

    def set_email(self, email: str) -> None:
        """Set the email field and update the HMAC search index atomically."""
        normalised = email.strip().lower()
        self.email      = normalised          # stored encrypted via EncryptedString
        self.email_hmac = hmac_index(normalised)  # searchable HMAC index

    def set_password(self, password: str) -> None:
        """Hash password using Argon2id and store the encoded hash."""
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> tuple[bool, bool]:
        """Verify password and return (is_valid, needs_rehash).

        The needs_rehash flag is True when the stored hash uses legacy
        PBKDF2 or outdated Argon2id parameters.  Callers should rehash
        transparently on successful login.
        """
        return verify_password(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def is_system_admin(self):
        return self.role == 'system_admin'

    def is_admin(self):
        return self.role in ('system_admin', 'council_admin')

    def is_staff(self):
        return self.role in ('system_admin', 'council_admin', 'council_staff')

    def __repr__(self):
        return f'<User {self.username}>'


# ── Grant ─────────────────────────────────────────────────────────────────────

class Grant(db.Model):
    """Grant program model — scoped to a council tenant."""
    __tablename__ = 'grants'

    id          = db.Column(db.Integer, primary_key=True)

    # Tenant FK
    council_id  = db.Column(db.Integer, db.ForeignKey('councils.id'), nullable=False, index=True)

    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category    = db.Column(db.String(100), nullable=False)
    total_budget= db.Column(Numeric(12, 2), nullable=False)
    max_amount_per_application = db.Column(Numeric(10, 2))
    min_amount_per_application = db.Column(Numeric(10, 2))

    # Dates
    opens_at            = db.Column(db.DateTime, nullable=False)
    closes_at           = db.Column(db.DateTime, nullable=False)
    assessment_deadline = db.Column(db.DateTime)
    notification_date   = db.Column(db.DateTime)

    # Status and settings
    status                    = db.Column(db.String(20), default='draft')
    is_published              = db.Column(db.Boolean, default=False)
    allow_multiple_applications = db.Column(db.Boolean, default=False)
    require_community_voting  = db.Column(db.Boolean, default=False)
    enable_mapping            = db.Column(db.Boolean, default=False)

    # Location fields for mapping
    location_name = db.Column(db.String(200))
    latitude      = db.Column(db.Float)
    longitude     = db.Column(db.Float)
    address       = db.Column(db.String(500))
    postcode      = db.Column(db.String(10))
    state         = db.Column(db.String(50))
    region        = db.Column(db.String(100))

    # Metadata
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))

    # Assessment team — configured at grant creation by council admin
    # JSON-encoded list of user IDs authorised to review applications for this grant.
    # An empty list means any council_staff member may self-assign.
    assigned_reviewer_ids = db.Column(db.Text, default='[]', nullable=False)
    # Number of independent staff approvals required before an application is marked approved.
    required_approvals    = db.Column(db.Integer, default=1, nullable=False)

    # QR Code
    qr_code_data = db.Column(db.Text)

    # Relationships
    applications   = db.relationship('Application', backref='grant', lazy='dynamic',
                                     cascade='all, delete-orphan')
    criteria       = db.relationship('GrantCriteria', backref='grant', lazy='dynamic',
                                     cascade='all, delete-orphan')

    def generate_qr_code(self):
        """Generate QR code for the grant using the council's subdomain URL."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        if self.council and self.council.subdomain:
            qr_data = f"https://{self.council.subdomain}.grantthrive.com/grants/{self.id}"
        else:
            qr_data = f"https://app.grantthrive.com/grants/{self.id}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        self.qr_code_data = base64.b64encode(buffer.getvalue()).decode()

    @property
    def is_open(self):
        now = datetime.now(timezone.utc)
        return (self.status == 'open' and
                self.is_published and
                self.opens_at <= now <= self.closes_at)

    @property
    def days_remaining(self):
        if not self.is_open:
            return 0
        delta = self.closes_at - datetime.now(timezone.utc)
        return max(0, delta.days)

    def __repr__(self):
        return f'<Grant {self.title}>'


class GrantCriteria(db.Model):
    """Grant assessment criteria"""
    __tablename__ = 'grant_criteria'

    id          = db.Column(db.Integer, primary_key=True)
    grant_id    = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    weight      = db.Column(db.Integer, default=1)
    max_score   = db.Column(db.Integer, default=10)
    order       = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<GrantCriteria {self.name}>'


# ── Application ───────────────────────────────────────────────────────────────

class Application(db.Model):
    """Grant application model"""
    __tablename__ = 'applications'

    id           = db.Column(db.Integer, primary_key=True)
    grant_id     = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    organization_name   = db.Column(db.String(200), nullable=False)
    project_title       = db.Column(db.String(200), nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    amount_requested    = db.Column(Numeric(10, 2), nullable=False)

    contact_person = db.Column(db.String(100), nullable=False)
    contact_email  = db.Column(EncryptedString(500), nullable=False)
    contact_phone  = db.Column(EncryptedString(200))

    address   = db.Column(EncryptedString(700))
    postcode  = db.Column(db.String(10))
    latitude  = db.Column(db.Float)
    longitude = db.Column(db.Float)

    status       = db.Column(db.String(20), default='draft')
    submitted_at = db.Column(db.DateTime)
    reviewed_at  = db.Column(db.DateTime)
    decision_date= db.Column(db.DateTime)

    total_score   = db.Column(db.Float)
    average_score = db.Column(db.Float)

    community_votes = db.Column(db.Integer, default=0)
    community_score = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    reviews   = db.relationship('Review', backref='application', lazy='dynamic',
                                cascade='all, delete-orphan')
    documents = db.relationship('ApplicationDocument', backref='application', lazy='dynamic',
                                cascade='all, delete-orphan')
    votes     = db.relationship('CommunityVote', back_populates='application', lazy='dynamic',
                                cascade='all, delete-orphan')

    def calculate_scores(self):
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
        return self.status != 'draft'

    def __repr__(self):
        return f'<Application {self.project_title}>'


class ApplicationDocument(db.Model):
    """Documents attached to applications"""
    __tablename__ = 'application_documents'

    id                  = db.Column(db.Integer, primary_key=True)
    application_id      = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    filename            = db.Column(db.String(255), nullable=False)
    original_filename   = db.Column(db.String(255), nullable=False)
    file_size           = db.Column(db.Integer)
    mime_type           = db.Column(db.String(100))
    uploaded_at         = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ApplicationDocument {self.original_filename}>'


# ── Review ────────────────────────────────────────────────────────────────────

class Review(db.Model):
    """Application review and scoring"""
    __tablename__ = 'reviews'

    id             = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    reviewer_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    is_complete  = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime)

    total_score    = db.Column(db.Float, default=0.0)
    recommendation = db.Column(db.String(20))
    comments       = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    scores = db.relationship('ReviewScore', backref='review', lazy='dynamic',
                             cascade='all, delete-orphan')

    def calculate_total_score(self):
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

    id          = db.Column(db.Integer, primary_key=True)
    review_id   = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=False)
    criteria_id = db.Column(db.Integer, db.ForeignKey('grant_criteria.id'), nullable=False)
    score       = db.Column(db.Float)
    comments    = db.Column(db.Text)

    criteria = db.relationship('GrantCriteria', backref='scores')

    def __repr__(self):
        return f'<ReviewScore {self.score}>'


# ── Community Voting ──────────────────────────────────────────────────────────

class CommunityVote(db.Model):
    """Community voting on applications"""
    __tablename__ = 'community_votes'

    id                 = db.Column(db.Integer, primary_key=True)
    application_id     = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    voter_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    voting_session_id  = db.Column(db.Integer, db.ForeignKey('voting_sessions.id'), nullable=False)

    vote_value = db.Column(db.Integer, nullable=False)
    vote_type  = db.Column(db.String(20), default='rating')
    comments   = db.Column(db.Text)

    voter_email   = db.Column(EncryptedString(500))
    voter_postcode= db.Column(db.String(10))
    voter_name    = db.Column(EncryptedString(300))

    ip_address  = db.Column(db.String(45))
    user_agent  = db.Column(db.String(500))
    is_verified = db.Column(db.Boolean, default=True)
    is_flagged  = db.Column(db.Boolean, default=False)
    flagged_reason = db.Column(db.String(200))

    voted_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    application = db.relationship('Application', back_populates='votes')
    voter       = db.relationship('User', backref='community_votes')

    def __repr__(self):
        return f'<CommunityVote {self.vote_value}>'


class VotingSession(db.Model):
    """Voting sessions for managing community voting periods"""
    __tablename__ = 'voting_sessions'

    id         = db.Column(db.Integer, primary_key=True)
    grant_id   = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)

    # Tenant FK — denormalised for efficient scoping queries
    council_id = db.Column(db.Integer, db.ForeignKey('councils.id'), nullable=False, index=True)

    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    voting_type          = db.Column(db.String(20), default='rating')
    min_vote_value       = db.Column(db.Integer, default=1)
    max_vote_value       = db.Column(db.Integer, default=5)
    allow_comments       = db.Column(db.Boolean, default=True)
    require_registration = db.Column(db.Boolean, default=False)

    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at   = db.Column(db.DateTime, nullable=False)

    is_active    = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)

    total_votes          = db.Column(db.Integer, default=0)
    total_voters         = db.Column(db.Integer, default=0)
    average_participation= db.Column(db.Float, default=0.0)
    voting_weight        = db.Column(db.Float, default=0.2)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    grant   = db.relationship('Grant', backref='voting_sessions')
    creator = db.relationship('User', backref='created_voting_sessions')
    votes   = db.relationship('CommunityVote', backref='voting_session',
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<VotingSession {self.title}>'

    @property
    def is_open(self):
        now = datetime.now(timezone.utc)
        return self.is_active and self.starts_at <= now <= self.ends_at

    @property
    def status(self):
        now = datetime.now(timezone.utc)
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

    id                 = db.Column(db.Integer, primary_key=True)
    application_id     = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    voting_session_id  = db.Column(db.Integer, db.ForeignKey('voting_sessions.id'), nullable=False)

    total_votes   = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    total_score   = db.Column(db.Float, default=0.0)

    votes_1_star  = db.Column(db.Integer, default=0)
    votes_2_star  = db.Column(db.Integer, default=0)
    votes_3_star  = db.Column(db.Integer, default=0)
    votes_4_star  = db.Column(db.Integer, default=0)
    votes_5_star  = db.Column(db.Integer, default=0)

    community_rank    = db.Column(db.Integer)
    percentile        = db.Column(db.Float)
    total_comments    = db.Column(db.Integer, default=0)
    engagement_score  = db.Column(db.Float, default=0.0)

    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                             onupdate=lambda: datetime.now(timezone.utc))

    application    = db.relationship('Application', backref='voting_results')
    voting_session = db.relationship('VotingSession', backref='results')

    def __repr__(self):
        return f'<VotingResult App:{self.application_id} Score:{self.average_score}>'


# ── Workflow ──────────────────────────────────────────────────────────────────

class WorkflowStep(db.Model):
    """Workflow steps for grant processing"""
    __tablename__ = 'workflow_steps'

    id          = db.Column(db.Integer, primary_key=True)
    grant_id    = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order       = db.Column(db.Integer, nullable=False)

    requires_review  = db.Column(db.Boolean, default=False)
    requires_approval= db.Column(db.Boolean, default=False)
    auto_advance     = db.Column(db.Boolean, default=False)
    assigned_users   = db.Column(db.Text)  # JSON list of user IDs

    grant = db.relationship('Grant', backref='workflow_steps')

    def __repr__(self):
        return f'<WorkflowStep {self.name}>'


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLog(db.Model):
    """Audit trail for all system actions"""
    __tablename__ = 'audit_logs'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Tenant FK — NULL for system-level events
    council_id  = db.Column(db.Integer, db.ForeignKey('councils.id'), nullable=True, index=True)

    action      = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id   = db.Column(db.Integer, nullable=False)
    old_values  = db.Column(db.Text)   # JSON
    new_values  = db.Column(db.Text)   # JSON
    ip_address  = db.Column(db.String(45))
    user_agent  = db.Column(db.String(500))
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action}>'


# ── Pricing Configuration ─────────────────────────────────────────────────────
class PricingConfig(db.Model):
    """
    Live pricing configuration for each plan tier.

    System admins can edit these values via the admin dashboard.
    The public /api/pricing/plans endpoint reads from this table so that
    the marketing website always shows current prices.

    Prices are stored in AUD cents (integer) to avoid floating-point issues.
    """
    __tablename__ = 'pricing_config'

    id           = db.Column(db.Integer, primary_key=True)
    plan_key     = db.Column(db.String(20), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)

    # Monthly subscription price (AUD cents)
    monthly_price_aud_cents       = db.Column(db.Integer, nullable=False, default=0)
    # Annual subscription price (AUD cents) — 10 x monthly = 2 months free
    annual_price_aud_cents        = db.Column(db.Integer, nullable=False, default=0)
    # Per-month equivalent when billed annually (for display only)
    annual_monthly_price_aud_cents= db.Column(db.Integer, nullable=False, default=0)

    # Add-on prices (AUD cents per month) — only applicable to 'small' plan
    addon_community_voting_cents  = db.Column(db.Integer, nullable=False, default=5000)
    addon_grant_mapping_cents     = db.Column(db.Integer, nullable=False, default=5000)

    # Audit fields
    updated_at   = db.Column(db.DateTime, nullable=True)
    updated_by   = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<PricingConfig {self.plan_key}>'


# ── Community Forum ───────────────────────────────────────────────────────────

class Forum(db.Model):
    """
    A discussion forum created by council staff to communicate with
    community members.  Forums belong to a council and can be joined
    by any staff member of that council.
    """
    __tablename__ = 'forums'

    id          = db.Column(db.Integer, primary_key=True)
    council_id  = db.Column(db.Integer, db.ForeignKey('councils.id'), nullable=False, index=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public   = db.Column(db.Boolean, default=True, nullable=False)  # visible to community
    is_active   = db.Column(db.Boolean, default=True, nullable=False)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at  = db.Column(db.DateTime, nullable=True)

    council  = db.relationship('Council', backref='forums')
    creator  = db.relationship('User', foreign_keys=[created_by], backref='created_forums')
    posts    = db.relationship('ForumPost', back_populates='forum',
                               order_by='ForumPost.created_at', cascade='all, delete-orphan')
    members  = db.relationship('ForumMember', back_populates='forum',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Forum {self.id} {self.title!r}>'


class ForumPost(db.Model):
    """A message posted in a forum thread."""
    __tablename__ = 'forum_posts'

    id         = db.Column(db.Integer, primary_key=True)
    forum_id   = db.Column(db.Integer, db.ForeignKey('forums.id'), nullable=False, index=True)
    author_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    is_pinned  = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=True)

    forum  = db.relationship('Forum', back_populates='posts')
    author = db.relationship('User', backref='forum_posts')

    def __repr__(self):
        return f'<ForumPost {self.id} forum={self.forum_id}>'


class ForumMember(db.Model):
    """
    Tracks which staff members have joined a forum.
    Community members see public forums without needing to join.
    """
    __tablename__ = 'forum_members'
    __table_args__ = (db.UniqueConstraint('forum_id', 'user_id', name='uq_forum_member'),)

    id         = db.Column(db.Integer, primary_key=True)
    forum_id   = db.Column(db.Integer, db.ForeignKey('forums.id'), nullable=False, index=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    joined_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    forum = db.relationship('Forum', back_populates='members')
    user  = db.relationship('User', backref='forum_memberships')

    def __repr__(self):
        return f'<ForumMember forum={self.forum_id} user={self.user_id}>'


# ── Application Assignment ────────────────────────────────────────────────────

class ApplicationAssignment(db.Model):
    """
    Tracks which staff members are assigned to review a specific application.
    A staff member can recuse themselves so the application can be reassigned.
    """
    __tablename__ = 'application_assignments'
    __table_args__ = (
        db.UniqueConstraint('application_id', 'staff_id', name='uq_app_assignment'),
    )

    id             = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False, index=True)
    staff_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    assigned_by    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # status: 'assigned' | 'recused' | 'completed'
    status         = db.Column(db.String(20), default='assigned', nullable=False)
    notes          = db.Column(db.Text, nullable=True)
    assigned_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at     = db.Column(db.DateTime, nullable=True)

    application  = db.relationship('Application', backref='assignments')
    staff        = db.relationship('User', foreign_keys=[staff_id],  backref='review_assignments')
    assigner     = db.relationship('User', foreign_keys=[assigned_by], backref='assigned_reviews')

    def __repr__(self):
        return f'<ApplicationAssignment app={self.application_id} staff={self.staff_id} status={self.status!r}>'
