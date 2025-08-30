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

def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))

def downgrade() -> None:
    op.drop_column("users", "password_hash")
