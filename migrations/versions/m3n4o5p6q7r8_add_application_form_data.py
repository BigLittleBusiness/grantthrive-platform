"""add encrypted application form data

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa


revision = "m3n4o5p6q7r8"
down_revision = "l2m3n4o5p6q7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("applications", sa.Column("form_data", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("applications", "form_data")
