"""create messages table

Revision ID: 202508300004
Revises: 202508300003
Create Date: 2025-08-30 00:04:00
"""
from alembic import op
import sqlalchemy as sa

revision = "202508300004"
down_revision = "202508300003"
branch_labels = None
depends_on = None


def _ts_default():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return sa.text("CURRENT_TIMESTAMP")
    return sa.text("NOW()")


def upgrade():
    ts_default = _ts_default()

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=ts_default),
    )

    op.create_index("ix_messages_room_id_created_at", "messages", ["room_id", "created_at"], unique=False)


def downgrade():
    op.drop_index("ix_messages_room_id_created_at", table_name="messages")
    op.drop_table("messages")
