from datetime import datetime
from src.models.user import db

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Grant relationship
    grant_id = db.Column(db.Integer, db.ForeignKey('grants.id'), nullable=False)
    
    # Applicant information
    applicant_name = db.Column(db.String(200), nullable=False)
    applicant_email = db.Column(db.String(120), nullable=False)
    applicant_phone = db.Column(db.String(20), nullable=True)
    organization_name = db.Column(db.String(200), nullable=True)
    organization_type = db.Column(db.String(100), nullable=True)  # individual, nonprofit, business, community_group
    abn_acn = db.Column(db.String(50), nullable=True)
    
    # Application details
    project_title = db.Column(db.String(200), nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    requested_amount = db.Column(db.Float, nullable=False)
    project_budget = db.Column(db.Text, nullable=True)  # JSON string
    
    # Timeline
    project_start_date = db.Column(db.Date, nullable=True)
    project_end_date = db.Column(db.Date, nullable=True)
    
    # Status and workflow
    status = db.Column(db.String(50), nullable=False, default='submitted')  # submitted, under_review, approved, rejected, withdrawn
    priority = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, urgent
    
    # Dates
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    decision_date = db.Column(db.DateTime, nullable=True)
    
    # Assessment
    score = db.Column(db.Float, nullable=True)
    reviewer_notes = db.Column(db.Text, nullable=True)
    public_notes = db.Column(db.Text, nullable=True)
    
    # Documents and attachments
    documents = db.Column(db.Text, nullable=True)  # JSON string of file paths/URLs
    
    # Community engagement
    community_support = db.Column(db.Integer, default=0)  # Number of community endorsements
    public_comments = db.Column(db.Text, nullable=True)
    
    # Financial tracking
    approved_amount = db.Column(db.Float, nullable=True)
    paid_amount = db.Column(db.Float, default=0.0)
    payment_schedule = db.Column(db.Text, nullable=True)  # JSON string
    
    # Compliance and reporting
    reporting_requirements = db.Column(db.Text, nullable=True)
    compliance_status = db.Column(db.String(50), default='pending')  # pending, compliant, non_compliant
    
    def to_dict(self):
        return {
            'id': self.id,
            'grant_id': self.grant_id,
            'applicant_name': self.applicant_name,
            'applicant_email': self.applicant_email,
            'applicant_phone': self.applicant_phone,
            'organization_name': self.organization_name,
            'organization_type': self.organization_type,
            'abn_acn': self.abn_acn,
            'project_title': self.project_title,
            'project_description': self.project_description,
            'requested_amount': self.requested_amount,
            'project_budget': self.project_budget,
            'project_start_date': self.project_start_date.isoformat() if self.project_start_date else None,
            'project_end_date': self.project_end_date.isoformat() if self.project_end_date else None,
            'status': self.status,
            'priority': self.priority,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'decision_date': self.decision_date.isoformat() if self.decision_date else None,
            'score': self.score,
            'reviewer_notes': self.reviewer_notes,
            'public_notes': self.public_notes,
            'documents': self.documents,
            'community_support': self.community_support,
            'public_comments': self.public_comments,
            'approved_amount': self.approved_amount,
            'paid_amount': self.paid_amount,
            'payment_schedule': self.payment_schedule,
            'reporting_requirements': self.reporting_requirements,
            'compliance_status': self.compliance_status
        }
    
    def __repr__(self):
        return f'<Application {self.project_title} for Grant {self.grant_id}>'

