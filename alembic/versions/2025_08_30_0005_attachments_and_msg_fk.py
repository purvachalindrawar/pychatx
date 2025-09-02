"""attachments table and messages.attachment_id

Revision ID: 202508300005
Revises: 202508300004
Create Date: 2025-08-30 00:05:00
"""
from alembic import op
import sqlalchemy as sa

revision = "202508300005"
down_revision = "202508300004"
branch_labels = None
depends_on = None


def _ts_default():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return sa.text("CURRENT_TIMESTAMP")
    return sa.text("NOW()")


def upgrade():
    ts_default = _ts_default()

    # 1) Create attachments table
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False, server_default="application/octet-stream"),
        sa.Column("size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("uploader_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=ts_default),
    )

    # 2) Add attachment_id to messages using batch mode (SQLite-safe)
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.add_column(sa.Column("attachment_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_messages_attachment",
            "attachments",
            ["attachment_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_messages_attachment_id", ["attachment_id"], unique=False)


def downgrade():
    # reverse: drop index, FK, column (batch for SQLite)
    with op.batch_alter_table("messages", schema=None) as batch_op:
        batch_op.drop_index("ix_messages_attachment_id")
        batch_op.drop_constraint("fk_messages_attachment", type_="foreignkey")
        batch_op.drop_column("attachment_id")

    op.drop_table("attachments")
