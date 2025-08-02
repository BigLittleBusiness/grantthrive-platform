"""
GrantThrive Professional Marketplace API Endpoints
Handles professional services, bookings, and reviews
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud.marketplace import (
    create_professional_profile, get_professional_profiles, get_profile_by_id,
    update_professional_profile, approve_professional_profile,
    create_service_listing, get_service_listings, get_service_by_id,
    update_service_listing, delete_service_listing,
    create_booking, get_bookings, get_booking_by_id, update_booking_status,
    create_service_review, get_service_reviews, get_professional_reviews,
    get_marketplace_stats
)
from app.models.user import User
from app.schemas.marketplace import (
    ProfessionalProfileCreate, ProfessionalProfile, ProfessionalProfileUpdate,
    ProfessionalServiceCreate, ProfessionalService, ProfessionalServiceUpdate,
    ServiceBookingCreate, ServiceBooking, ServiceBookingUpdate,
    ProfessionalReviewCreate, ProfessionalReview
)

router = APIRouter()

# Professional Profile Management
@router.post("/profiles", response_model=ProfessionalProfile)
def create_profile(
    profile: ProfessionalProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create professional profile application"""
    if current_user.role != "professional":
        raise HTTPException(status_code=403, detail="Only professional users can create profiles")
    
    return create_professional_profile(
        db=db, profile=profile, user_id=current_user.id,
        organization_id=current_user.organization_id
    )

@router.get("/profiles", response_model=List[ProfessionalProfile])
def get_profiles(
    status: Optional[str] = Query("approved", description="Filter by approval status"),
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    location: Optional[str] = Query(None, description="Filter by location"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get professional profiles"""
    return get_professional_profiles(
        db=db, organization_id=current_user.organization_id,
        status=status, specialization=specialization,
        location=location, skip=skip, limit=limit
    )

@router.get("/profiles/{profile_id}", response_model=ProfessionalProfile)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific professional profile"""
    profile = get_profile_by_id(db=db, profile_id=profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/profiles/{profile_id}", response_model=ProfessionalProfile)
def update_profile(
    profile_id: int,
    profile_update: ProfessionalProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update professional profile"""
    profile = get_profile_by_id(db=db, profile_id=profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if profile.user_id != current_user.id and current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return update_professional_profile(db=db, profile_id=profile_id, profile_update=profile_update)

@router.put("/profiles/{profile_id}/approve", response_model=ProfessionalProfile)
def approve_profile(
    profile_id: int,
    approved: bool = True,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject professional profile"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return approve_professional_profile(
        db=db, profile_id=profile_id, approved=approved,
        reviewer_id=current_user.id, feedback=feedback
    )

# Service Listings Management
@router.post("/services", response_model=ProfessionalService)
def create_service(
    service: ProfessionalServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create service listing"""
    if current_user.role != "professional":
        raise HTTPException(status_code=403, detail="Only professionals can create services")
    
    return create_service_listing(
        db=db, service=service, professional_id=current_user.id
    )

@router.get("/services", response_model=List[ProfessionalService])
def get_services(
    category: Optional[str] = Query(None, description="Filter by service category"),
    pricing_model: Optional[str] = Query(None, description="Filter by pricing model"),
    location: Optional[str] = Query(None, description="Filter by location"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    is_active: bool = Query(True, description="Show only active services"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get service listings"""
    return get_service_listings(
        db=db, organization_id=current_user.organization_id,
        category=category, pricing_model=pricing_model,
        location=location, min_price=min_price, max_price=max_price,
        is_active=is_active, skip=skip, limit=limit
    )

@router.get("/services/{service_id}", response_model=ProfessionalService)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific service listing"""
    service = get_service_by_id(db=db, service_id=service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.put("/services/{service_id}", response_model=ProfessionalService)
def update_service(
    service_id: int,
    service_update: ProfessionalServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update service listing"""
    service = get_service_by_id(db=db, service_id=service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if service.professional_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return update_service_listing(db=db, service_id=service_id, service_update=service_update)

@router.delete("/services/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete service listing"""
    service = get_service_by_id(db=db, service_id=service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if service.professional_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = delete_service_listing(db=db, service_id=service_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete service")
    
    return {"message": "Service deleted successfully"}

# Booking Management
@router.post("/bookings", response_model=ServiceBooking)
def create_booking_request(
    booking: ServiceBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create service booking request"""
    return create_booking(
        db=db, booking=booking, client_id=current_user.id
    )

@router.get("/bookings", response_model=List[ServiceBooking])
def get_my_bookings(
    status: Optional[str] = Query(None, description="Filter by booking status"),
    as_client: bool = Query(True, description="Get bookings as client or professional"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's bookings"""
    return get_bookings(
        db=db, user_id=current_user.id, as_client=as_client,
        status=status, skip=skip, limit=limit
    )

@router.get("/bookings/{booking_id}", response_model=ServiceBooking)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific booking"""
    booking = get_booking_by_id(db=db, booking_id=booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check access permissions
    if booking.client_id != current_user.id and booking.professional_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return booking

@router.put("/bookings/{booking_id}/status", response_model=ServiceBooking)
def update_booking(
    booking_id: int,
    booking_update: ServiceBookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update booking status"""
    booking = get_booking_by_id(db=db, booking_id=booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check permissions based on status change
    if booking_update.status in ["accepted", "rejected"] and booking.professional_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only professional can accept/reject")
    
    if booking_update.status == "cancelled" and booking.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only client can cancel")
    
    return update_booking_status(
        db=db, booking_id=booking_id, status=booking_update.status,
        notes=booking_update.notes
    )

# Reviews and Ratings
@router.post("/reviews", response_model=ProfessionalReview)
def create_review(
    review: ProfessionalReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create service review"""
    return create_service_review(
        db=db, review=review, reviewer_id=current_user.id
    )

@router.get("/services/{service_id}/reviews", response_model=List[ProfessionalReview])
def get_service_reviews_list(
    service_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get reviews for a service"""
    return get_service_reviews(db=db, service_id=service_id, skip=skip, limit=limit)

@router.get("/professionals/{professional_id}/reviews", response_model=List[ProfessionalReview])
def get_professional_reviews_list(
    professional_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get reviews for a professional"""
    return get_professional_reviews(db=db, professional_id=professional_id, skip=skip, limit=limit)

# Marketplace Statistics
@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get marketplace statistics"""
    return get_marketplace_stats(db=db, organization_id=current_user.organization_id)

# Admin endpoints
@router.get("/admin/pending-profiles", response_model=List[ProfessionalProfile])
def get_pending_profiles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pending professional profiles for review"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return get_professional_profiles(
        db=db, organization_id=current_user.organization_id,
        status="pending", skip=skip, limit=limit
    )

