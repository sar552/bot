"""initial schema

Revision ID: 0001_init
Revises:
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

code_status = postgresql.ENUM(
    "unused", "used", "blocked", name="code_status", create_type=False
)
bonus_status = postgresql.ENUM(
    "unused", "assigned", "used", "expired", "blocked",
    name="bonus_status", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    code_status.create(bind, checkfirst=True)
    bonus_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column("username", sa.String(128)),
        sa.Column("full_name", sa.String(256), nullable=False),
        sa.Column("phone", sa.String(32)),
        sa.Column("language", sa.String(8), server_default="uz"),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "codes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("status", code_status, nullable=False, server_default="unused"),
        sa.Column("used_by_telegram_id", sa.BigInteger),
        sa.Column("used_by_name", sa.String(256)),
        sa.Column("used_by_phone", sa.String(32)),
        sa.Column("used_by_username", sa.String(128)),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("note", sa.String(256)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_codes_code", "codes", ["code"])
    op.create_index("idx_codes_status", "codes", ["status"])

    op.create_table(
        "bonuses",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("bonus_code", sa.String(64), nullable=False, unique=True),
        sa.Column("discount_percent", sa.Integer, nullable=False, server_default="10"),
        sa.Column("status", bonus_status, nullable=False, server_default="unused"),
        sa.Column("assigned_to_telegram_id", sa.BigInteger),
        sa.Column("assigned_to_name", sa.String(256)),
        sa.Column("assigned_to_phone", sa.String(32)),
        sa.Column("assigned_to_username", sa.String(128)),
        sa.Column("source_code_id", sa.BigInteger, sa.ForeignKey("codes.id")),
        sa.Column("assigned_at", sa.DateTime(timezone=True)),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("note", sa.String(256)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_bonuses_status", "bonuses", ["status"])

    op.create_table(
        "rate_limits",
        sa.Column("telegram_id", sa.BigInteger, primary_key=True),
        sa.Column("failed_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("blocked_until", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "channel_clicks",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("clicked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_channel_clicks_tg", "channel_clicks", ["telegram_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("actor_id", sa.BigInteger),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity", sa.String(32)),
        sa.Column("entity_id", sa.BigInteger),
        sa.Column("details", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_index("idx_channel_clicks_tg", table_name="channel_clicks")
    op.drop_table("channel_clicks")
    op.drop_table("rate_limits")
    op.drop_index("idx_bonuses_status", table_name="bonuses")
    op.drop_table("bonuses")
    op.drop_index("idx_codes_status", table_name="codes")
    op.drop_index("idx_codes_code", table_name="codes")
    op.drop_table("codes")
    op.drop_index("idx_users_telegram_id", table_name="users")
    op.drop_table("users")
    bind = op.get_bind()
    bonus_status.drop(bind, checkfirst=True)
    code_status.drop(bind, checkfirst=True)
