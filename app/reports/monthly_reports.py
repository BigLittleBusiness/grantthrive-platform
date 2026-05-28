"""
GrantThrive - Automated Monthly Report Runner
==============================================
Orchestrates the generation and email delivery of monthly performance reports
for every council (tenant) that has at least one grant in the system.

The reports are generated as PDF documents and stored in S3. If S3 is not configured,
reports fall back to local filesystem storage (development only).

Designed to be invoked:
  - Via the Flask CLI:      flask run-monthly-reports
  - Via the cron scheduler: scripts/run_monthly_reports.py
  - Via APScheduler:        configured in app/__init__.py (optional)

Execution schedule: 1st of each month at 09:00 local time.
"""

import os
import logging
import json
import io
from datetime import datetime, timedelta, timezone

from flask import current_app

from app import db
from app.models import Council, User, Grant
from app.reports.report_generator import generate_council_report
from app.common import email_service
from app.common.s3_service import s3_service

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


def _send_report_email(council, report_data, year, month):
    """
    Email the PDF report to all council_admin users associated with the council.

    Parameters
    ----------
    council : Council
        The council that the report is for.
    report_data : dict
        Report metadata dict from generate_council_report() with keys:
        - 'filename': original filename
        - 's3_key': S3 key if uploaded (None if local)
        - 'local_path': local path if written locally (None if S3)
        - 'content': BytesIO buffer with PDF content
    year : int
        Report year.
    month : int
        Report month.

    Returns
    -------
    bool
        True if at least one email was sent successfully.
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
    
    # Prepare email content
    text = f"""Dear {council.name} Team,

Your monthly performance report for {period_label} is attached.

This report includes:
- Grant overview and status
- Applications & processing metrics
- Budget allocation analysis
- Community engagement metrics
- Cost savings analysis
- Reviewer performance

Best regards,
The GrantThrive Platform
"""

    html = f"""<html><body>
<p>Dear {council.name} Team,</p>
<p>Your monthly performance report for <strong>{period_label}</strong> is attached.</p>
<h3>Report Contents:</h3>
<ul>
<li>Grant overview and status</li>
<li>Applications & processing metrics</li>
<li>Budget allocation analysis</li>
<li>Community engagement metrics</li>
<li>Cost savings analysis</li>
<li>Reviewer performance</li>
</ul>
<p>Best regards,<br/>The GrantThrive Platform</p>
</body></html>"""

    success_count = 0
    for admin in admins:
        try:
            # Get PDF content from buffer
            report_data["content"].seek(0)
            pdf_content = report_data["content"].read()
            
            res = email_service.send_monthly_report_pdf(
                to_email=admin.email,
                first_name=admin.first_name,
                council_name=council.name,
                period_label=period_label,
                subject=subject,
                text=text,
                html=html,
                pdf_filename=report_data["filename"],
                pdf_content=pdf_content,
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
    Write a structured JSON log of the run results to S3 and/or local disk.

    Parameters
    ----------
    results : list[dict]
        List of result dicts from run_monthly_reports.
    output_dir : str | None
        Optional directory for local filesystem log (development only).
    """
    run_summary = {
        "run_at":   datetime.now(timezone.utc).isoformat(),
        "total":    len(results),
        "success":  sum(1 for r in results if r["status"] == STATUS_SUCCESS),
        "skipped":  sum(1 for r in results if r["status"] == STATUS_SKIPPED),
        "failed":   sum(1 for r in results if r["status"] == STATUS_FAILED),
        "results":  results,
    }

    log_filename = f"monthly_reports_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    log_content = json.dumps(run_summary, indent=2, default=str)

    # ── Write to S3 if configured ──────────────────────────────────────────────
    if s3_service.is_configured():
        try:
            s3_key = s3_service.make_log_key(log_filename)
            buf = io.BytesIO(log_content.encode("utf-8"))
            s3_service.upload_fileobj(
                buf,
                s3_key,
                content_type="application/json",
                extra_metadata={"purpose": "monthly_reports_log"}
            )
            logger.info("Report log uploaded to S3: %s", s3_key)
        except RuntimeError as exc:
            logger.error("Failed to upload report log to S3: %s", exc)
    
    # ── Write to local filesystem if output_dir provided (fallback/development) ─
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
            log_path = os.path.join(output_dir, log_filename)
            with open(log_path, "w") as f:
                f.write(log_content)
            logger.info("Report log written to: %s", log_path)
        except Exception as exc:
            logger.error("Failed to write report log locally: %s", exc)

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

    Reports are generated as PDF documents stored in S3 (or local filesystem
    if S3 is not configured).

    Parameters
    ----------
    output_dir : str
        Directory for local fallback (development/testing only).
    log_dir : str | None
        Directory for log files. Defaults to local only if S3 not configured.
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
            "s3_key":     None,
            "local_path": None,
            "error":      None,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        }

        try:
            logger.info("Processing council: %s (id=%d)", council.name, council.id)

            # Step 1: Generate the PDF report in-memory and upload to S3 (or save locally)
            report_data = generate_council_report(
                council=council,
                year=year,
                month=month,
                output_dir=output_dir,
            )
            
            result["s3_key"] = report_data.get("s3_key")
            result["local_path"] = report_data.get("local_path")
            
            storage_location = report_data.get("s3_key") or report_data.get("local_path") or "memory"
            logger.info("  Report generated: %s", storage_location)

            # Step 2: Email the report
            if dry_run:
                logger.info("  [DRY RUN] Skipping email send for %s", council.name)
                result["status"] = STATUS_SKIPPED
            else:
                success = _send_report_email(council, report_data, year, month)
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

    # Step 3: Write structured log to S3 and/or local filesystem
    _log_result(results, output_dir=log_dir)

    return results
