"""add notifications table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-09 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    # Add password reset token columns to users table
    op.add_column('users', sa.Column('reset_token',        sa.String(100), nullable=True))
    op.add_column('users', sa.Column('reset_token_expiry', sa.DateTime(),  nullable=True))
    op.add_column('users', sa.Column('email_opt_in',       sa.Boolean(),   nullable=False, server_default='1'))
    op.create_index('ix_users_reset_token', 'users', ['reset_token'])

    op.create_table(
        'notifications',
        sa.Column('id',         sa.Integer(),     nullable=False),
        sa.Column('user_id',    sa.Integer(),     nullable=False),
        sa.Column('type',       sa.String(50),    nullable=False),
        sa.Column('title',      sa.String(200),   nullable=False),
        sa.Column('message',    sa.Text(),        nullable=False),
        sa.Column('link',       sa.String(500),   nullable=True),
        sa.Column('is_read',    sa.Boolean(),     nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(),    nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_user_id',    'notifications', ['user_id'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])


def downgrade():
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_user_id',    table_name='notifications')
    op.drop_table('notifications')
    op.drop_index('ix_users_reset_token', table_name='users')
    op.drop_column('users', 'reset_token_expiry')
    op.drop_column('users', 'reset_token')
    op.drop_column('users', 'email_opt_in')
