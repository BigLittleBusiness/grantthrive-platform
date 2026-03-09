"""
GrantThrive — Notifications API
=================================
Endpoints for the in-app notification bell.

GET  /api/notifications/          — list unread + recent notifications for current user
GET  /api/notifications/unread-count — unread badge count
POST /api/notifications/<id>/read — mark one notification as read
POST /api/notifications/read-all  — mark all as read
"""

from datetime import datetime, timezone, timedelta
from flask import jsonify, request
from app.notifications import bp
from app.common.decorators import login_required_api


@bp.route('/', methods=['GET'])
@login_required_api
def list_notifications(current_user):
    """Return the 50 most recent notifications for the current user."""
    from app.models import Notification

    notifications = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count':  sum(1 for n in notifications if not n.is_read),
    })


@bp.route('/unread-count', methods=['GET'])
@login_required_api
def unread_count(current_user):
    """Return just the unread badge count (lightweight poll endpoint)."""
    from app.models import Notification

    count = (
        Notification.query
        .filter_by(user_id=current_user.id, is_read=False)
        .count()
    )
    return jsonify({'unread_count': count})


@bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required_api
def mark_read(current_user, notification_id):
    """Mark a single notification as read."""
    from app import db
    from app.models import Notification

    notif = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first()

    if not notif:
        return jsonify({'error': 'Notification not found'}), 404

    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True, 'notification': notif.to_dict()})


@bp.route('/read-all', methods=['POST'])
@login_required_api
def mark_all_read(current_user):
    """Mark all unread notifications as read for the current user."""
    from app import db
    from app.models import Notification

    updated = (
        Notification.query
        .filter_by(user_id=current_user.id, is_read=False)
        .update({'is_read': True})
    )
    db.session.commit()
    return jsonify({'success': True, 'marked_read': updated})
