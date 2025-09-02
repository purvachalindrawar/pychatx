"""room invites

Revision ID: 202508300007
Revises: 202508300006
Create Date: 2025-08-30 00:07:00
"""
from alembic import op
import sqlalchemy as sa

revision = "202508300007"
down_revision = "202508300006"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "room_invites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("uses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_room_invites_code", "room_invites", ["code"])
    op.create_index("ix_room_invites_room_id", "room_invites", ["room_id"])

def downgrade() -> None:
    op.drop_index("ix_room_invites_room_id", table_name="room_invites")
    op.drop_index("ix_room_invites_code", table_name="room_invites")
    op.drop_table("room_invites")
