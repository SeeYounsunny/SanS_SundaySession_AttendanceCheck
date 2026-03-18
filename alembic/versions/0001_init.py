"""init

Revision ID: 0001_init
Revises: None
Create Date: 2026-03-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "group_chats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
    )

    op.create_table(
        "checkins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("week_date", sa.Date(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("user_username", sa.String(length=64), nullable=True),
        sa.Column("user_first_name", sa.String(length=128), nullable=True),
        sa.Column("user_last_name", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["group_chats.chat_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id", "week_date", "user_id", name="uq_checkins_chat_week_user"),
    )
    op.create_index("ix_checkins_chat_week", "checkins", ["chat_id", "week_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_checkins_chat_week", table_name="checkins")
    op.drop_table("checkins")
    op.drop_table("group_chats")

