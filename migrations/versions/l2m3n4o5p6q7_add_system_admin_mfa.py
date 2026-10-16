"""add system administrator MFA

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa

revision = "l2m3n4o5p6q7"
down_revision = "k1l2m3n4o5p6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("mfa_secret", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("mfa_enrolled_at", sa.DateTime(), nullable=True))
    op.alter_column("users", "mfa_enabled", server_default=None)


def downgrade():
    op.drop_column("users", "mfa_enrolled_at")
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "mfa_secret")
