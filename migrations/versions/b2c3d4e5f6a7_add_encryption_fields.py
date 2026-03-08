"""Add email_hmac index and widen PII columns for AES-256-GCM ciphertext

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-08

Changes
-------
1. users table:
   - Add email_hmac VARCHAR(64) NOT NULL (unique index) — HMAC-SHA256 search index
   - Widen email         VARCHAR(120) → VARCHAR(500)  — stores AES-256-GCM ciphertext
   - Widen phone         VARCHAR(20)  → VARCHAR(200)
   - Widen organisation  VARCHAR(200) → VARCHAR(300)
   - Widen abn           VARCHAR(20)  → VARCHAR(100)

2. councils table:
   - Widen contact_email VARCHAR(120) → VARCHAR(500)
   - Widen contact_phone VARCHAR(20)  → VARCHAR(200)
   - Widen address       VARCHAR(500) → VARCHAR(700)

3. applications table:
   - Widen contact_email VARCHAR(120) → VARCHAR(500)
   - Widen contact_phone VARCHAR(20)  → VARCHAR(200)
   - Widen address       VARCHAR(500) → VARCHAR(700)

4. community_votes table:
   - Widen voter_email VARCHAR(120) → VARCHAR(500)
   - Widen voter_name  VARCHAR(100) → VARCHAR(300)

Note on email_hmac backfill
---------------------------
Because existing rows have email stored as plaintext (pre-encryption),
this migration backfills email_hmac using SHA-256(lower(email)) as a
temporary measure.  Once FIELD_HMAC_KEY is set in the environment and
the application restarts, the first login for each user will transparently
rehash their email_hmac to the proper keyed HMAC value.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # ── users ─────────────────────────────────────────────────────────────────
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Add email_hmac — allow NULL initially so existing rows don't fail
        batch_op.add_column(
            sa.Column('email_hmac', sa.String(64), nullable=True)
        )
        # Widen columns to accommodate ciphertext
        batch_op.alter_column('email',
            existing_type=sa.String(120),
            type_=sa.String(500),
            existing_nullable=False)
        batch_op.alter_column('phone',
            existing_type=sa.String(20),
            type_=sa.String(200),
            existing_nullable=True)
        batch_op.alter_column('organisation',
            existing_type=sa.String(200),
            type_=sa.String(300),
            existing_nullable=True)
        batch_op.alter_column('abn',
            existing_type=sa.String(20),
            type_=sa.String(100),
            existing_nullable=True)

    # Backfill email_hmac with SHA-256(lower(email)) for existing plaintext rows
    op.execute("""
        UPDATE users
        SET email_hmac = encode(sha256(lower(email)::bytea), 'hex')
        WHERE email_hmac IS NULL
    """)

    # Now enforce NOT NULL and unique index
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('email_hmac', nullable=False)
        batch_op.create_unique_constraint('uq_users_email_hmac', ['email_hmac'])
        batch_op.create_index('ix_users_email_hmac', ['email_hmac'], unique=True)

    # ── councils ──────────────────────────────────────────────────────────────
    with op.batch_alter_table('councils', schema=None) as batch_op:
        batch_op.alter_column('contact_email',
            existing_type=sa.String(120),
            type_=sa.String(500),
            existing_nullable=True)
        batch_op.alter_column('contact_phone',
            existing_type=sa.String(20),
            type_=sa.String(200),
            existing_nullable=True)
        batch_op.alter_column('address',
            existing_type=sa.String(500),
            type_=sa.String(700),
            existing_nullable=True)

    # ── applications ──────────────────────────────────────────────────────────
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.alter_column('contact_email',
            existing_type=sa.String(120),
            type_=sa.String(500),
            existing_nullable=False)
        batch_op.alter_column('contact_phone',
            existing_type=sa.String(20),
            type_=sa.String(200),
            existing_nullable=True)
        batch_op.alter_column('address',
            existing_type=sa.String(500),
            type_=sa.String(700),
            existing_nullable=True)

    # ── community_votes ───────────────────────────────────────────────────────
    with op.batch_alter_table('community_votes', schema=None) as batch_op:
        batch_op.alter_column('voter_email',
            existing_type=sa.String(120),
            type_=sa.String(500),
            existing_nullable=True)
        batch_op.alter_column('voter_name',
            existing_type=sa.String(100),
            type_=sa.String(300),
            existing_nullable=True)


def downgrade():
    # ── community_votes ───────────────────────────────────────────────────────
    with op.batch_alter_table('community_votes', schema=None) as batch_op:
        batch_op.alter_column('voter_email',
            existing_type=sa.String(500),
            type_=sa.String(120),
            existing_nullable=True)
        batch_op.alter_column('voter_name',
            existing_type=sa.String(300),
            type_=sa.String(100),
            existing_nullable=True)

    # ── applications ──────────────────────────────────────────────────────────
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.alter_column('contact_email',
            existing_type=sa.String(500),
            type_=sa.String(120),
            existing_nullable=False)
        batch_op.alter_column('contact_phone',
            existing_type=sa.String(200),
            type_=sa.String(20),
            existing_nullable=True)
        batch_op.alter_column('address',
            existing_type=sa.String(700),
            type_=sa.String(500),
            existing_nullable=True)

    # ── councils ──────────────────────────────────────────────────────────────
    with op.batch_alter_table('councils', schema=None) as batch_op:
        batch_op.alter_column('contact_email',
            existing_type=sa.String(500),
            type_=sa.String(120),
            existing_nullable=True)
        batch_op.alter_column('contact_phone',
            existing_type=sa.String(200),
            type_=sa.String(20),
            existing_nullable=True)
        batch_op.alter_column('address',
            existing_type=sa.String(700),
            type_=sa.String(500),
            existing_nullable=True)

    # ── users ─────────────────────────────────────────────────────────────────
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_email_hmac')
        batch_op.drop_constraint('uq_users_email_hmac', type_='unique')
        batch_op.drop_column('email_hmac')
        batch_op.alter_column('email',
            existing_type=sa.String(500),
            type_=sa.String(120),
            existing_nullable=False)
        batch_op.alter_column('phone',
            existing_type=sa.String(200),
            type_=sa.String(20),
            existing_nullable=True)
        batch_op.alter_column('organisation',
            existing_type=sa.String(300),
            type_=sa.String(200),
            existing_nullable=True)
        batch_op.alter_column('abn',
            existing_type=sa.String(100),
            type_=sa.String(20),
            existing_nullable=True)
