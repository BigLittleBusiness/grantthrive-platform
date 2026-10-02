"""Add Stripe subscription billing fields.

Councils: chosen plan/cycle, Stripe customer & subscription, status, period end.
Users: plan/cycle chosen at council registration.

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-10-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "k1l2m3n4o5p6"
down_revision = "j0k1l2m3n4o5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("councils", sa.Column("billing_plan", sa.String(length=20), nullable=True))
    op.add_column("councils", sa.Column("billing_cycle", sa.String(length=10), nullable=True))
    op.add_column("councils", sa.Column("stripe_customer_id", sa.String(length=64), nullable=True))
    op.add_column("councils", sa.Column("stripe_subscription_id", sa.String(length=64), nullable=True))
    op.add_column("councils", sa.Column("subscription_status", sa.String(length=32), nullable=True))
    op.add_column("councils", sa.Column("current_period_end", sa.DateTime(), nullable=True))
    op.add_column("councils", sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_councils_stripe_customer_id", "councils", ["stripe_customer_id"], unique=True)
    op.create_index("ix_councils_stripe_subscription_id", "councils", ["stripe_subscription_id"], unique=True)

    op.add_column("users", sa.Column("requested_plan", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("requested_billing_cycle", sa.String(length=10), nullable=True))


def downgrade():
    op.drop_column("users", "requested_billing_cycle")
    op.drop_column("users", "requested_plan")

    op.drop_index("ix_councils_stripe_subscription_id", table_name="councils")
    op.drop_index("ix_councils_stripe_customer_id", table_name="councils")
    for column in ("cancel_at_period_end", "current_period_end", "subscription_status",
                   "stripe_subscription_id", "stripe_customer_id", "billing_cycle", "billing_plan"):
        op.drop_column("councils", column)
