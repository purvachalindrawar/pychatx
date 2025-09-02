"""create rooms and room_members

Revision ID: 202508300003
Revises: 202508300002
Create Date: 2025-08-30 00:03:00
"""
from alembic import op
import sqlalchemy as sa

revision = "202508300003"
down_revision = "202508300002"
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
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=ts_default),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=ts_default),
    )

    op.create_table(
        "room_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=ts_default),
        sa.UniqueConstraint("room_id", "user_id", name="uq_room_user"),  # important: defined at create time
    )


def downgrade():
    op.drop_table("room_members")
    op.drop_table("rooms")
