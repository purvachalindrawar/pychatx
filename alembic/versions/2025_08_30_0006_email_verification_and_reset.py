"""email verified + email/reset tokens

Revision ID: 202508300006
Revises: 202508300005
Create Date: 2025-08-30 00:06:00
"""
from alembic import op
import sqlalchemy as sa

revision = "202508300006"
down_revision = "202508300005"
branch_labels = None
depends_on = None


def _ts_default():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return sa.text("CURRENT_TIMESTAMP")
    return sa.text("NOW()")


def _bool_default_false():
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return sa.text("0")
    return sa.text("false")


def upgrade():
    ts_default = _ts_default()

    # Add users.email_verified with a default; don't attempt DROP DEFAULT on SQLite
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "email_verified",
                sa.Boolean(),
                nullable=False,
                server_default=_bool_default_false(),
            )
        )

    # Create email verification tokens
    op.create_table(
        "email_verify_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=ts_default),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_email_verify_tokens_user_id", "email_verify_tokens", ["user_id"], unique=False)

    # Create password reset tokens
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=ts_default),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"], unique=False)


def downgrade():
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_index("ix_email_verify_tokens_user_id", table_name="email_verify_tokens")
    op.drop_table("email_verify_tokens")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("email_verified")
