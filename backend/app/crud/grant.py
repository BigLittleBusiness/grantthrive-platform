"""
GrantThrive Grant CRUD Operations
Enterprise-grade database operations for grant management
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime
from ..models.grant import Grant, Application, GrantStatus, ApplicationStatus, GrantCategory
from ..schemas.grant import GrantCreate, GrantUpdate, ApplicationCreate, ApplicationUpdate


def get_grant(db: Session, grant_id: int) -> Optional[Grant]:
    """Get grant by ID"""
    return db.query(Grant).filter(Grant.id == grant_id).first()


def get_grant_by_slug(db: Session, slug: str) -> Optional[Grant]:
    """Get grant by slug"""
    return db.query(Grant).filter(Grant.slug == slug).first()


def get_grants(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[GrantStatus] = None,
    category: Optional[GrantCategory] = None,
    organization_id: Optional[int] = None,
    search: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_open: Optional[bool] = None
) -> List[Grant]:
    """Get grants with filtering and pagination"""
    query = db.query(Grant)
    
    # Apply filters
    if status:
        query = query.filter(Grant.status == status)
    if category:
        query = query.filter(Grant.category == category)
    if organization_id:
        query = query.filter(Grant.organization_id == organization_id)
    if is_featured is not None:
        query = query.filter(Grant.is_featured == is_featured)
    if search:
        search_filter = or_(
            Grant.title.ilike(f"%{search}%"),
            Grant.description.ilike(f"%{search}%"),
            Grant.organization_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Filter for open grants
    if is_open is not None:
        now = datetime.utcnow()
        if is_open:
            query = query.filter(
                and_(
                    Grant.status == GrantStatus.PUBLISHED,
                    Grant.application_open_date <= now,
                    Grant.application_close_date >= now
                )
            )
        else:
            query = query.filter(
                or_(
                    Grant.status != GrantStatus.PUBLISHED,
                    Grant.application_open_date > now,
                    Grant.application_close_date < now
                )
            )
    
    return query.order_by(desc(Grant.created_at)).offset(skip).limit(limit).all()


def create_grant(db: Session, grant: GrantCreate, creator_id: int) -> Grant:
    """Create new grant"""
    # Generate slug from title
    import re
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', grant.title.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    
    # Ensure slug is unique
    base_slug = slug
    counter = 1
    while get_grant_by_slug(db, slug):
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    db_grant = Grant(
        title=grant.title,
        slug=slug,
        description=grant.description,
        objectives=grant.objectives,
        eligibility_criteria=grant.eligibility_criteria,
        application_guidelines=grant.application_guidelines,
        total_funding=grant.total_funding,
        min_amount=grant.min_amount,
        max_amount=grant.max_amount,
        category=grant.category,
        tags=grant.tags,
        application_open_date=grant.application_open_date,
        application_close_date=grant.application_close_date,
        decision_date=grant.decision_date,
        project_start_date=grant.project_start_date,
        project_end_date=grant.project_end_date,
        organization_id=grant.organization_id,
        organization_name=grant.organization_name,
        contact_email=grant.contact_email,
        contact_phone=grant.contact_phone,
        contact_person=grant.contact_person,
        required_documents=grant.required_documents,
        application_form_fields=grant.application_form_fields,
        created_by=creator_id
    )
    
    db.add(db_grant)
    db.commit()
    db.refresh(db_grant)
    return db_grant


def update_grant(db: Session, grant_id: int, grant_update: GrantUpdate) -> Optional[Grant]:
    """Update grant information"""
    db_grant = get_grant(db, grant_id)
    if not db_grant:
        return None
    
    update_data = grant_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_grant, field, value)
    
    db.commit()
    db.refresh(db_grant)
    return db_grant


def delete_grant(db: Session, grant_id: int) -> bool:
    """Delete grant (soft delete by setting status to archived)"""
    db_grant = get_grant(db, grant_id)
    if not db_grant:
        return False
    
    db_grant.status = GrantStatus.ARCHIVED
    db.commit()
    return True


def get_grants_count(
    db: Session,
    status: Optional[GrantStatus] = None,
    category: Optional[GrantCategory] = None,
    organization_id: Optional[int] = None
) -> int:
    """Get total count of grants with filters"""
    query = db.query(Grant)
    
    if status:
        query = query.filter(Grant.status == status)
    if category:
        query = query.filter(Grant.category == category)
    if organization_id:
        query = query.filter(Grant.organization_id == organization_id)
    
    return query.count()


def get_organization_grants(db: Session, organization_id: int) -> List[Grant]:
    """Get all grants belonging to an organization"""
    return db.query(Grant).filter(Grant.organization_id == organization_id).all()


# Application CRUD operations
def get_application(db: Session, application_id: int) -> Optional[Application]:
    """Get application by ID"""
    return db.query(Application).filter(Application.id == application_id).first()


def get_application_by_reference(db: Session, reference_number: str) -> Optional[Application]:
    """Get application by reference number"""
    return db.query(Application).filter(Application.reference_number == reference_number).first()


def get_applications(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ApplicationStatus] = None,
    grant_id: Optional[int] = None,
    applicant_id: Optional[int] = None,
    organization_id: Optional[int] = None
) -> List[Application]:
    """Get applications with filtering and pagination"""
    query = db.query(Application)
    
    # Apply filters
    if status:
        query = query.filter(Application.status == status)
    if grant_id:
        query = query.filter(Application.grant_id == grant_id)
    if applicant_id:
        query = query.filter(Application.applicant_id == applicant_id)
    if organization_id:
        # Filter by grants from specific organization
        query = query.join(Grant).filter(Grant.organization_id == organization_id)
    
    return query.order_by(desc(Application.created_at)).offset(skip).limit(limit).all()


def create_application(db: Session, application: ApplicationCreate, applicant_id: int) -> Application:
    """Create new grant application"""
    # Generate reference number
    from datetime import datetime
    year = datetime.now().year
    
    db_application = Application(
        project_title=application.project_title,
        project_description=application.project_description,
        requested_amount=application.requested_amount,
        project_duration=application.project_duration,
        applicant_id=applicant_id,
        organization_name=application.organization_name,
        abn_acn=application.abn_acn,
        grant_id=application.grant_id,
        form_data=application.form_data,
        documents=application.documents
    )
    
    db.add(db_application)
    db.flush()  # Get the ID without committing
    
    # Generate reference number with ID
    reference_number = f"GT{year}{application.grant_id:04d}{db_application.id:06d}"
    db_application.reference_number = reference_number
    
    db.commit()
    db.refresh(db_application)
    return db_application


def update_application(db: Session, application_id: int, application_update: ApplicationUpdate) -> Optional[Application]:
    """Update application information"""
    db_application = get_application(db, application_id)
    if not db_application:
        return None
    
    update_data = application_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_application, field, value)
    
    db.commit()
    db.refresh(db_application)
    return db_application


def submit_application(db: Session, application_id: int) -> Optional[Application]:
    """Submit application for review"""
    db_application = get_application(db, application_id)
    if not db_application:
        return None
    
    if db_application.status != ApplicationStatus.DRAFT:
        return None  # Can only submit draft applications
    
    db_application.status = ApplicationStatus.SUBMITTED
    db_application.submitted_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_application)
    return db_application


def review_application(
    db: Session, 
    application_id: int, 
    reviewer_id: int, 
    status: ApplicationStatus,
    reviewer_notes: Optional[str] = None,
    feedback: Optional[str] = None,
    score: Optional[int] = None
) -> Optional[Application]:
    """Review application and update status"""
    db_application = get_application(db, application_id)
    if not db_application:
        return None
    
    db_application.status = status
    db_application.reviewed_at = datetime.utcnow()
    db_application.reviewed_by = reviewer_id
    db_application.reviewer_notes = reviewer_notes
    db_application.feedback = feedback
    db_application.score = score
    
    db.commit()
    db.refresh(db_application)
    return db_application


def get_applications_count(
    db: Session,
    status: Optional[ApplicationStatus] = None,
    grant_id: Optional[int] = None,
    applicant_id: Optional[int] = None,
    organization_id: Optional[int] = None
) -> int:
    """Get total count of applications with filters"""
    query = db.query(Application)
    
    if status:
        query = query.filter(Application.status == status)
    if grant_id:
        query = query.filter(Application.grant_id == grant_id)
    if applicant_id:
        query = query.filter(Application.applicant_id == applicant_id)
    if organization_id:
        query = query.join(Grant).filter(Grant.organization_id == organization_id)
    
    return query.count()


def get_user_applications(db: Session, user_id: int) -> List[Application]:
    """Get all applications by a specific user"""
    return db.query(Application).filter(Application.applicant_id == user_id).all()


def get_grant_applications(db: Session, grant_id: int) -> List[Application]:
    """Get all applications for a specific grant"""
    return db.query(Application).filter(Application.grant_id == grant_id).all()

