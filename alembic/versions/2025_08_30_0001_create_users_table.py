"""create users table

Revision ID: 202508300001
Revises:
Create Date: 2025-08-30 00:01:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "202508300001"
down_revision = None
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
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=ts_default),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=ts_default),
    )


def downgrade():
    op.drop_table("users")
