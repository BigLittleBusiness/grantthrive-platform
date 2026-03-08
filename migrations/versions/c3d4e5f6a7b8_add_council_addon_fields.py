"""Add addon_community_voting and addon_grant_mapping to councils table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-08 00:00:00.000000

These two boolean columns track whether a Small Council has purchased the
Community Voting (+$50/mo) or Grant Mapping (+$50/mo) add-ons.

Medium and Large councils have these features included in their plan and
will always have these columns set to False (the feature availability is
determined by the plan, not the add-on flag).
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('councils', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'addon_community_voting',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('false'),
            )
        )
        batch_op.add_column(
            sa.Column(
                'addon_grant_mapping',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('false'),
            )
        )


def downgrade():
    with op.batch_alter_table('councils', schema=None) as batch_op:
        batch_op.drop_column('addon_grant_mapping')
        batch_op.drop_column('addon_community_voting')
