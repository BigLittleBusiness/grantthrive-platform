"""
GrantThrive Notifications API Endpoints
Handles notification delivery, preferences, and management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud.notifications import (
    get_user_notifications, mark_notification_read, mark_all_read,
    get_notification_preferences, update_notification_preferences,
    create_notification, get_notification_stats, delete_notification
)
from app.models.user import User
from app.schemas.notifications import (
    NotificationResponse, NotificationPreferencesResponse,
    NotificationPreferencesUpdate, NotificationCreate
)

router = APIRouter()

# User Notifications
@router.get("/", response_model=List[NotificationResponse])
def get_my_notifications(
    unread_only: bool = Query(False, description="Show only unread notifications"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    priority: Optional[str] = Query(None, description="Filter by priority level"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user notifications"""
    return get_user_notifications(
        db=db, user_id=current_user.id,
        unread_only=unread_only, notification_type=notification_type,
        priority=priority, skip=skip, limit=limit
    )

@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""
    success = mark_notification_read(
        db=db, notification_id=notification_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

@router.put("/mark-all-read")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read"""
    count = mark_all_read(db=db, user_id=current_user.id)
    return {"message": f"Marked {count} notifications as read"}

@router.delete("/{notification_id}")
def delete_user_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete notification"""
    success = delete_notification(
        db=db, notification_id=notification_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted"}

# Notification Preferences
@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_my_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user notification preferences"""
    return get_notification_preferences(db=db, user_id=current_user.id)

@router.put("/preferences", response_model=NotificationPreferencesResponse)
def update_my_notification_preferences(
    preferences: NotificationPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user notification preferences"""
    return update_notification_preferences(
        db=db, user_id=current_user.id, preferences=preferences
    )

# Notification Statistics
@router.get("/stats")
def get_my_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user notification statistics"""
    return get_notification_stats(db=db, user_id=current_user.id)

# System Notifications (Admin only)
@router.post("/system", response_model=NotificationResponse)
def create_system_notification(
    notification: NotificationCreate,
    target_user_id: Optional[int] = None,
    target_role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create system notification (admin only)"""
    if current_user.role not in ["client_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return create_notification(
        db=db, notification=notification,
        sender_id=current_user.id,
        target_user_id=target_user_id,
        target_role=target_role,
        organization_id=current_user.organization_id
    )

# Real-time notification endpoints
@router.get("/unread-count")
def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    notifications = get_user_notifications(
        db=db, user_id=current_user.id, unread_only=True, skip=0, limit=1000
    )
    return {"unread_count": len(notifications)}

@router.get("/recent")
def get_recent_notifications(
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent notifications for header/dropdown"""
    return get_user_notifications(
        db=db, user_id=current_user.id,
        unread_only=False, skip=0, limit=limit
    )

