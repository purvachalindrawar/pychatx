"""add password_hash column to users

Revision ID: 202508300002
Revises: 202508300001
Create Date: 2025-08-30 00:02:00
"""
from alembic import op
import sqlalchemy as sa

revision = "202508300002"
down_revision = "202508300001"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite can add columns, but NOT NULL needs a default at add-time
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("password_hash", sa.String(255), nullable=False, server_default="")
        )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("password_hash")
