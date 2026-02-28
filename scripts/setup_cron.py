#!/usr/bin/env python3
"""
GrantThrive — Cron Job Setup Script
=====================================
Installs (or updates) the system crontab entry that triggers the monthly
performance report generation on the 1st of each month at 09:00.

Usage:
    python3 scripts/setup_cron.py [--remove]

Options:
    --remove    Remove the cron job instead of installing it.
"""

import sys
import os
import argparse
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RUNNER       = os.path.join(SCRIPT_DIR, "run_monthly_reports.py")
LOG_DIR      = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE     = os.path.join(LOG_DIR, "cron_monthly_reports.log")

# Cron expression: minute hour day-of-month month day-of-week
# "At 09:00 on day-of-month 1"
CRON_SCHEDULE = "0 9 1 * *"
CRON_COMMENT  = "GrantThrive monthly performance reports"
CRON_LINE     = (
    f"{CRON_SCHEDULE} "
    f"/usr/bin/python3 {RUNNER} "
    f">> {LOG_FILE} 2>&1  # {CRON_COMMENT}"
)


def _read_crontab():
    """Return current crontab lines as a list."""
    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return result.stdout.splitlines()
    # No existing crontab is fine
    return []


def _write_crontab(lines):
    """Write a list of lines back to the crontab."""
    content = "\n".join(lines) + "\n"
    proc = subprocess.run(
        ["crontab", "-"],
        input=content, text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        logger.error("Failed to write crontab: %s", proc.stderr)
        sys.exit(1)


def install_cron():
    """Install the monthly report cron job."""
    os.makedirs(LOG_DIR, exist_ok=True)
    lines = _read_crontab()

    # Remove any existing GrantThrive monthly report lines
    lines = [l for l in lines if CRON_COMMENT not in l]

    lines.append(CRON_LINE)
    _write_crontab(lines)
    logger.info("Cron job installed: %s", CRON_LINE)
    logger.info(
        "The monthly report runner will execute on the 1st of each month at 09:00."
    )


def remove_cron():
    """Remove the monthly report cron job."""
    lines = _read_crontab()
    original_count = len(lines)
    lines = [l for l in lines if CRON_COMMENT not in l]

    if len(lines) == original_count:
        logger.info("No GrantThrive monthly report cron job found — nothing to remove.")
        return

    _write_crontab(lines)
    logger.info("Cron job removed.")


def main():
    parser = argparse.ArgumentParser(
        description="Install or remove the GrantThrive monthly report cron job."
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove the cron job instead of installing it.",
    )
    args = parser.parse_args()

    if args.remove:
        remove_cron()
    else:
        install_cron()


if __name__ == "__main__":
    main()
