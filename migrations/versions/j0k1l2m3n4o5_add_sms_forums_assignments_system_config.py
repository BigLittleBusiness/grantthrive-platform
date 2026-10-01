"""Add tables and columns present in the models but missing from migrations.

Covers SMS (councils.addon_sms / sms_* columns, council_sms_usage),
system_config, forums (forums, forum_members, forum_posts),
application_assignments and application_documents.s3_key.

Each step is skipped when the table/column already exists, so this is safe
to run against databases where these objects were created outside Alembic.

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-10-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "j0k1l2m3n4o5"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None


def _has_table(name):
    return sa.inspect(op.get_bind()).has_table(name)


def _has_column(table, column):
    return column in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade():
    if not _has_table("system_config"):
        op.create_table(
            "system_config",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("key", sa.String(length=100), nullable=False),
            sa.Column("value", sa.Text(), nullable=True),
            sa.Column("is_sensitive", sa.Boolean(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("updated_by", sa.String(length=200), nullable=True),
        )
        op.create_index("ix_system_config_key", "system_config", ["key"], unique=True)

    if not _has_table("council_sms_usage"):
        op.create_table(
            "council_sms_usage",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("council_id", sa.Integer(), sa.ForeignKey("councils.id"), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("messages_sent", sa.Integer(), nullable=False),
            sa.UniqueConstraint("council_id", "date", name="uq_council_sms_date"),
        )
        op.create_index("ix_council_sms_usage_council_id", "council_sms_usage", ["council_id"])
        op.create_index("ix_council_sms_usage_date", "council_sms_usage", ["date"])

    if not _has_table("forums"):
        op.create_table(
            "forums",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("council_id", sa.Integer(), sa.ForeignKey("councils.id"), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_public", sa.Boolean(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_forums_council_id", "forums", ["council_id"])

    if not _has_table("forum_members"):
        op.create_table(
            "forum_members",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("forum_id", sa.Integer(), sa.ForeignKey("forums.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("joined_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("forum_id", "user_id", name="uq_forum_member"),
        )
        op.create_index("ix_forum_members_forum_id", "forum_members", ["forum_id"])
        op.create_index("ix_forum_members_user_id", "forum_members", ["user_id"])

    if not _has_table("forum_posts"):
        op.create_table(
            "forum_posts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("forum_id", sa.Integer(), sa.ForeignKey("forums.id"), nullable=False),
            sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("is_pinned", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_forum_posts_forum_id", "forum_posts", ["forum_id"])

    if not _has_table("application_assignments"):
        op.create_table(
            "application_assignments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id"), nullable=False),
            sa.Column("staff_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("assigned_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("application_id", "staff_id", name="uq_app_assignment"),
        )
        op.create_index("ix_application_assignments_application_id", "application_assignments", ["application_id"])
        op.create_index("ix_application_assignments_staff_id", "application_assignments", ["staff_id"])

    if not _has_column("application_documents", "s3_key"):
        op.add_column("application_documents", sa.Column("s3_key", sa.String(length=1024), nullable=True))

    council_columns = [
        sa.Column("addon_sms", sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column("sms_tier", sa.String(length=20), nullable=True),
        sa.Column("sms_event_prefs", sa.JSON(), nullable=True),
        sa.Column("sms_business_hours_only", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column("sms_timezone", sa.String(length=60), nullable=True, server_default="Australia/Sydney"),
    ]
    for column in council_columns:
        if not _has_column("councils", column.name):
            op.add_column("councils", column)


def downgrade():
    for column in ("sms_timezone", "sms_business_hours_only", "sms_event_prefs", "sms_tier", "addon_sms"):
        if _has_column("councils", column):
            op.drop_column("councils", column)
    if _has_column("application_documents", "s3_key"):
        op.drop_column("application_documents", "s3_key")
    for table in ("application_assignments", "forum_posts", "forum_members", "forums",
                  "council_sms_usage", "system_config"):
        if _has_table(table):
            op.drop_table(table)
