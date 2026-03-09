"""
GrantThrive — In-App Notification Helper
==========================================
Provides a single `notify()` function that creates a Notification row
and optionally fires the corresponding email.

Usage:
    from app.common.notifications import notify

    notify(
        user_id   = user.id,
        ntype     = 'reviewer_assigned',
        title     = 'New application to review',
        message   = f'You have been assigned to review application #{app.id}.',
        link      = 'portal/council/pending-approvals',
        send_email_fn = lambda: email_service.send_reviewer_assigned(...),
    )
"""

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def notify(
    user_id: int,
    ntype: str,
    title: str,
    message: str,
    link: Optional[str] = None,
    send_email_fn: Optional[Callable] = None,
) -> None:
    """
    Persist an in-app notification and optionally send the email.

    Args:
        user_id:       ID of the recipient User.
        ntype:         Notification type string (see Notification.type).
        title:         Short notification title shown in the bell dropdown.
        message:       Full notification message.
        link:          Relative frontend path to navigate to on click.
        send_email_fn: Zero-argument callable that sends the email.
                       Called after the DB row is committed.
                       Failures are logged but do not raise.
    """
    try:
        from app import db
        from app.models import Notification

        notif = Notification(
            user_id    = user_id,
            type       = ntype,
            title      = title,
            message    = message,
            link       = link,
            is_read    = False,
            created_at = datetime.now(timezone.utc),
        )
        db.session.add(notif)
        db.session.commit()
        logger.debug("In-app notification created: user=%s type=%s", user_id, ntype)
    except Exception as exc:
        logger.error("Failed to create in-app notification: %s", exc)
        try:
            db.session.rollback()
        except Exception:
            pass

    if send_email_fn:
        try:
            send_email_fn()
        except Exception as exc:
            logger.error("Notification email failed for user %s type %s: %s", user_id, ntype, exc)
