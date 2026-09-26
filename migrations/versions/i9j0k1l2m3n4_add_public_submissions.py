"""Add encrypted database-first public form submissions.

Revision ID: i9j0k1l2m3n4
Revises: g7h8i9j0k1l2
Create Date: 2026-09-26
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "i9j0k1l2m3n4"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "public_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_type", sa.String(length=20), nullable=False),
        sa.Column("contact_type", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="new"),
        # AES-256-GCM ciphertext is stored in these VARCHAR columns.
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("email", sa.String(length=500), nullable=False),
        sa.Column("organisation", sa.String(length=500), nullable=True),
        sa.Column("phone", sa.String(length=200), nullable=True),
        sa.Column("message", sa.String(length=8000), nullable=True),
        sa.Column("internal_note", sa.String(length=8000), nullable=True),
        sa.Column("notification_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("notification_attempted_at", sa.DateTime(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_public_submissions_submission_type", "public_submissions", ["submission_type"])
    op.create_index("ix_public_submissions_contact_type", "public_submissions", ["contact_type"])
    op.create_index("ix_public_submissions_status", "public_submissions", ["status"])
    op.create_index("ix_public_submissions_received_at", "public_submissions", ["received_at"])


def downgrade():
    op.drop_index("ix_public_submissions_received_at", table_name="public_submissions")
    op.drop_index("ix_public_submissions_status", table_name="public_submissions")
    op.drop_index("ix_public_submissions_contact_type", table_name="public_submissions")
    op.drop_index("ix_public_submissions_submission_type", table_name="public_submissions")
    op.drop_table("public_submissions")
