"""Add SMS add-on fields to councils table

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h8i9j0k1l2m3'
down_revision = 'g7h8i9j0k1l2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('councils', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'addon_sms',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('false'),
            )
        )
        batch_op.add_column(sa.Column('sms_tier', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('sms_event_prefs', sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column(
                'sms_business_hours_only',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('true'),
            )
        )
        batch_op.add_column(
            sa.Column(
                'sms_timezone',
                sa.String(length=60),
                nullable=False,
                server_default='Australia/Sydney',
            )
        )


def downgrade():
    with op.batch_alter_table('councils', schema=None) as batch_op:
        batch_op.drop_column('sms_timezone')
        batch_op.drop_column('sms_business_hours_only')
        batch_op.drop_column('sms_event_prefs')
        batch_op.drop_column('sms_tier')
        batch_op.drop_column('addon_sms')
