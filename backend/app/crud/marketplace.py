"""
GrantThrive Professional Services Marketplace CRUD Operations
Database operations for professional services marketplace
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from ..models.marketplace import (
    ProfessionalProfile, ProfessionalService, ServiceBooking, 
    BookingMessage, ProfessionalReview, ProfessionalDocument,
    ApplicationStatus, BookingStatus, ServiceCategory
)
from ..schemas.marketplace import (
    ProfessionalProfileCreate, ProfessionalProfileUpdate,
    ProfessionalServiceCreate, ProfessionalServiceUpdate,
    ServiceBookingCreate, ServiceBookingUpdate,
    BookingMessageCreate, ProfessionalReviewCreate, ProfessionalReviewUpdate,
    ProfessionalDocumentCreate, ProfessionalApplicationReview
)


# Professional Profile CRUD
def create_professional_profile(
    db: Session, 
    profile: ProfessionalProfileCreate, 
    user_id: int
) -> ProfessionalProfile:
    """Create a new professional profile"""
    db_profile = ProfessionalProfile(
        **profile.model_dump(),
        user_id=user_id,
        application_status=ApplicationStatus.PENDING
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def get_professional_profiles(
    db: Session,
    status: Optional[ApplicationStatus] = None,
    is_active: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    category: Optional[ServiceCategory] = None,
    location: Optional[str] = None,
    remote_services: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> List[ProfessionalProfile]:
    """Get professional profiles with filters"""
    query = db.query(ProfessionalProfile)
    
    if status:
        query = query.filter(ProfessionalProfile.application_status == status)
    
    if is_active is not None:
        query = query.filter(ProfessionalProfile.is_active == is_active)
    
    if is_featured is not None:
        query = query.filter(ProfessionalProfile.is_featured == is_featured)
    
    if location:
        query = query.filter(
            or_(
                ProfessionalProfile.city.contains(location),
                ProfessionalProfile.state.contains(location)
            )
        )
    
    if remote_services is not None:
        query = query.filter(ProfessionalProfile.remote_services == remote_services)
    
    if search:
        query = query.filter(
            or_(
                ProfessionalProfile.title.contains(search),
                ProfessionalProfile.bio.contains(search),
                ProfessionalProfile.business_name.contains(search)
            )
        )
    
    # Filter by service category if specified
    if category:
        query = query.join(ProfessionalService).filter(
            ProfessionalService.category == category
        )
    
    return query.order_by(
        desc(ProfessionalProfile.is_featured),
        desc(ProfessionalProfile.average_rating),
        desc(ProfessionalProfile.total_reviews)
    ).offset(skip).limit(limit).all()


def get_professional_profile(db: Session, profile_id: int) -> Optional[ProfessionalProfile]:
    """Get professional profile by ID"""
    return db.query(ProfessionalProfile).filter(ProfessionalProfile.id == profile_id).first()


def get_professional_profile_by_user(db: Session, user_id: int) -> Optional[ProfessionalProfile]:
    """Get professional profile by user ID"""
    return db.query(ProfessionalProfile).filter(ProfessionalProfile.user_id == user_id).first()


def update_professional_profile(
    db: Session,
    profile_id: int,
    profile_update: ProfessionalProfileUpdate
) -> Optional[ProfessionalProfile]:
    """Update professional profile"""
    db_profile = get_professional_profile(db, profile_id)
    if not db_profile:
        return None
    
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_profile, field, value)
    
    db_profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_profile)
    return db_profile


def review_professional_application(
    db: Session,
    profile_id: int,
    review: ProfessionalApplicationReview,
    reviewer_id: int
) -> Optional[ProfessionalProfile]:
    """Review professional application"""
    db_profile = get_professional_profile(db, profile_id)
    if not db_profile:
        return None
    
    db_profile.application_status = review.status
    if review.status == ApplicationStatus.APPROVED:
        db_profile.approval_date = datetime.utcnow()
        db_profile.approved_by = reviewer_id
        db_profile.is_active = True
    elif review.status == ApplicationStatus.REJECTED:
        db_profile.rejection_reason = review.rejection_reason
    
    db.commit()
    db.refresh(db_profile)
    return db_profile


# Professional Service CRUD
def create_professional_service(
    db: Session,
    service: ProfessionalServiceCreate,
    professional_id: int
) -> ProfessionalService:
    """Create a new professional service"""
    db_service = ProfessionalService(
        **service.model_dump(),
        professional_id=professional_id
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


def get_professional_services(
    db: Session,
    professional_id: Optional[int] = None,
    category: Optional[ServiceCategory] = None,
    is_active: bool = True,
    is_featured: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> List[ProfessionalService]:
    """Get professional services with filters"""
    query = db.query(ProfessionalService).filter(ProfessionalService.is_active == is_active)
    
    if professional_id:
        query = query.filter(ProfessionalService.professional_id == professional_id)
    
    if category:
        query = query.filter(ProfessionalService.category == category)
    
    if is_featured is not None:
        query = query.filter(ProfessionalService.is_featured == is_featured)
    
    if search:
        query = query.filter(
            or_(
                ProfessionalService.title.contains(search),
                ProfessionalService.description.contains(search)
            )
        )
    
    return query.order_by(
        desc(ProfessionalService.is_featured),
        desc(ProfessionalService.average_rating),
        desc(ProfessionalService.booking_count)
    ).offset(skip).limit(limit).all()


def get_professional_service(db: Session, service_id: int) -> Optional[ProfessionalService]:
    """Get professional service by ID"""
    return db.query(ProfessionalService).filter(ProfessionalService.id == service_id).first()


def update_professional_service(
    db: Session,
    service_id: int,
    service_update: ProfessionalServiceUpdate
) -> Optional[ProfessionalService]:
    """Update professional service"""
    db_service = get_professional_service(db, service_id)
    if not db_service:
        return None
    
    update_data = service_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_service, field, value)
    
    db_service.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_service)
    return db_service


# Service Booking CRUD
def create_service_booking(
    db: Session,
    booking: ServiceBookingCreate,
    client_id: int
) -> ServiceBooking:
    """Create a new service booking"""
    # Get service and professional info
    service = get_professional_service(db, booking.service_id)
    if not service:
        raise ValueError("Service not found")
    
    # Generate unique booking reference
    booking_reference = f"BK{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
    
    db_booking = ServiceBooking(
        **booking.model_dump(),
        booking_reference=booking_reference,
        client_id=client_id,
        professional_id=service.professional_id,
        status=BookingStatus.PENDING
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    # Update service booking count
    service.booking_count += 1
    db.commit()
    
    return db_booking


def get_service_bookings(
    db: Session,
    client_id: Optional[int] = None,
    professional_id: Optional[int] = None,
    service_id: Optional[int] = None,
    status: Optional[BookingStatus] = None,
    skip: int = 0,
    limit: int = 20
) -> List[ServiceBooking]:
    """Get service bookings with filters"""
    query = db.query(ServiceBooking)
    
    if client_id:
        query = query.filter(ServiceBooking.client_id == client_id)
    
    if professional_id:
        query = query.filter(ServiceBooking.professional_id == professional_id)
    
    if service_id:
        query = query.filter(ServiceBooking.service_id == service_id)
    
    if status:
        query = query.filter(ServiceBooking.status == status)
    
    return query.order_by(desc(ServiceBooking.created_at)).offset(skip).limit(limit).all()


def get_service_booking(db: Session, booking_id: int) -> Optional[ServiceBooking]:
    """Get service booking by ID"""
    return db.query(ServiceBooking).filter(ServiceBooking.id == booking_id).first()


def get_service_booking_by_reference(db: Session, booking_reference: str) -> Optional[ServiceBooking]:
    """Get service booking by reference"""
    return db.query(ServiceBooking).filter(ServiceBooking.booking_reference == booking_reference).first()


def update_service_booking(
    db: Session,
    booking_id: int,
    booking_update: ServiceBookingUpdate
) -> Optional[ServiceBooking]:
    """Update service booking"""
    db_booking = get_service_booking(db, booking_id)
    if not db_booking:
        return None
    
    update_data = booking_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_booking, field, value)
    
    db_booking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_booking)
    return db_booking


# Booking Message CRUD
def create_booking_message(
    db: Session,
    booking_id: int,
    message: BookingMessageCreate,
    sender_id: int
) -> BookingMessage:
    """Create a new booking message"""
    db_message = BookingMessage(
        **message.model_dump(),
        booking_id=booking_id,
        sender_id=sender_id
    )
    db.add(db_message)
    
    # Update booking last message time and unread counts
    booking = get_service_booking(db, booking_id)
    if booking:
        booking.last_message_at = datetime.utcnow()
        if sender_id == booking.client_id:
            booking.unread_messages_professional += 1
        else:
            booking.unread_messages_client += 1
    
    db.commit()
    db.refresh(db_message)
    return db_message


def get_booking_messages(
    db: Session,
    booking_id: int,
    skip: int = 0,
    limit: int = 50
) -> List[BookingMessage]:
    """Get messages for a booking"""
    return db.query(BookingMessage).filter(
        BookingMessage.booking_id == booking_id
    ).order_by(BookingMessage.created_at).offset(skip).limit(limit).all()


def mark_messages_as_read(
    db: Session,
    booking_id: int,
    user_id: int
) -> None:
    """Mark messages as read for a user"""
    # Mark messages as read
    db.query(BookingMessage).filter(
        and_(
            BookingMessage.booking_id == booking_id,
            BookingMessage.sender_id != user_id,
            BookingMessage.is_read == False
        )
    ).update({"is_read": True})
    
    # Reset unread count
    booking = get_service_booking(db, booking_id)
    if booking:
        if user_id == booking.client_id:
            booking.unread_messages_client = 0
        else:
            booking.unread_messages_professional = 0
    
    db.commit()


# Professional Review CRUD
def create_professional_review(
    db: Session,
    review: ProfessionalReviewCreate,
    booking_id: int,
    reviewer_id: int
) -> ProfessionalReview:
    """Create a new professional review"""
    # Get booking info
    booking = get_service_booking(db, booking_id)
    if not booking:
        raise ValueError("Booking not found")
    
    db_review = ProfessionalReview(
        **review.model_dump(),
        professional_id=booking.professional_id,
        booking_id=booking_id,
        reviewer_id=reviewer_id
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Update professional rating statistics
    update_professional_rating_stats(db, booking.professional_id)
    
    return db_review


def get_professional_reviews(
    db: Session,
    professional_id: int,
    is_approved: bool = True,
    skip: int = 0,
    limit: int = 20
) -> List[ProfessionalReview]:
    """Get reviews for a professional"""
    return db.query(ProfessionalReview).filter(
        and_(
            ProfessionalReview.professional_id == professional_id,
            ProfessionalReview.is_approved == is_approved
        )
    ).order_by(desc(ProfessionalReview.created_at)).offset(skip).limit(limit).all()


def update_professional_review_response(
    db: Session,
    review_id: int,
    response: ProfessionalReviewUpdate
) -> Optional[ProfessionalReview]:
    """Update professional review with response"""
    db_review = db.query(ProfessionalReview).filter(ProfessionalReview.id == review_id).first()
    if not db_review:
        return None
    
    db_review.professional_response = response.professional_response
    db_review.response_date = datetime.utcnow()
    db_review.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_review)
    return db_review


def update_professional_rating_stats(db: Session, professional_id: int) -> None:
    """Update professional rating statistics"""
    # Calculate average rating and review count
    stats = db.query(
        func.avg(ProfessionalReview.overall_rating).label('avg_rating'),
        func.count(ProfessionalReview.id).label('review_count')
    ).filter(
        and_(
            ProfessionalReview.professional_id == professional_id,
            ProfessionalReview.is_approved == True
        )
    ).first()
    
    # Update professional profile
    professional = get_professional_profile(db, professional_id)
    if professional:
        professional.average_rating = float(stats.avg_rating) if stats.avg_rating else 0.0
        professional.total_reviews = stats.review_count
        db.commit()


# Professional Document CRUD
def create_professional_document(
    db: Session,
    document: ProfessionalDocumentCreate,
    professional_id: int,
    file_url: str,
    file_name: str,
    file_size: int,
    mime_type: str
) -> ProfessionalDocument:
    """Create a new professional document"""
    db_document = ProfessionalDocument(
        **document.model_dump(),
        professional_id=professional_id,
        file_url=file_url,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_professional_documents(
    db: Session,
    professional_id: int,
    document_type: Optional[str] = None,
    is_verified: Optional[bool] = None
) -> List[ProfessionalDocument]:
    """Get documents for a professional"""
    query = db.query(ProfessionalDocument).filter(
        ProfessionalDocument.professional_id == professional_id
    )
    
    if document_type:
        query = query.filter(ProfessionalDocument.document_type == document_type)
    
    if is_verified is not None:
        query = query.filter(ProfessionalDocument.is_verified == is_verified)
    
    return query.order_by(desc(ProfessionalDocument.created_at)).all()


def verify_professional_document(
    db: Session,
    document_id: int,
    verifier_id: int,
    verification_notes: Optional[str] = None
) -> Optional[ProfessionalDocument]:
    """Verify a professional document"""
    db_document = db.query(ProfessionalDocument).filter(ProfessionalDocument.id == document_id).first()
    if not db_document:
        return None
    
    db_document.is_verified = True
    db_document.verified_by = verifier_id
    db_document.verified_at = datetime.utcnow()
    db_document.verification_notes = verification_notes
    db_document.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_document)
    return db_document


# Statistics and Analytics
def get_marketplace_stats(db: Session) -> Dict[str, Any]:
    """Get marketplace statistics"""
    # Professional stats
    total_professionals = db.query(ProfessionalProfile).count()
    active_professionals = db.query(ProfessionalProfile).filter(
        and_(
            ProfessionalProfile.is_active == True,
            ProfessionalProfile.application_status == ApplicationStatus.APPROVED
        )
    ).count()
    pending_applications = db.query(ProfessionalProfile).filter(
        ProfessionalProfile.application_status == ApplicationStatus.PENDING
    ).count()
    
    # Service stats
    total_services = db.query(ProfessionalService).filter(ProfessionalService.is_active == True).count()
    
    # Booking stats
    total_bookings = db.query(ServiceBooking).count()
    completed_bookings = db.query(ServiceBooking).filter(
        ServiceBooking.status == BookingStatus.COMPLETED
    ).count()
    
    # Average rating
    avg_rating = db.query(func.avg(ProfessionalProfile.average_rating)).filter(
        ProfessionalProfile.total_reviews > 0
    ).scalar() or 0.0
    
    # Category breakdown
    category_stats = db.query(
        ProfessionalService.category,
        func.count(ProfessionalService.id).label('count')
    ).filter(ProfessionalService.is_active == True).group_by(ProfessionalService.category).all()
    
    categories_count = {category: count for category, count in category_stats}
    
    return {
        "total_professionals": total_professionals,
        "active_professionals": active_professionals,
        "pending_applications": pending_applications,
        "total_services": total_services,
        "total_bookings": total_bookings,
        "completed_bookings": completed_bookings,
        "average_rating": float(avg_rating),
        "categories_count": categories_count
    }

