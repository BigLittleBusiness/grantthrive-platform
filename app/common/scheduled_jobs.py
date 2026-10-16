"""Scheduled GrantThrive maintenance jobs.

Jobs run in a dedicated scheduler process, never in a Gunicorn web worker. This
prevents duplicate email and report jobs when the HTTP service is scaled.
"""
import logging
import signal
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


def _job_reviewer_reminder(app):
    """Remind assigned reviewers whose work has been waiting for 48 hours."""
    with app.app_context():
        try:
            from app import db
            from app.models import ApplicationAssignment, Application, Grant, User
            from app.common.notifications import notify
            from app.common import email_service
            cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
            rows = (
                db.session.query(ApplicationAssignment, User, Application, Grant)
                .join(User, User.id == ApplicationAssignment.staff_id)
                .join(Application, Application.id == ApplicationAssignment.application_id)
                .join(Grant, Grant.id == Application.grant_id)
                .filter(
                    ApplicationAssignment.status == "assigned",
                    ApplicationAssignment.assigned_at <= cutoff,
                    User.is_active.is_(True),
                ).all()
            )
            for assignment, staff, application, grant in rows:
                notify(
                    user_id=staff.id,
                    ntype="reviewer_reminder",
                    title="Reminder: application awaiting your review",
                    message=f'Application #{application.id} for "{grant.title}" has been waiting for your review for more than 48 hours.',
                    link="portal/council/pending-approvals",
                    send_email_fn=lambda s=staff, a=application, g=grant: email_service.send_reviewer_reminder(s.email, s.first_name, g.title, a.id),
                )
            logger.info("reviewer_reminder job: processed %d assignments", len(rows))
        except Exception:
            logger.exception("reviewer_reminder job failed")
            db.session.rollback()


def _job_voting_closes_soon(app):
    """Notify opted-in members about voting sessions that close in 48 hours."""
    with app.app_context():
        try:
            from app import db
            from app.models import VotingSession, CommunityVote, User, Grant
            from app.common.notifications import notify
            from app.common import email_service
            now = datetime.now(timezone.utc)
            sessions = VotingSession.query.join(Grant).filter(
                VotingSession.is_active.is_(True),
                VotingSession.is_published.is_(True),
                VotingSession.ends_at >= now + timedelta(hours=47),
                VotingSession.ends_at <= now + timedelta(hours=49),
                Grant.is_published.is_(True),
            ).all()
            sent = 0
            for session in sessions:
                members = User.query.filter_by(council_id=session.council_id, role="community_member", is_active=True).filter(User.email_opt_in.is_(True)).all()
                voted_ids = {user_id for (user_id,) in db.session.query(CommunityVote.voter_id).filter(CommunityVote.voting_session_id == session.id, CommunityVote.voter_id.isnot(None)).all()}
                for member in members:
                    if member.id in voted_ids:
                        continue
                    notify(
                        user_id=member.id,
                        ntype="voting_closes_soon",
                        title=f"Voting closes soon: {session.title}",
                        message=f'The voting session "{session.title}" closes in less than 48 hours.',
                        link="portal/community/voting",
                        send_email_fn=lambda m=member, s=session: email_service.send_voting_closes_soon(m.email, m.first_name, s.title, s.id, s.ends_at),
                    )
                    sent += 1
            logger.info("voting_closes_soon job: processed %d sessions and notified %d members", len(sessions), sent)
        except Exception:
            logger.exception("voting_closes_soon job failed")
            db.session.rollback()


def _job_monthly_digest(app):
    """Send a concise previous-month activity digest to each council admin."""
    with app.app_context():
        try:
            from app.models import User, Application, Grant
            from app.common import email_service
            now = datetime.now(timezone.utc)
            month_end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_start = (month_end - timedelta(days=1)).replace(day=1)
            admins = User.query.filter_by(role="council_admin", is_active=True).all()
            for admin in admins:
                base = Application.query.join(Grant).filter(Grant.council_id == admin.council_id)
                submitted = base.filter(Application.submitted_at >= month_start, Application.submitted_at < month_end).count()
                approved = base.filter(Application.decision_date >= month_start, Application.decision_date < month_end, Application.status == "approved").count()
                active_grants = Grant.query.filter_by(council_id=admin.council_id, status="open", is_published=True).count()
                email_service.send_monthly_digest(admin.email, admin.first_name, month_start.strftime("%B %Y"), submitted, approved, active_grants)
            logger.info("monthly_digest job: processed %d council admins", len(admins))
        except Exception:
            logger.exception("monthly_digest job failed")


def _job_monthly_performance_reports(app):
    with app.app_context():
        try:
            import os
            from app.reports.monthly_reports import run_monthly_reports
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            results = run_monthly_reports(output_dir=os.path.join(root, "reports_output"), log_dir=os.path.join(root, "logs"), dry_run=False)
            logger.info("monthly_performance_reports job: completed %d reports", len(results))
        except Exception:
            logger.exception("monthly_performance_reports job failed")


def build_scheduler(app):
    """Return the one scheduler used by the dedicated service process."""
    scheduler = BlockingScheduler(timezone="Australia/Sydney")
    jobs = [
        ("reviewer_reminder", _job_reviewer_reminder, CronTrigger(hour=9, minute=0)),
        ("voting_closes_soon", _job_voting_closes_soon, CronTrigger(hour=9, minute=5)),
        ("monthly_digest", _job_monthly_digest, CronTrigger(day=1, hour=8, minute=0)),
        ("monthly_performance_reports", _job_monthly_performance_reports, CronTrigger(day=1, hour=9, minute=0)),
    ]
    for job_id, func, trigger in jobs:
        scheduler.add_job(func, trigger, args=[app], id=job_id, replace_existing=True, max_instances=1, coalesce=True, misfire_grace_time=3600)
    return scheduler


def run_scheduler(app):
    """Run scheduler until systemd sends SIGTERM/SIGINT."""
    scheduler = build_scheduler(app)
    def shutdown(*_args):
        logger.info("Stopping GrantThrive scheduler")
        scheduler.shutdown(wait=False)
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    logger.info("Starting dedicated scheduler process with %d jobs", len(scheduler.get_jobs()))
    scheduler.start()
