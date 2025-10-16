from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import models  # noqa: F401,E402
from app.config import get_settings  # noqa: E402
from app.db import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
database_url = settings.default_database_url
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine_kwargs = {"prefix": "sqlalchemy."}
    if settings.using_supabase_default:
        overflow = max(
            settings.supabase_pool_max_connections - settings.supabase_pool_min_connections,
            0,
        )
        engine_kwargs.update(
            {
                "poolclass": pool.QueuePool,
                "pool_size": settings.supabase_pool_min_connections,
                "max_overflow": overflow,
                "pool_timeout": settings.supabase_pool_timeout_seconds,
                "connect_args": {"sslmode": "require"},
            }
        )
    else:
        engine_kwargs["poolclass"] = pool.NullPool

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        **engine_kwargs,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
