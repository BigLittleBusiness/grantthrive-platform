"""add pricing_config table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-08

"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'pricing_config',
        sa.Column('id',                            sa.Integer(),     nullable=False),
        sa.Column('plan_key',                      sa.String(20),    nullable=False),
        sa.Column('display_name',                  sa.String(100),   nullable=False),
        sa.Column('monthly_price_aud_cents',       sa.Integer(),     nullable=False, server_default='0'),
        sa.Column('annual_price_aud_cents',        sa.Integer(),     nullable=False, server_default='0'),
        sa.Column('annual_monthly_price_aud_cents',sa.Integer(),     nullable=False, server_default='0'),
        sa.Column('addon_community_voting_cents',  sa.Integer(),     nullable=False, server_default='5000'),
        sa.Column('addon_grant_mapping_cents',     sa.Integer(),     nullable=False, server_default='5000'),
        sa.Column('updated_at',                    sa.DateTime(),    nullable=True),
        sa.Column('updated_by',                    sa.String(200),   nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pricing_config_plan_key', 'pricing_config', ['plan_key'], unique=True)

    # Seed default pricing from compiled plan defaults
    op.execute("""
        INSERT INTO pricing_config
            (plan_key, display_name, monthly_price_aud_cents, annual_price_aud_cents,
             annual_monthly_price_aud_cents, addon_community_voting_cents, addon_grant_mapping_cents)
        VALUES
            ('small',  'Small Council',  20000,  200000,  16700, 5000, 5000),
            ('medium', 'Medium Council', 50000,  500000,  41700, 5000, 5000),
            ('large',  'Large Council',  110000, 1100000, 91700, 5000, 5000)
        ON CONFLICT (plan_key) DO NOTHING
    """)


def downgrade():
    op.drop_index('ix_pricing_config_plan_key', table_name='pricing_config')
    op.drop_table('pricing_config')
