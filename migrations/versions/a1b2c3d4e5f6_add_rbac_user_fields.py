"""add rbac user fields: is_approved, organisation, abn

Revision ID: a1b2c3d4e5f6
Revises: f8908766984b
Create Date: 2026-03-08 00:00:00.000000

Adds three new columns to the ``users`` table to support the stepwise
registration flow and RBAC approval workflow:

  is_approved  (Boolean, default False)
      Tracks whether a self-registered community_member or
      professional_consultant account has been approved by a council_admin.
      council_staff, council_admin, and system_admin accounts are created
      with is_approved = True (they are provisioned, not self-registered).

  organisation (String(200), nullable)
      The organisation name provided during registration.
      Optional for community_member; recommended for professional_consultant.

  abn          (String(20), nullable)
      Australian Business Number. Collected during registration for
      professional_consultant accounts only.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f8908766984b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false')
        )
        batch_op.add_column(
            sa.Column('organisation', sa.String(length=200), nullable=True)
        )
        batch_op.add_column(
            sa.Column('abn', sa.String(length=20), nullable=True)
        )

    # Backfill: existing users who are already active are considered approved
    op.execute(
        "UPDATE users SET is_approved = true WHERE is_active = true"
    )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('abn')
        batch_op.drop_column('organisation')
        batch_op.drop_column('is_approved')
