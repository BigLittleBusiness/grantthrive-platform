"""
GrantThrive Networking API Endpoints
Handles user connections, events, and networking features
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud.community import (
    create_user_connection, get_user_connections, update_connection_status,
    create_networking_event, get_networking_events, get_event_by_id,
    register_for_event, get_event_registrations, get_user_interests,
    create_user_interest, delete_user_interest
)
from app.models.user import User
from app.schemas.community import (
    UserConnectionCreate, UserConnectionResponse, UserConnectionUpdate,
    NetworkingEventCreate, NetworkingEventResponse, NetworkingEventUpdate,
    EventRegistrationCreate, EventRegistrationResponse,
    UserInterestCreate, UserInterestResponse
)

router = APIRouter()

# User Connections Endpoints
@router.post("/connections", response_model=UserConnectionResponse)
def create_connection(
    connection: UserConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user connection request"""
    return create_user_connection(db=db, connection=connection, requester_id=current_user.id)

@router.get("/connections", response_model=List[UserConnectionResponse])
def get_connections(
    status: Optional[str] = Query(None, description="Filter by connection status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's connections"""
    return get_user_connections(
        db=db, user_id=current_user.id, status=status, skip=skip, limit=limit
    )

@router.put("/connections/{connection_id}", response_model=UserConnectionResponse)
def update_connection(
    connection_id: int,
    connection_update: UserConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update connection status (accept/reject/block)"""
    return update_connection_status(
        db=db, connection_id=connection_id, 
        status=connection_update.status, user_id=current_user.id
    )

# Networking Events Endpoints
@router.post("/events", response_model=NetworkingEventResponse)
def create_event(
    event: NetworkingEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new networking event"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return create_networking_event(
        db=db, event=event, organizer_id=current_user.id,
        organization_id=current_user.organization_id
    )

@router.get("/events", response_model=List[NetworkingEventResponse])
def get_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    is_virtual: Optional[bool] = Query(None, description="Filter by virtual/in-person"),
    upcoming_only: bool = Query(True, description="Show only upcoming events"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get networking events"""
    return get_networking_events(
        db=db, organization_id=current_user.organization_id,
        event_type=event_type, is_virtual=is_virtual,
        upcoming_only=upcoming_only, skip=skip, limit=limit
    )

@router.get("/events/{event_id}", response_model=NetworkingEventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific networking event"""
    event = get_event_by_id(db=db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.post("/events/{event_id}/register", response_model=EventRegistrationResponse)
def register_event(
    event_id: int,
    registration: EventRegistrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register for a networking event"""
    return register_for_event(
        db=db, event_id=event_id, user_id=current_user.id,
        registration_data=registration
    )

@router.get("/events/{event_id}/registrations", response_model=List[EventRegistrationResponse])
def get_event_registrations_list(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event registrations (organizers only)"""
    event = get_event_by_id(db=db, event_id=event_id)
    if not event or event.organizer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return get_event_registrations(db=db, event_id=event_id)

# User Interests Endpoints
@router.get("/interests", response_model=List[UserInterestResponse])
def get_my_interests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's interests"""
    return get_user_interests(db=db, user_id=current_user.id)

@router.post("/interests", response_model=UserInterestResponse)
def add_interest(
    interest: UserInterestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add user interest"""
    return create_user_interest(
        db=db, user_id=current_user.id, interest=interest
    )

@router.delete("/interests/{interest_id}")
def remove_interest(
    interest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove user interest"""
    success = delete_user_interest(
        db=db, interest_id=interest_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Interest not found")
    return {"message": "Interest removed successfully"}

# Networking Statistics
@router.get("/stats")
def get_networking_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get networking statistics for current user"""
    connections = get_user_connections(db=db, user_id=current_user.id)
    interests = get_user_interests(db=db, user_id=current_user.id)
    
    return {
        "total_connections": len([c for c in connections if c.status == "accepted"]),
        "pending_requests": len([c for c in connections if c.status == "pending"]),
        "total_interests": len(interests),
        "events_attended": 0  # TODO: Implement event attendance tracking
    }

