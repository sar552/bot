"""books table

Revision ID: 0002_books
Revises: 0001_init
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_books"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("filename", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("books")
