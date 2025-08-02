"""
GrantThrive Notifications CRUD Operations
Database operations for notification delivery and management
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, time

from ..models.gamification import Notification, NotificationPreference
from ..schemas.notifications import (
    NotificationResponse, NotificationPreferencesResponse,
    NotificationPreferencesUpdate, NotificationCreate
)


# Notification CRUD
def get_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[NotificationResponse]:
    """Get user notifications"""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    
    if priority:
        query = query.filter(Notification.priority == priority)
    
    notifications = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()
    
    return [
        NotificationResponse(
            id=notif.id,
            user_id=notif.user_id,
            notification_type=notif.notification_type,
            title=notif.title,
            message=notif.message,
            priority=notif.priority,
            channels=notif.channels,
            metadata=notif.metadata,
            read_at=notif.read_at,
            delivered_at=notif.delivered_at,
            scheduled_for=notif.scheduled_for,
            created_at=notif.created_at
        )
        for notif in notifications
    ]

def mark_notification_read(db: Session, notification_id: int, user_id: int) -> bool:
    """Mark notification as read"""
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
    ).first()
    
    if notification and not notification.read_at:
        notification.read_at = datetime.utcnow()
        db.commit()
        return True
    
    return False

def mark_all_read(db: Session, user_id: int) -> int:
    """Mark all notifications as read"""
    count = db.query(Notification).filter(
        and_(
            Notification.user_id == user_id,
            Notification.read_at.is_(None)
        )
    ).update({"read_at": datetime.utcnow()})
    
    db.commit()
    return count

def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
    """Delete notification"""
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
    ).first()
    
    if notification:
        db.delete(notification)
        db.commit()
        return True
    
    return False

def create_notification(
    db: Session,
    notification: NotificationCreate,
    sender_id: Optional[int] = None,
    target_user_id: Optional[int] = None,
    target_role: Optional[str] = None,
    organization_id: Optional[int] = None
) -> NotificationResponse:
    """Create notification for user(s)"""
    from ..models.user import User
    
    # Determine target users
    target_users = []
    
    if target_user_id:
        target_users = [target_user_id]
    elif target_role and organization_id:
        users = db.query(User.id).filter(
            and_(
                User.organization_id == organization_id,
                User.role == target_role
            )
        ).all()
        target_users = [user.id for user in users]
    elif organization_id:
        users = db.query(User.id).filter(User.organization_id == organization_id).all()
        target_users = [user.id for user in users]
    
    # Create notifications for each target user
    created_notifications = []
    
    for user_id in target_users:
        # Check user preferences
        preferences = get_notification_preferences(db, user_id)
        
        # Filter channels based on preferences
        allowed_channels = []
        for channel in notification.channels:
            pref_key = f"{notification.notification_type}_{channel}"
            if getattr(preferences, pref_key, True):  # Default to True if preference not found
                allowed_channels.append(channel)
        
        # Check quiet hours
        if _is_quiet_hours(preferences):
            # Schedule for later or use only non-intrusive channels
            allowed_channels = [ch for ch in allowed_channels if ch in ["in_app"]]
        
        if allowed_channels:  # Only create if user allows this type of notification
            db_notification = Notification(
                user_id=user_id,
                sender_id=sender_id,
                notification_type=notification.notification_type,
                title=notification.title,
                message=notification.message,
                priority=notification.priority,
                channels=allowed_channels,
                metadata=notification.metadata or {},
                scheduled_for=notification.scheduled_for
            )
            db.add(db_notification)
            created_notifications.append(db_notification)
    
    db.commit()
    
    # Return the first created notification as example
    if created_notifications:
        db.refresh(created_notifications[0])
        return NotificationResponse(
            id=created_notifications[0].id,
            user_id=created_notifications[0].user_id,
            notification_type=created_notifications[0].notification_type,
            title=created_notifications[0].title,
            message=created_notifications[0].message,
            priority=created_notifications[0].priority,
            channels=created_notifications[0].channels,
            metadata=created_notifications[0].metadata,
            read_at=created_notifications[0].read_at,
            delivered_at=created_notifications[0].delivered_at,
            scheduled_for=created_notifications[0].scheduled_for,
            created_at=created_notifications[0].created_at
        )

def _is_quiet_hours(preferences: NotificationPreferencesResponse) -> bool:
    """Check if current time is within user's quiet hours"""
    if not preferences.quiet_hours_enabled:
        return False
    
    current_time = datetime.utcnow().time()
    start_time = time.fromisoformat(preferences.quiet_hours_start)
    end_time = time.fromisoformat(preferences.quiet_hours_end)
    
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    else:  # Quiet hours span midnight
        return current_time >= start_time or current_time <= end_time

# Notification Preferences
def get_notification_preferences(db: Session, user_id: int) -> NotificationPreferencesResponse:
    """Get user notification preferences"""
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id
    ).first()
    
    if not preferences:
        # Create default preferences
        preferences = NotificationPreference(
            user_id=user_id,
            grant_updates_email=True,
            grant_updates_sms=False,
            grant_updates_push=True,
            application_status_email=True,
            application_status_sms=True,
            application_status_push=True,
            community_activity_email=False,
            community_activity_sms=False,
            community_activity_push=True,
            marketplace_activity_email=True,
            marketplace_activity_sms=False,
            marketplace_activity_push=True,
            system_announcements_email=True,
            system_announcements_sms=False,
            system_announcements_push=True,
            quiet_hours_enabled=False,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
            timezone="UTC"
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return NotificationPreferencesResponse(
        user_id=preferences.user_id,
        grant_updates_email=preferences.grant_updates_email,
        grant_updates_sms=preferences.grant_updates_sms,
        grant_updates_push=preferences.grant_updates_push,
        application_status_email=preferences.application_status_email,
        application_status_sms=preferences.application_status_sms,
        application_status_push=preferences.application_status_push,
        community_activity_email=preferences.community_activity_email,
        community_activity_sms=preferences.community_activity_sms,
        community_activity_push=preferences.community_activity_push,
        marketplace_activity_email=preferences.marketplace_activity_email,
        marketplace_activity_sms=preferences.marketplace_activity_sms,
        marketplace_activity_push=preferences.marketplace_activity_push,
        system_announcements_email=preferences.system_announcements_email,
        system_announcements_sms=preferences.system_announcements_sms,
        system_announcements_push=preferences.system_announcements_push,
        quiet_hours_enabled=preferences.quiet_hours_enabled,
        quiet_hours_start=preferences.quiet_hours_start,
        quiet_hours_end=preferences.quiet_hours_end,
        timezone=preferences.timezone
    )

def update_notification_preferences(
    db: Session,
    user_id: int,
    preferences: NotificationPreferencesUpdate
) -> NotificationPreferencesResponse:
    """Update user notification preferences"""
    db_preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id
    ).first()
    
    if not db_preferences:
        db_preferences = NotificationPreference(user_id=user_id)
        db.add(db_preferences)
    
    # Update preferences
    for field, value in preferences.model_dump(exclude_unset=True).items():
        setattr(db_preferences, field, value)
    
    db_preferences.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_preferences)
    
    return get_notification_preferences(db, user_id)

# Statistics
def get_notification_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """Get user notification statistics"""
    total_notifications = db.query(Notification).filter(
        Notification.user_id == user_id
    ).count()
    
    unread_notifications = db.query(Notification).filter(
        and_(
            Notification.user_id == user_id,
            Notification.read_at.is_(None)
        )
    ).count()
    
    # Notifications by type
    type_counts = db.query(
        Notification.notification_type,
        func.count(Notification.id).label('count')
    ).filter(
        Notification.user_id == user_id
    ).group_by(Notification.notification_type).all()
    
    notifications_by_type = {ntype: count for ntype, count in type_counts}
    
    # Recent notifications (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_notifications = db.query(Notification).filter(
        and_(
            Notification.user_id == user_id,
            Notification.created_at >= seven_days_ago
        )
    ).count()
    
    return {
        "total_notifications": total_notifications,
        "unread_notifications": unread_notifications,
        "read_rate": ((total_notifications - unread_notifications) / total_notifications * 100) if total_notifications > 0 else 0,
        "notifications_by_type": notifications_by_type,
        "recent_notifications": recent_notifications
    }

