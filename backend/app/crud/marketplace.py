"""
GrantThrive Marketplace CRUD Operations
Database operations for professional services marketplace
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.sql import func as sql_func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.marketplace import (
    ProfessionalProfile, ProfessionalService, ServiceBooking, ProfessionalReview
)
from ..schemas.marketplace import (
    ProfessionalProfileCreate, ProfessionalProfileUpdate,
    ProfessionalServiceCreate, ProfessionalServiceUpdate,
    ServiceBookingCreate, ServiceBookingUpdate,
    ProfessionalReviewCreate
)


# Professional Profile CRUD
def create_professional_profile(
    db: Session, 
    profile: ProfessionalProfileCreate, 
    user_id: int, 
    organization_id: int
) -> ProfessionalProfile:
    """Create professional profile"""
    db_profile = ProfessionalProfile(
        **profile.model_dump(),
        user_id=user_id,
        organization_id=organization_id,
        status="pending"
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def get_professional_profiles(
    db: Session,
    organization_id: int,
    status: Optional[str] = "approved",
    specialization: Optional[str] = None,
    location: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> List[ProfessionalProfile]:
    """Get professional profiles"""
    query = db.query(ProfessionalProfile).filter(
        ProfessionalProfile.organization_id == organization_id
    )
    
    if status:
        query = query.filter(ProfessionalProfile.status == status)
    
    if specialization:
        query = query.filter(ProfessionalProfile.specializations.contains([specialization]))
    
    if location:
        query = query.filter(
            or_(
                ProfessionalProfile.location.ilike(f"%{location}%"),
                ProfessionalProfile.serves_remote == True
            )
        )
    
    return query.order_by(desc(ProfessionalProfile.created_at)).offset(skip).limit(limit).all()

def get_profile_by_id(db: Session, profile_id: int) -> Optional[ProfessionalProfile]:
    """Get profile by ID"""
    return db.query(ProfessionalProfile).filter(ProfessionalProfile.id == profile_id).first()

def update_professional_profile(
    db: Session, 
    profile_id: int, 
    profile_update: ProfessionalProfileUpdate
) -> Optional[ProfessionalProfile]:
    """Update professional profile"""
    profile = db.query(ProfessionalProfile).filter(ProfessionalProfile.id == profile_id).first()
    if not profile:
        return None
    
    for field, value in profile_update.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile

def approve_professional_profile(
    db: Session, 
    profile_id: int, 
    approved: bool, 
    reviewer_id: int, 
    feedback: Optional[str] = None
) -> Optional[ProfessionalProfile]:
    """Approve or reject professional profile"""
    profile = db.query(ProfessionalProfile).filter(ProfessionalProfile.id == profile_id).first()
    if not profile:
        return None
    
    profile.status = "approved" if approved else "rejected"
    profile.reviewed_by = reviewer_id
    profile.reviewed_at = datetime.utcnow()
    if feedback:
        profile.review_feedback = feedback
    
    db.commit()
    db.refresh(profile)
    return profile

# Service Listing CRUD
def create_service_listing(
    db: Session, 
    service: ProfessionalServiceCreate, 
    professional_id: int
) -> ProfessionalService:
    """Create service listing"""
    db_service = ProfessionalService(
        **service.model_dump(),
        professional_id=professional_id
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def get_service_listings(
    db: Session,
    organization_id: int,
    category: Optional[str] = None,
    pricing_model: Optional[str] = None,
    location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 20
) -> List[ProfessionalService]:
    """Get service listings"""
    query = db.query(ProfessionalService).join(ProfessionalProfile).filter(
        ProfessionalProfile.organization_id == organization_id,
        ProfessionalService.is_active == is_active
    )
    
    if category:
        query = query.filter(ProfessionalService.category == category)
    
    if pricing_model:
        query = query.filter(ProfessionalService.pricing_model == pricing_model)
    
    if location:
        query = query.filter(
            or_(
                ProfessionalService.location.ilike(f"%{location}%"),
                ProfessionalService.remote_available == True
            )
        )
    
    if min_price is not None:
        query = query.filter(ProfessionalService.base_price >= min_price)
    
    if max_price is not None:
        query = query.filter(ProfessionalService.base_price <= max_price)
    
    return query.order_by(desc(ProfessionalService.created_at)).offset(skip).limit(limit).all()

def get_service_by_id(db: Session, service_id: int) -> Optional[ProfessionalService]:
    """Get service by ID"""
    return db.query(ProfessionalService).filter(ProfessionalService.id == service_id).first()

def update_service_listing(
    db: Session, 
    service_id: int, 
    service_update: ProfessionalServiceUpdate
) -> Optional[ProfessionalService]:
    """Update service listing"""
    service = db.query(ProfessionalService).filter(ProfessionalService.id == service_id).first()
    if not service:
        return None
    
    for field, value in service_update.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    
    service.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(service)
    return service

def delete_service_listing(db: Session, service_id: int) -> bool:
    """Delete service listing"""
    service = db.query(ProfessionalService).filter(ProfessionalService.id == service_id).first()
    if service:
        db.delete(service)
        db.commit()
        return True
    return False

# ServiceBooking CRUD
def create_booking(db: Session, booking: ServiceBookingCreate, client_id: int) -> ServiceBooking:
    """Create booking"""
    # Generate unique booking reference
    import uuid
    booking_reference = f"BK-{uuid.uuid4().hex[:8].upper()}"
    
    db_booking = ServiceBooking(
        **booking.model_dump(),
        client_id=client_id,
        booking_reference=booking_reference,
        status="pending"
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_bookings(
    db: Session,
    user_id: int,
    as_client: bool = True,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[ServiceBooking]:
    """Get user bookings"""
    if as_client:
        query = db.query(ServiceBooking).filter(ServiceBooking.client_id == user_id)
    else:
        query = db.query(ServiceBooking).filter(ServiceBooking.professional_id == user_id)
    
    if status:
        query = query.filter(ServiceBooking.status == status)
    
    return query.order_by(desc(ServiceBooking.created_at)).offset(skip).limit(limit).all()

def get_booking_by_id(db: Session, booking_id: int) -> Optional[ServiceBooking]:
    """Get booking by ID"""
    return db.query(ServiceBooking).filter(ServiceBooking.id == booking_id).first()

def update_booking_status(
    db: Session, 
    booking_id: int, 
    status: str, 
    notes: Optional[str] = None
) -> Optional[ServiceBooking]:
    """Update booking status"""
    booking = db.query(ServiceBooking).filter(ServiceBooking.id == booking_id).first()
    if not booking:
        return None
    
    booking.status = status
    if notes:
        booking.notes = notes
    booking.updated_at = datetime.utcnow()
    
    # Set completion date if completed
    if status == "completed":
        booking.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(booking)
    return booking

# Review CRUD
def create_service_review(
    db: Session, 
    review: ProfessionalReviewCreate, 
    reviewer_id: int
) -> ProfessionalReview:
    """Create service review"""
    db_review = ProfessionalReview(
        **review.model_dump(),
        reviewer_id=reviewer_id
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Update service rating
    _update_service_rating(db, review.service_id)
    
    return db_review

def get_service_reviews(
    db: Session, 
    service_id: int, 
    skip: int = 0, 
    limit: int = 20
) -> List[ProfessionalReview]:
    """Get reviews for a service"""
    return db.query(ProfessionalReview).filter(
        ProfessionalReview.service_id == service_id
    ).order_by(desc(ProfessionalReview.created_at)).offset(skip).limit(limit).all()

def get_professional_reviews(
    db: Session, 
    professional_id: int, 
    skip: int = 0, 
    limit: int = 20
) -> List[ProfessionalReview]:
    """Get reviews for a professional"""
    return db.query(ProfessionalReview).join(ProfessionalService).filter(
        ProfessionalService.professional_id == professional_id
    ).order_by(desc(ProfessionalReview.created_at)).offset(skip).limit(limit).all()

def _update_service_rating(db: Session, service_id: int):
    """Update service average rating"""
    avg_rating = db.query(func.avg(ProfessionalReview.overall_rating)).filter(
        ProfessionalReview.service_id == service_id
    ).scalar()
    
    review_count = db.query(func.count(ProfessionalReview.id)).filter(
        ProfessionalReview.service_id == service_id
    ).scalar()
    
    service = db.query(ProfessionalService).filter(ProfessionalService.id == service_id).first()
    if service:
        service.average_rating = float(avg_rating) if avg_rating else 0.0
        service.review_count = review_count or 0
        db.commit()

# Statistics
def get_marketplace_stats(db: Session, organization_id: int) -> Dict[str, Any]:
    """Get marketplace statistics"""
    # Professional profiles
    total_professionals = db.query(ProfessionalProfile).filter(
        ProfessionalProfile.organization_id == organization_id,
        ProfessionalProfile.status == "approved"
    ).count()
    
    # Active services
    active_services = db.query(ProfessionalService).join(ProfessionalProfile).filter(
        ProfessionalProfile.organization_id == organization_id,
        ProfessionalService.is_active == True
    ).count()
    
    # Bookings
    total_bookings = db.query(ServiceBooking).join(ProfessionalService).join(ProfessionalProfile).filter(
        ProfessionalProfile.organization_id == organization_id
    ).count()
    
    completed_bookings = db.query(ServiceBooking).join(ProfessionalService).join(ProfessionalProfile).filter(
        ProfessionalProfile.organization_id == organization_id,
        ServiceBooking.status == "completed"
    ).count()
    
    # Reviews
    total_reviews = db.query(ProfessionalReview).join(ProfessionalService).join(ProfessionalProfile).filter(
        ProfessionalProfile.organization_id == organization_id
    ).count()
    
    avg_rating = db.query(func.avg(ProfessionalReview.overall_rating)).join(ProfessionalService).join(ProfessionalProfile).filter(
        ProfessionalProfile.organization_id == organization_id
    ).scalar()
    
    return {
        "total_professionals": total_professionals,
        "active_services": active_services,
        "total_bookings": total_bookings,
        "completed_bookings": completed_bookings,
        "completion_rate": (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0,
        "total_reviews": total_reviews,
        "average_rating": float(avg_rating) if avg_rating else 0.0
    }

