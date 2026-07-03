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


@app.cli.command("seed-test-accounts")
@click.option(
    "--council-name",
    default="GrantThrive Test Council",
    show_default=True,
    help="Display name for the test council.",
)
@click.option(
    "--subdomain",
    default="gt-test",
    show_default=True,
    help="Subdomain for the test council (must be unique).",
)
@click.option(
    "--admin-email",
    default="council_admin_test@grantthrive.com",
    show_default=True,
    help="Email address for the council_admin test account.",
)
@click.option(
    "--admin-password",
    default="GZS7dR^oU%5Mm8Hz",
    show_default=False,
    help="Password for the council_admin test account.",
)
@click.option(
    "--staff-email",
    default="council_staff_test@grantthrive.com",
    show_default=True,
    help="Email address for the council_staff test account.",
)
@click.option(
    "--staff-password",
    default="AoR0VFl4lEyRxym#",
    show_default=False,
    help="Password for the council_staff test account.",
)
def seed_test_accounts_command(
    council_name, subdomain,
    admin_email, admin_password,
    staff_email, staff_password,
):
    """
    Create persistent test accounts for staging/UAT manual testing.

    Creates (idempotently — safe to run multiple times):
      1. A test Council record (subdomain: gt-test)
      2. A council_admin user  (council_admin_test@grantthrive.com)
      3. A council_staff user  (council_staff_test@grantthrive.com)

    Both accounts are immediately active and approved — no approval
    workflow is required.  Existing accounts are left untouched.

    \b
    Usage:
      FLASK_APP=wsgi.py flask seed-test-accounts
      FLASK_APP=wsgi.py flask seed-test-accounts --subdomain my-test
    """
    from app.models import Council, User
    from app.common.password import hash_password
    from app.common.encryption import hmac_index

    click.echo(click.style("GrantThrive — Seed Test Accounts", fg="green", bold=True))
    click.echo("")

    # ── 1. Ensure the test council exists ────────────────────────────────────
    council = Council.query.filter_by(subdomain=subdomain).first()
    if council:
        click.echo(
            click.style(
                f"  ✓ Council already exists: '{council.name}' "
                f"(id={council.id}, subdomain={council.subdomain})",
                fg="yellow",
            )
        )
    else:
        slug = Council.make_slug(council_name)
        council = Council(
            name             = council_name,
            subdomain        = subdomain,
            slug             = slug,
            state            = "QLD",
            plan             = "medium",
            contact_email    = "test@grantthrive.com",
            website_url      = "https://grantthrive.com",
            primary_colour   = "#15803d",
            secondary_colour = "#166534",
            is_active        = True,
            addon_community_voting = True,
            addon_grant_mapping    = True,
        )
        db.session.add(council)
        db.session.flush()  # populate council.id before creating users
        click.echo(
            click.style(
                f"  ✓ Council created: '{council.name}' "
                f"(id={council.id}, subdomain={council.subdomain})",
                fg="green",
            )
        )

    # ── Helper: create or skip a user ────────────────────────────────────────
    def _ensure_user(email, password, role, first_name, last_name):
        """Create user if not present; skip with a notice if already exists."""
        hmac = hmac_index(email.strip().lower())
        existing = User.query.filter_by(email_hmac=hmac).first()
        if existing:
            click.echo(
                click.style(
                    f"  ✓ {role} already exists: {email} (id={existing.id}) — skipped",
                    fg="yellow",
                )
            )
            return existing

        base_username = email.split("@")[0].replace(".", "_")
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1

        user = User(
            username      = username,
            first_name    = first_name,
            last_name     = last_name,
            role          = role,
            council_id    = council.id,
            is_active     = True,
            is_approved   = True,
            position      = "Test Account",
            department    = "Quality Assurance",
        )
        user.set_email(email)
        user.set_password(password)
        db.session.add(user)
        click.echo(
            click.style(
                f"  ✓ {role} created: {email} (username={username})",
                fg="green",
            )
        )
        return user

    # ── 2. council_admin test account ────────────────────────────────────────
    _ensure_user(
        email      = admin_email,
        password   = admin_password,
        role       = "council_admin",
        first_name = "Test",
        last_name  = "Admin",
    )

    # ── 3. council_staff test account ────────────────────────────────────────
    _ensure_user(
        email      = staff_email,
        password   = staff_password,
        role       = "council_staff",
        first_name = "Test",
        last_name  = "Staff",
    )

    # ── Commit everything ────────────────────────────────────────────────────
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        click.echo(
            click.style(f"\n  ✗ Database commit failed: {exc}", fg="red", bold=True)
        )
        raise SystemExit(1)

    click.echo("")
    click.echo(click.style("  All test accounts are ready.", fg="green", bold=True))
    click.echo("")
    click.echo(
        "  ┌─────────────────────────────────────────────────────────────┐\n"
        "  │  COUNCIL ADMIN TEST ACCOUNT                                 │\n"
        f"  │  Email    : {admin_email:<47} │\n"
        "  │  Password : (set via --admin-password option)               │\n"
        "  │  Role     : council_admin                                   │\n"
        f"  │  Council  : {council_name:<47} │\n"
        "  ├─────────────────────────────────────────────────────────────┤\n"
        "  │  COUNCIL STAFF TEST ACCOUNT                                 │\n"
        f"  │  Email    : {staff_email:<47} │\n"
        "  │  Password : (set via --staff-password option)               │\n"
        "  │  Role     : council_staff                                   │\n"
        f"  │  Council  : {council_name:<47} │\n"
        "  └─────────────────────────────────────────────────────────────┘"
    )
    click.echo("")
    click.echo(
        click.style(
            "  ⚠  These are test credentials. Do not use in production.",
            fg="yellow",
        )
    )
