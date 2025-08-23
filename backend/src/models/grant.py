from datetime import datetime
from src.models.user import db

class Grant(db.Model):
    __tablename__ = 'grants'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='draft')  # draft, active, closed, cancelled
    
    # Dates
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    opens_at = db.Column(db.DateTime, nullable=True)
    closes_at = db.Column(db.DateTime, nullable=True)
    
    # Requirements and criteria
    eligibility_criteria = db.Column(db.Text, nullable=True)
    required_documents = db.Column(db.Text, nullable=True)  # JSON string
    assessment_criteria = db.Column(db.Text, nullable=True)
    
    # Council information
    council_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    
    # Settings
    max_applications = db.Column(db.Integer, nullable=True)
    auto_approve = db.Column(db.Boolean, default=False)
    public_voting = db.Column(db.Boolean, default=False)
    
    # Relationships
    council = db.relationship('User', backref=db.backref('grants', lazy=True))
    applications = db.relationship('Application', backref='grant', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'amount': self.amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'opens_at': self.opens_at.isoformat() if self.opens_at else None,
            'closes_at': self.closes_at.isoformat() if self.closes_at else None,
            'eligibility_criteria': self.eligibility_criteria,
            'required_documents': self.required_documents,
            'assessment_criteria': self.assessment_criteria,
            'council_id': self.council_id,
            'contact_person': self.contact_person,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'max_applications': self.max_applications,
            'auto_approve': self.auto_approve,
            'public_voting': self.public_voting,
            'application_count': len(self.applications) if self.applications else 0
        }
    
    def __repr__(self):
        return f'<Grant {self.title}>'

