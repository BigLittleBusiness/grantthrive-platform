#!/usr/bin/env python3
"""
GrantThrive — Monthly Report Pipeline Test
===========================================
Exercises the full report generation and logging pipeline using an in-memory
SQLite database populated with realistic synthetic data.  Email delivery is
mocked so no real messages are sent.

Run from the project root:
    python3 scripts/test_monthly_reports.py
"""

import sys
import os
import logging
import tempfile
import json
import glob
import importlib
import types
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

# ── Path setup ────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test_monthly_reports")

# ── Build a minimal Flask app that uses SQLite in-memory ─────────────────────
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from sqlalchemy import Numeric
from flask_login import UserMixin
from werkzeug.security import generate_password_hash

test_app = Flask(__name__)
test_app.config.update(
    SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY="test-secret-key",
    TESTING=True,
    MAIL_SERVER="localhost",
    MAIL_PORT=25,
    MAIL_USE_TLS=False,
    MAIL_USERNAME=None,
    MAIL_PASSWORD=None,
    MAIL_DEFAULT_SENDER="noreply@grantthrive.com.au",
    MAIL_SUPPRESS_SEND=True,
    WTF_CSRF_ENABLED=False,
)

test_db   = SQLAlchemy(test_app)
test_mail = Mail(test_app)

# ── Define models on the test db ─────────────────────────────────────────────

class User(UserMixin, test_db.Model):
    __tablename__ = "users"
    id            = test_db.Column(test_db.Integer, primary_key=True)
    username      = test_db.Column(test_db.String(80), unique=True, nullable=False)
    email         = test_db.Column(test_db.String(120), unique=True, nullable=False)
    password_hash = test_db.Column(test_db.String(255), nullable=False)
    first_name    = test_db.Column(test_db.String(50), nullable=False)
    last_name     = test_db.Column(test_db.String(50), nullable=False)
    role          = test_db.Column(test_db.String(20), nullable=False, default="staff")
    is_active     = test_db.Column(test_db.Boolean, default=True)
    created_at    = test_db.Column(test_db.DateTime, default=datetime.utcnow)
    last_login    = test_db.Column(test_db.DateTime)

    def is_admin(self): return self.role == "admin"
    def is_staff(self): return self.role in ["admin", "staff"]

    @property
    def full_name(self): return f"{self.first_name} {self.last_name}"


class Grant(test_db.Model):
    __tablename__ = "grants"
    id            = test_db.Column(test_db.Integer, primary_key=True)
    title         = test_db.Column(test_db.String(200), nullable=False)
    description   = test_db.Column(test_db.Text, nullable=False)
    category      = test_db.Column(test_db.String(100), nullable=False)
    total_budget  = test_db.Column(Numeric(12, 2), nullable=False)
    opens_at      = test_db.Column(test_db.DateTime, nullable=False)
    closes_at     = test_db.Column(test_db.DateTime, nullable=False)
    status        = test_db.Column(test_db.String(20), default="open")
    is_published  = test_db.Column(test_db.Boolean, default=True)
    created_by    = test_db.Column(test_db.Integer, test_db.ForeignKey("users.id"), nullable=False)
    created_at    = test_db.Column(test_db.DateTime, default=datetime.utcnow)
    updated_at    = test_db.Column(test_db.DateTime, default=datetime.utcnow)
    allow_multiple_applications = test_db.Column(test_db.Boolean, default=False)
    require_community_voting    = test_db.Column(test_db.Boolean, default=False)
    enable_mapping              = test_db.Column(test_db.Boolean, default=False)
    max_amount_per_application  = test_db.Column(Numeric(10, 2))
    min_amount_per_application  = test_db.Column(Numeric(10, 2))
    qr_code_data                = test_db.Column(test_db.Text)


class Application(test_db.Model):
    __tablename__       = "applications"
    id                  = test_db.Column(test_db.Integer, primary_key=True)
    grant_id            = test_db.Column(test_db.Integer, test_db.ForeignKey("grants.id"), nullable=False)
    applicant_id        = test_db.Column(test_db.Integer, test_db.ForeignKey("users.id"), nullable=False)
    organization_name   = test_db.Column(test_db.String(200), nullable=False)
    project_title       = test_db.Column(test_db.String(200), nullable=False)
    project_description = test_db.Column(test_db.Text, nullable=False)
    amount_requested    = test_db.Column(Numeric(10, 2), nullable=False)
    contact_person      = test_db.Column(test_db.String(100), nullable=False)
    contact_email       = test_db.Column(test_db.String(120), nullable=False)
    status              = test_db.Column(test_db.String(20), default="submitted")
    submitted_at        = test_db.Column(test_db.DateTime)
    reviewed_at         = test_db.Column(test_db.DateTime)
    decision_date       = test_db.Column(test_db.DateTime)
    total_score         = test_db.Column(test_db.Float)
    average_score       = test_db.Column(test_db.Float)
    community_votes     = test_db.Column(test_db.Integer, default=0)
    community_score     = test_db.Column(test_db.Float, default=0.0)
    created_at          = test_db.Column(test_db.DateTime, default=datetime.utcnow)
    updated_at          = test_db.Column(test_db.DateTime, default=datetime.utcnow)


class Review(test_db.Model):
    __tablename__  = "reviews"
    id             = test_db.Column(test_db.Integer, primary_key=True)
    application_id = test_db.Column(test_db.Integer, test_db.ForeignKey("applications.id"), nullable=False)
    reviewer_id    = test_db.Column(test_db.Integer, test_db.ForeignKey("users.id"), nullable=False)
    is_complete    = test_db.Column(test_db.Boolean, default=False)
    submitted_at   = test_db.Column(test_db.DateTime)
    total_score    = test_db.Column(test_db.Float, default=0.0)
    recommendation = test_db.Column(test_db.String(20))
    comments       = test_db.Column(test_db.Text)
    created_at     = test_db.Column(test_db.DateTime, default=datetime.utcnow)
    updated_at     = test_db.Column(test_db.DateTime, default=datetime.utcnow)


class CommunityVote(test_db.Model):
    __tablename__     = "community_votes"
    id                = test_db.Column(test_db.Integer, primary_key=True)
    application_id    = test_db.Column(test_db.Integer, test_db.ForeignKey("applications.id"), nullable=False)
    voter_id          = test_db.Column(test_db.Integer, test_db.ForeignKey("users.id"), nullable=True)
    voting_session_id = test_db.Column(test_db.Integer, nullable=False)
    vote_value        = test_db.Column(test_db.Integer, nullable=False)
    vote_type         = test_db.Column(test_db.String(20), default="rating")
    voted_at          = test_db.Column(test_db.DateTime, default=datetime.utcnow)
    updated_at        = test_db.Column(test_db.DateTime, default=datetime.utcnow)
    is_verified       = test_db.Column(test_db.Boolean, default=True)
    is_flagged        = test_db.Column(test_db.Boolean, default=False)


class VotingSession(test_db.Model):
    __tablename__ = "voting_sessions"
    id            = test_db.Column(test_db.Integer, primary_key=True)
    grant_id      = test_db.Column(test_db.Integer, test_db.ForeignKey("grants.id"), nullable=False)
    title         = test_db.Column(test_db.String(200), nullable=False)
    voting_type   = test_db.Column(test_db.String(20), default="rating")
    starts_at     = test_db.Column(test_db.DateTime, nullable=False)
    ends_at       = test_db.Column(test_db.DateTime, nullable=False)
    is_active     = test_db.Column(test_db.Boolean, default=True)
    is_published  = test_db.Column(test_db.Boolean, default=True)
    total_votes   = test_db.Column(test_db.Integer, default=0)
    total_voters  = test_db.Column(test_db.Integer, default=0)
    voting_weight = test_db.Column(test_db.Float, default=0.2)
    created_at    = test_db.Column(test_db.DateTime, default=datetime.utcnow)
    created_by    = test_db.Column(test_db.Integer, test_db.ForeignKey("users.id"), nullable=False)
    updated_at    = test_db.Column(test_db.DateTime, default=datetime.utcnow)


# ── Build the `app` package stub so report modules can import from it ─────────
app_pkg = types.ModuleType("app")
app_pkg.db   = test_db
app_pkg.mail = test_mail
sys.modules["app"] = app_pkg

models_mod = types.ModuleType("app.models")
models_mod.User          = User
models_mod.Grant         = Grant
models_mod.Application   = Application
models_mod.Review        = Review
models_mod.CommunityVote = CommunityVote
models_mod.VotingSession = VotingSession
sys.modules["app.models"] = models_mod
app_pkg.models = models_mod

# Create stub sub-packages so Python doesn't complain
for sub in ["app.reports", "app.auth", "app.main", "app.admin", "app.grants",
            "app.applications", "app.reviews", "app.workflows", "app.voting",
            "app.mapping", "app.public", "app.api"]:
    if sub not in sys.modules:
        sys.modules[sub] = types.ModuleType(sub)

# ── Import report modules directly (bypassing the full app factory) ───────────
import importlib.util

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

rg_path = os.path.join(PROJECT_ROOT, "app", "reports", "report_generator.py")
mr_path = os.path.join(PROJECT_ROOT, "app", "reports", "monthly_reports.py")

report_generator = _load_module("app.reports.report_generator", rg_path)
monthly_reports  = _load_module("app.reports.monthly_reports",  mr_path)

generate_council_report = report_generator.generate_council_report
run_monthly_reports     = monthly_reports.run_monthly_reports


# ── Seed helper ───────────────────────────────────────────────────────────────

def _seed_database():
    now = datetime.utcnow()
    prev_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    prev_month_end   = now.replace(day=1) - timedelta(seconds=1)

    councils = [
        User(username="council_sydney",
             email="admin@sydneycity.nsw.gov.au",
             password_hash=generate_password_hash("test"),
             first_name="Sydney City", last_name="Council", role="admin"),
        User(username="council_melbourne",
             email="admin@melbourne.vic.gov.au",
             password_hash=generate_password_hash("test"),
             first_name="Melbourne City", last_name="Council", role="admin"),
    ]
    test_db.session.add_all(councils)
    test_db.session.flush()

    applicant = User(
        username="applicant1", email="applicant@example.com",
        password_hash=generate_password_hash("test"),
        first_name="Jane", last_name="Smith", role="community",
    )
    test_db.session.add(applicant)
    test_db.session.flush()

    grant_list = []
    for council in councils:
        for i in range(2):
            g = Grant(
                title=f"{council.first_name} Community Grant #{i+1}",
                description="Supporting local community initiatives.",
                category="Community Development",
                total_budget=Decimal("50000.00"),
                opens_at=prev_month_start - timedelta(days=30),
                closes_at=prev_month_end,
                status="open",
                is_published=True,
                created_by=council.id,
            )
            test_db.session.add(g)
            grant_list.append((council, g))
    test_db.session.flush()

    statuses = ["approved", "approved", "rejected", "under_review", "submitted"]
    for council, grant in grant_list:
        for j, status in enumerate(statuses):
            submitted = prev_month_start + timedelta(days=j * 3)
            decision  = submitted + timedelta(days=7) if status in ("approved", "rejected") else None
            app_obj = Application(
                grant_id=grant.id,
                applicant_id=applicant.id,
                organization_name=f"Org {j+1}",
                project_title=f"Project {j+1} for {grant.title}",
                project_description="A community project.",
                amount_requested=Decimal(str(5000 + j * 1000)),
                contact_person="Jane Smith",
                contact_email="jane@example.com",
                status=status,
                submitted_at=submitted,
                decision_date=decision,
            )
            test_db.session.add(app_obj)
    test_db.session.flush()

    all_apps = Application.query.all()
    for i, app_obj in enumerate(all_apps[:6]):
        vote = CommunityVote(
            application_id=app_obj.id,
            voting_session_id=1,
            vote_value=(i % 5) + 1,
        )
        test_db.session.add(vote)

    for council, grant in grant_list[:2]:
        vs = VotingSession(
            grant_id=grant.id,
            title=f"Community Vote — {grant.title}",
            starts_at=prev_month_start,
            ends_at=prev_month_end,
            is_active=True,
            is_published=True,
            created_by=council.id,
        )
        test_db.session.add(vs)

    for app_obj in all_apps[:4]:
        r = Review(
            application_id=app_obj.id,
            reviewer_id=councils[0].id,
            is_complete=True,
            total_score=7.5,
            recommendation="approve",
            created_at=prev_month_start + timedelta(days=2),
        )
        test_db.session.add(r)

    test_db.session.commit()
    logger.info(
        "Test database seeded — %d councils, %d grants, %d applications.",
        len(councils), len(grant_list), Application.query.count(),
    )
    return councils


# ── Test runner ───────────────────────────────────────────────────────────────

def run_tests():
    with test_app.app_context():
        test_db.create_all()
        councils = _seed_database()

        with tempfile.TemporaryDirectory() as tmpdir:

            # ── Test 1: Report generation ─────────────────────────────────────
            logger.info("\n=== TEST 1: Report Generation ===")
            for council in councils:
                report_path = generate_council_report(
                    admin_user=council,
                    year=2026,
                    month=1,
                    output_dir=tmpdir,
                )
                assert os.path.exists(report_path), f"Report file not found: {report_path}"
                size_kb = os.path.getsize(report_path) / 1024
                logger.info(
                    "  ✓ Report generated for %s: %s (%.1f KB)",
                    council.first_name, os.path.basename(report_path), size_kb,
                )
                assert size_kb > 5, f"Report file too small ({size_kb:.1f} KB)"

            # ── Test 2: Monthly runner — dry run ──────────────────────────────
            logger.info("\n=== TEST 2: Monthly Report Runner (Dry Run) ===")
            with patch.object(monthly_reports, "_get_report_period", return_value=(2026, 1)):
                results = run_monthly_reports(
                    output_dir=tmpdir,
                    log_dir=tmpdir,
                    dry_run=True,
                )

            assert len(results) == 2, f"Expected 2 results, got {len(results)}"
            for r in results:
                assert r["status"] == "skipped", f"Expected skipped, got {r['status']}"
                logger.info("  ✓ Dry-run result for %s: %s", r["council"], r["status"])

            # ── Test 3: Log file creation ─────────────────────────────────────
            logger.info("\n=== TEST 3: Log File Creation ===")
            log_files = glob.glob(os.path.join(tmpdir, "monthly_reports_*.json"))
            assert len(log_files) >= 1, "No log file created"
            with open(log_files[0]) as f:
                log_data = json.load(f)
            assert log_data["total"]   == 2
            assert log_data["skipped"] == 2
            logger.info("  ✓ Log file: %s", os.path.basename(log_files[0]))
            logger.info(
                "  ✓ Log summary: total=%d, success=%d, skipped=%d, failed=%d",
                log_data["total"], log_data["success"],
                log_data["skipped"], log_data["failed"],
            )

            # ── Test 4: Email delivery (mocked) ───────────────────────────────
            logger.info("\n=== TEST 4: Email Delivery (Mocked) ===")
            mock_mail = MagicMock()
            with patch.object(monthly_reports, "mail", mock_mail):
                with patch.object(monthly_reports, "_get_report_period", return_value=(2026, 1)):
                    results_email = run_monthly_reports(
                        output_dir=tmpdir,
                        log_dir=tmpdir,
                        dry_run=False,
                    )

            assert mock_mail.send.call_count == 2, (
                f"Expected 2 email sends, got {mock_mail.send.call_count}"
            )
            logger.info(
                "  ✓ mail.send() called %d time(s) — one per council",
                mock_mail.send.call_count,
            )
            for r in results_email:
                assert r["status"] == "success", f"Expected success, got {r['status']}"
                logger.info("  ✓ Email result for %s: %s", r["council"], r["status"])

    logger.info("\n✅  All tests passed.")


if __name__ == "__main__":
    run_tests()
