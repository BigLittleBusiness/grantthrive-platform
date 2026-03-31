#!/usr/bin/env python3
"""
GrantThrive — Monthly Report Dry-Run Test (v2)
===============================================
Standalone test that bootstraps a minimal in-memory SQLite database with
the real schema, seeds synthetic data, and runs the full monthly report
pipeline in dry-run mode.

This validates:
  1. Council discovery (councils with grants)
  2. PDF report generation for each council
  3. JSON run log creation
  4. Email dry-run logging (no real emails sent)

Usage:
    python3 scripts/test_monthly_reports_v2.py
"""

import sys
import os
import json
import logging
import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# ── Ensure project root is on path ────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test_monthly_reports_v2")

# ── Minimal Flask app with in-memory SQLite ───────────────────────────────────
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from sqlalchemy import Numeric
from datetime import datetime, timezone

app = Flask(__name__)
app.config.update(
    TESTING=True,
    SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAIL_SUPPRESS_SEND=True,
    SECRET_KEY="test-secret",
    AWS_SES_ENABLED="false",
)

db  = SQLAlchemy(app)
mail = Mail(app)

# ── Stub the app package so real imports resolve to our test db ───────────────
import types
app_mod = types.ModuleType("app")
app_mod.db   = db
app_mod.mail = mail
sys.modules["app"] = app_mod

# ── Stub common.encryption so models can be imported ─────────────────────────
enc_mod = types.ModuleType("app.common")
sys.modules["app.common"] = enc_mod

enc_sub = types.ModuleType("app.common.encryption")

class _PassThrough(db.TypeDecorator):
    impl = db.String
    cache_ok = True
    def process_bind_processor(self, dialect):
        return None
    def process_result_value(self, value, dialect):
        return value

def EncryptedString(length=500):
    return db.String(length)

def hmac_index(value):
    import hashlib
    return hashlib.sha256(value.encode()).hexdigest()

enc_sub.EncryptedString = EncryptedString
enc_sub.hmac_index = hmac_index
sys.modules["app.common.encryption"] = enc_sub

# Stub password module
pw_mod = types.ModuleType("app.common.password")
pw_mod.hash_password = lambda p: "hashed_" + p
pw_mod.verify_password = lambda h, p: (True, False)
sys.modules["app.common.password"] = pw_mod

# Stub qrcode
qr_mod = types.ModuleType("qrcode")
class _FakeQR:
    def __init__(self, **kw): pass
    def add_data(self, d): pass
    def make(self, fit=True): pass
    def make_image(self, **kw): return self
    def save(self, buf, format=None): buf.write(b"")
qr_mod.QRCode = _FakeQR
sys.modules["qrcode"] = qr_mod

# ── Minimal models matching real schema ───────────────────────────────────────
import re

class Council(db.Model):
    __tablename__ = "councils"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    subdomain   = db.Column(db.String(100), unique=True, nullable=False)
    slug        = db.Column(db.String(100), unique=True, nullable=False)
    state       = db.Column(db.String(50))
    country     = db.Column(db.String(50), default="Australia")
    plan        = db.Column(db.String(20), default="small")
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    grants      = db.relationship("Grant", backref="council", lazy="dynamic", cascade="all, delete-orphan")
    users       = db.relationship("User", foreign_keys="User.council_id", backref="council", lazy="dynamic")

class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(500), nullable=False)
    email_hmac    = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name    = db.Column(db.String(50), nullable=False)
    last_name     = db.Column(db.String(50), nullable=False)
    role          = db.Column(db.String(30), nullable=False, default="community_member")
    council_id    = db.Column(db.Integer, db.ForeignKey("councils.id"), nullable=True)
    is_active     = db.Column(db.Boolean, default=True)
    is_approved   = db.Column(db.Boolean, default=True)
    organisation  = db.Column(db.String(300))
    email_opt_in  = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_grants = db.relationship("Grant", foreign_keys="Grant.created_by", backref="creator", lazy="dynamic")
    applications   = db.relationship("Application", backref="applicant", lazy="dynamic")
    reviews        = db.relationship("Review", backref="reviewer", lazy="dynamic")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Grant(db.Model):
    __tablename__ = "grants"
    id          = db.Column(db.Integer, primary_key=True)
    council_id  = db.Column(db.Integer, db.ForeignKey("councils.id"), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category    = db.Column(db.String(100), nullable=False)
    total_budget= db.Column(Numeric(12, 2), nullable=False)
    max_amount_per_application = db.Column(Numeric(10, 2))
    opens_at    = db.Column(db.DateTime, nullable=False)
    closes_at   = db.Column(db.DateTime, nullable=False)
    status      = db.Column(db.String(20), default="draft")
    is_published = db.Column(db.Boolean, default=False)
    allow_multiple_applications = db.Column(db.Boolean, default=False)
    require_community_voting = db.Column(db.Boolean, default=False)
    enable_mapping = db.Column(db.Boolean, default=False)
    created_by  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    assigned_reviewer_ids = db.Column(db.Text, default="[]", nullable=False)
    required_approvals    = db.Column(db.Integer, default=1, nullable=False)
    applications = db.relationship("Application", backref="grant", lazy="dynamic", cascade="all, delete-orphan")

class Application(db.Model):
    __tablename__ = "applications"
    id           = db.Column(db.Integer, primary_key=True)
    grant_id     = db.Column(db.Integer, db.ForeignKey("grants.id"), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    organization_name   = db.Column(db.String(200), nullable=False)
    project_title       = db.Column(db.String(200), nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    amount_requested    = db.Column(Numeric(10, 2), nullable=False)
    contact_person = db.Column(db.String(100), nullable=False)
    contact_email  = db.Column(db.String(500), nullable=False)
    status       = db.Column(db.String(20), default="draft")
    submitted_at = db.Column(db.DateTime)
    reviewed_at  = db.Column(db.DateTime)
    decision_date= db.Column(db.DateTime)
    total_score   = db.Column(db.Float)
    average_score = db.Column(db.Float)
    community_votes = db.Column(db.Integer, default=0)
    community_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviews   = db.relationship("Review", backref="application", lazy="dynamic", cascade="all, delete-orphan")
    votes     = db.relationship("CommunityVote", back_populates="application", lazy="dynamic", cascade="all, delete-orphan")

class Review(db.Model):
    __tablename__ = "reviews"
    id             = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    reviewer_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_complete    = db.Column(db.Boolean, default=False)
    submitted_at   = db.Column(db.DateTime)
    total_score    = db.Column(db.Float, default=0.0)
    recommendation = db.Column(db.String(20))
    comments       = db.Column(db.Text)
    created_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class VotingSession(db.Model):
    __tablename__ = "voting_sessions"
    id         = db.Column(db.Integer, primary_key=True)
    grant_id   = db.Column(db.Integer, db.ForeignKey("grants.id"), nullable=False)
    council_id = db.Column(db.Integer, db.ForeignKey("councils.id"), nullable=True)
    title      = db.Column(db.String(200))
    is_active  = db.Column(db.Boolean, default=True)
    starts_at  = db.Column(db.DateTime)
    ends_at    = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class CommunityVote(db.Model):
    __tablename__ = "community_votes"
    id                = db.Column(db.Integer, primary_key=True)
    application_id    = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    voter_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    voting_session_id = db.Column(db.Integer, db.ForeignKey("voting_sessions.id"), nullable=False)
    vote_value        = db.Column(db.Integer, nullable=False)
    vote_type         = db.Column(db.String(20), default="rating")
    created_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    application       = db.relationship("Application", back_populates="votes")

# ── Patch models into sys.modules ─────────────────────────────────────────────
models_mod = types.ModuleType("app.models")
models_mod.Council        = Council
models_mod.User           = User
models_mod.Grant          = Grant
models_mod.Application    = Application
models_mod.Review         = Review
models_mod.VotingSession  = VotingSession
models_mod.CommunityVote  = CommunityVote
sys.modules["app.models"] = models_mod

# Stub email_service
email_svc_mod = types.ModuleType("app.common.email_service")
def _stub_send_monthly_report_pdf(to_email, first_name, council_name, period_label, report_path):
    logger.info(
        "DEV MODE — Email not sent (Attachment: %s): To: %s Subject: GrantThrive — Monthly Performance Report: %s — %s",
        os.path.basename(report_path), to_email, council_name, period_label,
    )
    return True
email_svc_mod.send_monthly_report_pdf = _stub_send_monthly_report_pdf
sys.modules["app.common.email_service"] = email_svc_mod

email_common_mod = types.ModuleType("app.common")
email_common_mod.email_service = email_svc_mod
sys.modules["app.common"] = email_common_mod

# ── Load app.reports modules directly from file paths ──────────────────────────────
import importlib.util

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

reports_pkg = types.ModuleType("app.reports")
sys.modules["app.reports"] = reports_pkg

report_generator = _load_module(
    "app.reports.report_generator",
    os.path.join(PROJECT_ROOT, "app", "reports", "report_generator.py"),
)
reports_pkg.report_generator = report_generator

monthly_reports = _load_module(
    "app.reports.monthly_reports",
    os.path.join(PROJECT_ROOT, "app", "reports", "monthly_reports.py"),
)
reports_pkg.monthly_reports = monthly_reports

# ── Seed test data ────────────────────────────────────────────────────────────
def seed_data():
    now = datetime.now(timezone.utc)
    prev_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    prev_month_mid   = prev_month_start + timedelta(days=10)
    prev_month_end   = now.replace(day=1) - timedelta(seconds=1)

    councils_data = [
        ("City of Melbourne",       "cityofmelbourne",       "city-of-melbourne",       "VIC"),
        ("Bayside City Council",    "baysidecitycouncil",    "bayside-city-council",    "VIC"),
        ("Moreland City Council",   "morelandcitycouncil",   "moreland-city-council",   "VIC"),
    ]

    for cname, subdomain, slug, state in councils_data:
        council = Council(name=cname, subdomain=subdomain, slug=slug, state=state)
        db.session.add(council)
        db.session.flush()

        # Admin user
        admin = User(
            username=f"admin_{slug.replace('-', '_')}",
            email=f"admin@{subdomain}.vic.gov.au",
            email_hmac=f"hmac_{subdomain}",
            password_hash="hashed_pass",
            first_name="Council",
            last_name="Admin",
            role="council_admin",
            council_id=council.id,
            is_active=True,
            is_approved=True,
        )
        db.session.add(admin)
        db.session.flush()

        # Applicant user
        applicant = User(
            username=f"applicant_{slug.replace('-', '_')}",
            email=f"applicant@example.com_{subdomain}",
            email_hmac=f"hmac_app_{subdomain}",
            password_hash="hashed_pass",
            first_name="Test",
            last_name="Applicant",
            role="community_member",
            council_id=council.id,
            is_active=True,
            is_approved=True,
        )
        db.session.add(applicant)
        db.session.flush()

        # Grants
        for i in range(2):
            grant = Grant(
                council_id=council.id,
                title=f"{cname} Community Grant {i+1}",
                description="Supporting local community projects.",
                category="Community",
                total_budget=Decimal("50000.00"),
                max_amount_per_application=Decimal("10000.00"),
                opens_at=prev_month_start,
                closes_at=prev_month_end,
                status="open",
                is_published=True,
                created_by=admin.id,
            )
            db.session.add(grant)
            db.session.flush()

            # Voting session
            vs = VotingSession(
                grant_id=grant.id,
                council_id=council.id,
                title=f"Community Vote — {grant.title}",
                is_active=True,
                starts_at=prev_month_start,
                ends_at=prev_month_end,
            )
            db.session.add(vs)
            db.session.flush()

            # Applications
            statuses = ["approved", "rejected", "under_review", "submitted"]
            for j, status in enumerate(statuses):
                app_obj = Application(
                    grant_id=grant.id,
                    applicant_id=applicant.id,
                    organization_name=f"Org {j+1}",
                    project_title=f"Project {j+1}",
                    project_description="A great community project.",
                    amount_requested=Decimal(str(3000 + j * 500)),
                    contact_person="Jane Doe",
                    contact_email=f"jane{j}@example.com",
                    status=status,
                    submitted_at=prev_month_mid,
                    decision_date=prev_month_mid + timedelta(days=5) if status in ("approved", "rejected") else None,
                )
                db.session.add(app_obj)
                db.session.flush()

                # Review
                review = Review(
                    application_id=app_obj.id,
                    reviewer_id=admin.id,
                    is_complete=(status in ("approved", "rejected")),
                    total_score=7.5,
                    recommendation="approve" if status == "approved" else "reject",
                    created_at=prev_month_mid,
                )
                db.session.add(review)
                db.session.flush()

                # Community vote
                vote = CommunityVote(
                    application_id=app_obj.id,
                    voting_session_id=vs.id,
                    vote_value=4,
                )
                db.session.add(vote)

    db.session.commit()
    logger.info("Test data seeded successfully.")


# ── Main test runner ──────────────────────────────────────────────────────────
def main():
    with app.app_context():
        db.create_all()
        seed_data()

        # Use the already-loaded monthly reports module
        run_monthly_reports = monthly_reports.run_monthly_reports

        output_dir = tempfile.mkdtemp(prefix="gt_reports_test_")
        log_dir    = tempfile.mkdtemp(prefix="gt_logs_test_")

        logger.info("=" * 60)
        logger.info("Running monthly reports pipeline (DRY RUN)...")
        logger.info("Output dir: %s", output_dir)
        logger.info("Log dir:    %s", log_dir)
        logger.info("=" * 60)

        results = run_monthly_reports(
            output_dir=output_dir,
            log_dir=log_dir,
            dry_run=True,
        )

        # ── Validate results ──────────────────────────────────────────────────
        assert results, "No results returned — expected at least one council to be processed."

        success = sum(1 for r in results if r["status"] == "success")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        failed  = sum(1 for r in results if r["status"] == "failed")

        logger.info("=" * 60)
        logger.info("RESULTS: total=%d  success=%d  skipped=%d  failed=%d",
                    len(results), success, skipped, failed)

        for r in results:
            status_icon = "✓" if r["status"] in ("success", "skipped") else "✗"
            logger.info("  %s  %s  [%s]  PDF: %s",
                        status_icon, r["council"], r["status"], r.get("report_path"))
            if r.get("error"):
                logger.error("     ERROR: %s", r["error"])

        # Verify PDFs exist
        for r in results:
            if r.get("report_path"):
                assert os.path.exists(r["report_path"]), f"PDF not found: {r['report_path']}"
                size = os.path.getsize(r["report_path"])
                logger.info("  PDF size: %d bytes — %s", size, os.path.basename(r["report_path"]))

        # Verify JSON log exists
        log_files = [f for f in os.listdir(log_dir) if f.startswith("monthly_reports_")]
        assert log_files, "No JSON log file was created."
        log_path = os.path.join(log_dir, log_files[0])
        with open(log_path) as f:
            log_data = json.load(f)
        logger.info("JSON log: %s", log_path)
        logger.info("  run_at=%s  total=%d  success=%d  skipped=%d  failed=%d",
                    log_data["run_at"], log_data["total"], log_data["success"],
                    log_data["skipped"], log_data["failed"])

        assert failed == 0, f"{failed} report(s) failed — check errors above."
        logger.info("=" * 60)
        logger.info("ALL TESTS PASSED ✓")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
