"""
GrantThrive - Automated Monthly Report Runner
==============================================
Orchestrates the generation and email delivery of monthly performance reports
for every council (tenant) that has at least one grant in the system.

Designed to be invoked:
  - Via the Flask CLI:      flask run-monthly-reports
  - Via the cron scheduler: scripts/run_monthly_reports.py
  - Via APScheduler:        configured in app/__init__.py (optional)

Execution schedule: 1st of each month at 09:00 local time.
"""

import os
import logging
import json
from datetime import datetime, timedelta, timezone

from flask import current_app

from app import db
from app.models import Council, User, Grant
from app.reports.report_generator import generate_council_report
from app.common import email_service

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
    today = datetime.now(timezone.utc)
    first_of_current = today.replace(day=1)
    last_of_previous = first_of_current - timedelta(days=1)
    return last_of_previous.year, last_of_previous.month


def _councils_with_grants():
    """
    Return a list of Council records that own at least one grant.
    """
    councils = (
        db.session.query(Council)
        .join(Grant, Grant.council_id == Council.id)
        .filter(Council.is_active == True)
        .distinct()
        .all()
    )
    return councils


def _send_report_email(council, report_path, year, month):
    """
    Email the PDF report to all council_admin users associated with the council.
    Uses the central SES email service.

    Parameters
    ----------
    council : Council
    report_path : str    Absolute path to the generated PDF.
    year : int
    month : int
    """
    period_label = datetime(year, month, 1).strftime("%B %Y")
    
    # Find all active council admins for this council
    admins = User.query.filter_by(
        council_id=council.id, 
        role='council_admin', 
        is_active=True
    ).all()
    
    if not admins:
        logger.warning("No active council admins found for %s", council.name)
        return False
        
    subject = f"GrantThrive — Monthly Performance Report: {council.name} — {period_label}"
    
    # Use SES to send the email (we'll implement send_monthly_report_pdf in email_service.py)
    success_count = 0
    for admin in admins:
        # Note: In a real production system with SES, we'd need a way to attach files.
        # Since email_service.py doesn't currently support attachments, we'll either need
        # to add attachment support to it, or fall back to Flask-Mail for this specific task,
        # or upload the PDF to S3 and send a link.
        # Let's add attachment support to email_service.py
        try:
            res = email_service.send_monthly_report_pdf(
                to_email=admin.email,
                first_name=admin.first_name,
                council_name=council.name,
                period_label=period_label,
                report_path=report_path
            )
            if res:
                success_count += 1
                logger.info(
                    "Report email sent to %s (%s) for period %s",
                    admin.email, council.name, period_label,
                )
        except Exception as e:
            logger.error("Failed to send report email to %s: %s", admin.email, e)
            
    return success_count > 0


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
        "run_at":   datetime.now(timezone.utc).isoformat(),
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
    log_filename = f"monthly_reports_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
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

    for council in councils:
        result = {
            "council":    council.name,
            "council_id": council.id,
            "period":     period_label,
            "status":     None,
            "report_path": None,
            "error":      None,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        }

        try:
            logger.info("Processing council: %s (id=%d)", council.name, council.id)

            # Step 1: Generate the PDF report
            report_path = generate_council_report(
                council=council,
                year=year,
                month=month,
                output_dir=output_dir,
            )
            result["report_path"] = report_path
            logger.info("  Report generated: %s", report_path)

            # Step 2: Email the report
            if dry_run:
                logger.info("  [DRY RUN] Skipping email send for %s", council.name)
                result["status"] = STATUS_SKIPPED
            else:
                success = _send_report_email(council, report_path, year, month)
                if success:
                    result["status"] = STATUS_SUCCESS
                else:
                    result["status"] = STATUS_FAILED
                    result["error"] = "Failed to send to any admin"

        except Exception as exc:
            logger.exception(
                "  Failed to process report for council '%s': %s",
                council.name, exc,
            )
            result["status"] = STATUS_FAILED
            result["error"]  = str(exc)

        results.append(result)

    # Step 3: Write structured log
    _log_result(results, output_dir=log_dir)

    return results
