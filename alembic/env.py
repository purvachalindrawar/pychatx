from __future__ import annotations
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make sure repo root is on sys.path (so imports work when running alembic from root)
# (alembic.ini has prepend_sys_path = . but we do this to be safe)
sys.path.append(".")

from backend.app.db import Base  # noqa
from backend.app.settings import settings  # noqa

# Import models so metadata is aware of them
from backend.app.models import User  # noqa

config = context.config
fileConfig(config.config_file_name)  # logging

# Use DATABASE_URL from our settings (.env)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
