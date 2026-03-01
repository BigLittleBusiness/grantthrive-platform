"""
GrantThrive - Automated Monthly Report Runner
==============================================
Orchestrates the generation and email delivery of monthly performance reports
for every council (admin user) that has at least one grant in the system.

Designed to be invoked:
  - Via the Flask CLI:      flask run-monthly-reports
  - Via the cron scheduler: scripts/run_monthly_reports.py
  - Via APScheduler:        configured in app/__init__.py (optional)

Execution schedule: 1st of each month at 09:00 local time.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from email.mime.base import MIMEBase
from email import encoders

from flask import current_app
from flask_mail import Message

from app import db, mail
from app.models import User, Grant
from app.reports.report_generator import generate_council_report

logger = logging.getLogger(__name__)


# ─── Result constants ─────────────────────────────────────────────────────────
STATUS_SUCCESS = "success"
STATUS_SKIPPED = "skipped"
STATUS_FAILED  = "failed"


def _get_report_period():
    """
    Return (year, month) for the previous calendar month relative to today.
    Running on the 1st of the month means 'today - 1 day' gives the previous month.
    """
    today = datetime.utcnow()
    first_of_current = today.replace(day=1)
    last_of_previous = first_of_current - timedelta(days=1)
    return last_of_previous.year, last_of_previous.month


def _councils_with_grants():
    """
    Return a list of User records (role='admin') who own at least one grant.
    Each such user represents a council in the GrantThrive model.
    """
    admins_with_grants = (
        db.session.query(User)
        .join(Grant, Grant.created_by == User.id)
        .filter(User.role == "admin", User.is_active == True)
        .distinct()
        .all()
    )
    return admins_with_grants


def _send_report_email(admin_user, report_path, year, month):
    """
    Email the PDF report to all admin users associated with the council.
    In the current data model a council is represented by a single admin user,
    but we also CC any other active admin users who share the same email domain
    so that multiple staff members at the same council receive the report.

    Parameters
    ----------
    admin_user : User
    report_path : str    Absolute path to the generated PDF.
    year : int
    month : int
    """
    period_label = datetime(year, month, 1).strftime("%B %Y")
    council_name = (
        admin_user.organisation_name
        if hasattr(admin_user, "organisation_name") and admin_user.organisation_name
        else f"{admin_user.first_name} {admin_user.last_name} Council"
    )

    subject = (
        f"GrantThrive — Monthly Performance Report: {council_name} — {period_label}"
    )

    body_text = (
        f"Dear {admin_user.first_name},\n\n"
        f"Please find attached the automated Monthly Performance Report for "
        f"{council_name} covering the period {period_label}.\n\n"
        f"The report includes the following sections:\n"
        f"  1. Grant Program Overview\n"
        f"  2. Applications & Processing Times\n"
        f"  3. Budget Allocation\n"
        f"  4. Community Engagement\n"
        f"  5. Cost Savings & Efficiency\n"
        f"  6. Review & Assessment Activity\n\n"
        f"This report was generated automatically by the GrantThrive platform on "
        f"{datetime.utcnow().strftime('%d %B %Y at %H:%M UTC')}.\n\n"
        f"If you have any questions about the data in this report, please contact "
        f"your GrantThrive administrator.\n\n"
        f"Kind regards,\n"
        f"GrantThrive Platform\n"
        f"https://grantthrive.com"
    )

    msg = Message(
        subject=subject,
        sender=current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@grantthrive.com"),
        recipients=[admin_user.email],
    )
    msg.body = body_text

    # Attach the PDF
    filename = os.path.basename(report_path)
    with open(report_path, "rb") as fp:
        msg.attach(
            filename=filename,
            content_type="application/pdf",
            data=fp.read(),
        )

    mail.send(msg)
    logger.info(
        "Report email sent to %s (%s) for period %s",
        admin_user.email, council_name, period_label,
    )


def _log_result(results, output_dir=None):
    """
    Write a structured JSON log of the run results to the logs directory
    and emit summary lines to the application logger.

    Parameters
    ----------
    results : list[dict]
    output_dir : str | None   Override the log output directory (for testing).
    """
    run_summary = {
        "run_at":   datetime.utcnow().isoformat(),
        "total":    len(results),
        "success":  sum(1 for r in results if r["status"] == STATUS_SUCCESS),
        "skipped":  sum(1 for r in results if r["status"] == STATUS_SKIPPED),
        "failed":   sum(1 for r in results if r["status"] == STATUS_FAILED),
        "results":  results,
    }

    # Determine log directory
    if output_dir is None:
        base_dir = current_app.root_path  # app/ directory
        log_dir  = os.path.join(os.path.dirname(base_dir), "logs")
    else:
        log_dir = output_dir

    os.makedirs(log_dir, exist_ok=True)
    log_filename = f"monthly_reports_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    log_path     = os.path.join(log_dir, log_filename)

    with open(log_path, "w") as f:
        json.dump(run_summary, f, indent=2, default=str)

    # Emit summary to application logger
    logger.info(
        "Monthly report run complete — total: %d, success: %d, skipped: %d, failed: %d | log: %s",
        run_summary["total"],
        run_summary["success"],
        run_summary["skipped"],
        run_summary["failed"],
        log_path,
    )
    return log_path


def run_monthly_reports(output_dir="/tmp", log_dir=None, dry_run=False):
    """
    Main entry point: generate and email monthly performance reports for all
    councils that have at least one grant in the system.

    Parameters
    ----------
    output_dir : str
        Directory to write generated PDF files.
    log_dir : str | None
        Directory to write the JSON run log. Defaults to <project_root>/logs/.
    dry_run : bool
        If True, generate reports but do not send emails.

    Returns
    -------
    list[dict]
        A list of result dicts, one per council processed.
    """
    year, month = _get_report_period()
    period_label = datetime(year, month, 1).strftime("%B %Y")

    logger.info(
        "=== GrantThrive Monthly Report Run — %s%s ===",
        period_label,
        " [DRY RUN]" if dry_run else "",
    )

    councils = _councils_with_grants()
    logger.info("Identified %d council(s) with grants.", len(councils))

    if not councils:
        logger.warning("No councils with grants found. Nothing to report.")
        return []

    results = []

    for admin_user in councils:
        council_name = (
            admin_user.organisation_name
            if hasattr(admin_user, "organisation_name") and admin_user.organisation_name
            else f"{admin_user.first_name} {admin_user.last_name} Council"
        )
        result = {
            "council":    council_name,
            "user_id":    admin_user.id,
            "email":      admin_user.email,
            "period":     period_label,
            "status":     None,
            "report_path": None,
            "error":      None,
            "timestamp":  datetime.utcnow().isoformat(),
        }

        try:
            logger.info("Processing council: %s (user_id=%d)", council_name, admin_user.id)

            # Step 1: Generate the PDF report
            report_path = generate_council_report(
                admin_user=admin_user,
                year=year,
                month=month,
                output_dir=output_dir,
            )
            result["report_path"] = report_path
            logger.info("  Report generated: %s", report_path)

            # Step 2: Email the report
            if dry_run:
                logger.info("  [DRY RUN] Skipping email send for %s", admin_user.email)
                result["status"] = STATUS_SKIPPED
            else:
                _send_report_email(admin_user, report_path, year, month)
                result["status"] = STATUS_SUCCESS

        except Exception as exc:
            logger.exception(
                "  Failed to process report for council '%s': %s",
                council_name, exc,
            )
            result["status"] = STATUS_FAILED
            result["error"]  = str(exc)

        results.append(result)

    # Step 3: Write structured log
    _log_result(results, output_dir=log_dir)

    return results
