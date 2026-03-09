"""Add assessment team fields to grants table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-09

Adds two columns to the grants table:
  - assigned_reviewer_ids  TEXT NOT NULL DEFAULT '[]'
      JSON-encoded list of user IDs nominated as reviewers for this grant.
      An empty list means any council_staff member may self-assign.
  - required_approvals     INTEGER NOT NULL DEFAULT 1
      Number of independent staff approvals required before an application
      is automatically transitioned to 'approved' status.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('grants', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'assigned_reviewer_ids',
                sa.Text(),
                nullable=False,
                server_default='[]',
            )
        )
        batch_op.add_column(
            sa.Column(
                'required_approvals',
                sa.Integer(),
                nullable=False,
                server_default='1',
            )
        )


def downgrade():
    with op.batch_alter_table('grants', schema=None) as batch_op:
        batch_op.drop_column('required_approvals')
        batch_op.drop_column('assigned_reviewer_ids')
