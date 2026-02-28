#!/usr/bin/env python3
"""
GrantThrive — Flask CLI Management Commands
============================================
Run with:  flask <command>

Available commands:
  run-monthly-reports   Generate and email monthly performance reports
                        for all councils with grants.
"""

import os
import click
from app import create_app, db

app = create_app()


@app.cli.command("run-monthly-reports")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Generate reports but do not send emails.",
)
@click.option(
    "--output-dir",
    default="/tmp",
    show_default=True,
    help="Directory to write generated PDF reports.",
)
def run_monthly_reports_command(dry_run, output_dir):
    """
    Generate and email monthly performance reports for all councils.

    This command is designed to be executed on the 1st of each month at 09:00
    via the system cron scheduler.  It identifies every council (admin user)
    that has at least one grant in the system, generates a comprehensive PDF
    performance report for the previous calendar month, and emails it to the
    council's admin user(s).

    \b
    Metrics covered:
      - Grant program overview and status
      - Applications received, approved, rejected, pending
      - Application processing times (avg / min / max)
      - Budget allocation and utilisation per grant
      - Community engagement (votes, ratings, sessions)
      - Estimated cost savings vs. manual processing
      - Review and assessment activity
    """
    from app.reports.monthly_reports import run_monthly_reports

    click.echo(
        click.style(
            f"GrantThrive Monthly Report Runner{'  [DRY RUN]' if dry_run else ''}",
            fg="green", bold=True,
        )
    )

    results = run_monthly_reports(
        output_dir=output_dir,
        dry_run=dry_run,
    )

    success = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed  = sum(1 for r in results if r["status"] == "failed")

    click.echo(f"\nResults: {len(results)} councils processed")
    click.echo(click.style(f"  ✓ Success: {success}", fg="green"))
    click.echo(click.style(f"  ⊘ Skipped: {skipped}", fg="yellow"))
    click.echo(click.style(f"  ✗ Failed:  {failed}",  fg="red" if failed else "white"))

    if failed:
        raise SystemExit(1)
