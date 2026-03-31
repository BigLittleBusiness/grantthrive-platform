"""
scheduled_jobs.py
─────────────────
APScheduler background jobs for timed notification nudges.

Jobs registered here:
  1. reviewer_reminder        — daily, 09:00 AEST
     Remind staff who have had an unreviewed assignment for ≥ 48 hours.

  2. voting_closes_soon       — daily, 09:00 AEST
     Notify opted-in community members 48 hours before a voting session closes.

  3. monthly_activity_digest  — 1st of each month, 08:00 AEST
     Send council admins a summary of the previous month's activity.

  4. subscription_renewal_reminder — daily, 09:00 AEST
     Warn council admins 14 days before their subscription renews.

Usage (in app/__init__.py):
    from app.common.scheduled_jobs import init_scheduler
    init_scheduler(app)
"""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = None


# ─────────────────────────────────────────────────────────────────────────────
# Job 1: Reviewer reminder (daily 09:00 UTC+10)
# ─────────────────────────────────────────────────────────────────────────────

def _job_reviewer_reminder(app):
    """Remind staff assigned to applications they haven't reviewed in 48 hours."""
    with app.app_context():
        try:
            from app import db
            from app.models import ApplicationAssignment, Application, User, Grant
            from app.common.notifications import notify
            from app.common import email_service

            cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
            stale = (
                ApplicationAssignment.query
                .filter(
                    ApplicationAssignment.status == 'assigned',
                    ApplicationAssignment.assigned_at <= cutoff,
                )
                .all()
            )
            for assignment in stale:
                staff = db.session.get(User, assignment.staff_id)
                app_obj = db.session.get(Application, assignment.application_id)
                grant = db.session.get(Grant, app_obj.grant_id) if app_obj else None
                if staff and app_obj and grant:
                    notify(
                        user_id=staff.id,
                        ntype='reviewer_reminder',
                        title=f'Reminder: application awaiting your review',
                        message=(
                            f'Application #{app_obj.id} for "{grant.title}" '
                            f'has been waiting for your review for more than 48 hours.'
                        ),
                        link='portal/council/pending-approvals',
                        send_email_fn=lambda s=staff, a=app_obj, g=grant: (
                            email_service.send_reviewer_reminder(
                                s.email, s.first_name, g.title, a.id
                            )
                        ),
                    )
            logger.info('reviewer_reminder job: sent %d reminders', len(stale))
        except Exception as exc:
            logger.error('reviewer_reminder job failed: %s', exc)


# ─────────────────────────────────────────────────────────────────────────────
# Job 2: Voting closes soon (daily 09:00 UTC+10)
# ─────────────────────────────────────────────────────────────────────────────

def _job_voting_closes_soon(app):
    """Notify opted-in community members 48 h before a voting session closes."""
    with app.app_context():
        try:
            from app import db
            from app.models import VotingSession, CommunityVote, User, Grant
            from app.common.notifications import notify
            from app.common import email_service

            now = datetime.now(timezone.utc)
            window_start = now + timedelta(hours=47)
            window_end   = now + timedelta(hours=49)

            sessions = VotingSession.query.filter(
                VotingSession.is_active == True,
                VotingSession.ends_at >= window_start,
                VotingSession.ends_at <= window_end,
            ).all()

            for session in sessions:
                grant = db.session.get(Grant, session.grant_id)
                if not grant:
                    continue
                members = (
                    User.query
                    .filter_by(
                        council_id=grant.council_id,
                        role='community_member',
                        is_active=True,
                    )
                    .filter(User.email_opt_in.is_(True))
                    .all()
                )
                for member in members:
                    # Only notify if they haven't voted yet
                    already_voted = CommunityVote.query.filter_by(
                        voting_session_id=session.id,
                        voter_id=member.id,
                    ).first()
                    if not already_voted:
                        notify(
                            user_id=member.id,
                            ntype='voting_closes_soon',
                            title=f'Voting closes soon: {session.title}',
                            message=(
                                f'The voting session "{session.title}" closes in less than 48 hours. '
                                f'Don\'t miss your chance to have your say!'
                            ),
                            link='portal/community/voting',
                            send_email_fn=lambda m=member, s=session: (
                                email_service.send_voting_closes_soon(
                                    m.email, m.first_name, s.title, s.id, s.ends_at
                                )
                            ),
                        )
            logger.info('voting_closes_soon job: processed %d sessions', len(sessions))
        except Exception as exc:
            logger.error('voting_closes_soon job failed: %s', exc)


# ─────────────────────────────────────────────────────────────────────────────
# Job 3: Monthly activity digest (1st of month 08:00 UTC+10)
# ─────────────────────────────────────────────────────────────────────────────

def _job_monthly_digest(app):
    """Send council admins a summary of the previous month's activity."""
    with app.app_context():
        try:
            from app import db
            from app.models import User, Application, Grant, Council
            from app.common import email_service
            from sqlalchemy import func

            now = datetime.now(timezone.utc)
            month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
            month_end   = now.replace(day=1)

            admins = User.query.filter_by(role='council_admin', is_active=True).all()
            for admin in admins:
                # Gather stats for their council
                council_grant_ids = [
                    g.id for g in Grant.query.filter_by(council_id=admin.council_id).all()
                ]
                if not council_grant_ids:
                    continue

                apps_this_month = Application.query.filter(
                    Application.grant_id.in_(council_grant_ids),
                    Application.submitted_at >= month_start,
                    Application.submitted_at < month_end,
                ).count()

                approved_this_month = Application.query.filter(
                    Application.grant_id.in_(council_grant_ids),
                    Application.decision_date >= month_start,
                    Application.decision_date < month_end,
                    Application.status == 'approved',
                ).count()

                active_grants = Grant.query.filter_by(
                    council_id=admin.council_id,
                    status='published',
                ).count()

                email_service.send_monthly_digest(
                    admin.email,
                    admin.first_name,
                    month_start.strftime('%B %Y'),
                    apps_this_month,
                    approved_this_month,
                    active_grants,
                )
            logger.info('monthly_digest job: sent to %d council admins', len(admins))
        except Exception as exc:
            logger.error('monthly_digest job failed: %s', exc)


# ───────────────────────────────────────────────────────────────────────────────
# Job 5: Monthly performance reports (1st of month 09:00 UTC+10)
# ───────────────────────────────────────────────────────────────────────────────

def _job_monthly_performance_reports(app):
    """Generate and email comprehensive monthly performance reports to all council admins."""
    with app.app_context():
        try:
            import os
            from app.reports.monthly_reports import run_monthly_reports

            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(project_root, 'reports_output')
            log_dir    = os.path.join(project_root, 'logs')

            results = run_monthly_reports(
                output_dir=output_dir,
                log_dir=log_dir,
                dry_run=False,
            )

            success = sum(1 for r in results if r['status'] == 'success')
            failed  = sum(1 for r in results if r['status'] == 'failed')
            logger.info(
                'monthly_performance_reports job: %d councils processed, %d success, %d failed',
                len(results), success, failed,
            )
        except Exception as exc:
            logger.error('monthly_performance_reports job failed: %s', exc)


# ───────────────────────────────────────────────────────────────────────────────
# Job 4: Subscription renewal reminder (daily 09:00 UTC+10)
# ───────────────────────────────────────────────────────────────────────────────

def _job_subscription_renewal_reminder(app):
    """Warn council admins 14 days before their subscription renews."""
    with app.app_context():
        try:
            from app import db
            from app.models import User, PricingConfig
            from app.common import email_service

            now = datetime.now(timezone.utc)
            target_date_start = now + timedelta(days=13, hours=23)
            target_date_end   = now + timedelta(days=14, hours=1)

            admins = (
                User.query
                .filter_by(role='council_admin', is_active=True)
                .filter(
                    User.subscription_renewal_date >= target_date_start,
                    User.subscription_renewal_date <= target_date_end,
                )
                .all()
            )
            for admin in admins:
                email_service.send_subscription_renewal_reminder(
                    admin.email,
                    admin.first_name,
                    admin.subscription_renewal_date,
                )
            logger.info(
                'subscription_renewal_reminder job: sent to %d admins', len(admins)
            )
        except Exception as exc:
            logger.error('subscription_renewal_reminder job failed: %s', exc)


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler init
# ─────────────────────────────────────────────────────────────────────────────

def init_scheduler(app):
    """Initialise and start the APScheduler background scheduler.
    Call once from app/__init__.py after the app is configured.
    """
    global _scheduler
    if _scheduler is not None:
        return  # Already initialised (guard against double-init in dev reloader)

    _scheduler = BackgroundScheduler(timezone='Australia/Sydney')

    # Job 1: reviewer reminder — daily at 09:00 AEST
    _scheduler.add_job(
        func=_job_reviewer_reminder,
        trigger=CronTrigger(hour=9, minute=0),
        args=[app],
        id='reviewer_reminder',
        replace_existing=True,
    )

    # Job 2: voting closes soon — daily at 09:00 AEST
    _scheduler.add_job(
        func=_job_voting_closes_soon,
        trigger=CronTrigger(hour=9, minute=5),
        args=[app],
        id='voting_closes_soon',
        replace_existing=True,
    )

    # Job 3: monthly digest — 1st of each month at 08:00 AEST
    _scheduler.add_job(
        func=_job_monthly_digest,
        trigger=CronTrigger(day=1, hour=8, minute=0),
        args=[app],
        id='monthly_digest',
        replace_existing=True,
    )

    # Job 5: monthly performance reports — 1st of each month at 09:00 AEST
    _scheduler.add_job(
        func=_job_monthly_performance_reports,
        trigger=CronTrigger(day=1, hour=9, minute=0),
        args=[app],
        id='monthly_performance_reports',
        replace_existing=True,
    )

    # Job 4: subscription renewal reminder — daily at 09:00 AEST
    _scheduler.add_job(
        func=_job_subscription_renewal_reminder,
        trigger=CronTrigger(hour=9, minute=10),
        args=[app],
        id='subscription_renewal_reminder',
        replace_existing=True,
    )

    _scheduler.start()
    logger.info('APScheduler started with %d jobs', len(_scheduler.get_jobs()))
