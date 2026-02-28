#!/usr/bin/env python3
"""
GrantThrive — Monthly Report Cron Runner
=========================================
Standalone script invoked by the system cron job on the 1st of each month
at 09:00.  It bootstraps the Flask application context and calls the
report generation / email delivery pipeline.

Crontab entry (add via: crontab -e):
    0 9 1 * * /usr/bin/python3 /path/to/grantthrive-platform/scripts/run_monthly_reports.py >> /path/to/logs/cron_monthly_reports.log 2>&1

Usage:
    python3 scripts/run_monthly_reports.py [--dry-run]
"""

import sys
import os
import argparse
import logging

# ── Ensure the project root is on the Python path ────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

# ── Bootstrap Flask app ───────────────────────────────────────────────────────
from app import create_app
from app.reports.monthly_reports import run_monthly_reports

# ── Logging setup ─────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(LOG_DIR, "monthly_reports.log"),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("monthly_report_runner")


def main():
    parser = argparse.ArgumentParser(
        description="GrantThrive — Automated Monthly Report Runner"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate reports but do not send emails.",
    )
    args = parser.parse_args()

    logger.info("Starting GrantThrive monthly report runner (dry_run=%s)", args.dry_run)

    app = create_app()
    with app.app_context():
        results = run_monthly_reports(
            output_dir=os.path.join(PROJECT_ROOT, "reports_output"),
            log_dir=LOG_DIR,
            dry_run=args.dry_run,
        )

    success = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed  = sum(1 for r in results if r["status"] == "failed")

    logger.info(
        "Run complete — %d processed | %d success | %d skipped | %d failed",
        len(results), success, skipped, failed,
    )

    # Exit with non-zero code if any reports failed
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
