"""Add position, department, requested_subdomain to users table

These fields support the council registration flow:
  - position: the registrant's job title (e.g. "Grants Officer")
  - department: the registrant's department (e.g. "Community Services")
  - requested_subdomain: the council subdomain chosen at registration;
    used by system_admin when approving the council_admin account to
    create the Council record with the correct subdomain.

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('position', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('department', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('requested_subdomain', sa.String(length=100), nullable=True))
        batch_op.create_index(
            'ix_users_requested_subdomain',
            ['requested_subdomain'],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_requested_subdomain')
        batch_op.drop_column('requested_subdomain')
        batch_op.drop_column('department')
        batch_op.drop_column('position')
