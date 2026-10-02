"""Alembic environment for upay Shield.

The migration URL always prefers ``DATABASE_URL`` (read through
``app.core.config.get_settings()``) and only falls back to the placeholder in
``alembic.ini``. This keeps a single source of truth for the connection string
and lets ``alembic upgrade head`` run against exactly the database the service
uses — there is never a second, drift-prone URL.

``target_metadata`` is ``app.models.Base.metadata``. ``app.models`` imports
every model module, so autogenerate sees the complete schema.
"""

from __future__ import annotations

import logging
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make `app` importable when alembic is invoked from the backend directory.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.models import Base  # noqa: E402

# Alembic Config object providing access to values in alembic.ini.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# The single source of truth for autogenerate.
target_metadata = Base.metadata

logger = logging.getLogger("alembic.env")


def get_database_url() -> str:
    """Resolve the migration URL.

    Prefers ``DATABASE_URL`` from the environment (via settings); falls back to
    the ``alembic.ini`` placeholder for offline SQL rendering. Raises if
    neither is usable, rather than guessing a default database.
    """
    settings = get_settings()
    url = settings.database_url or config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError(
            "No database URL configured. Set DATABASE_URL (see .env.example) "
            "or provide sqlalchemy.url in alembic.ini."
        )
    # Escape percent signs for configparser interpolation semantics.
    return url.replace("%", "%%")


def run_migrations_offline() -> None:
    """Render SQL to stdout (``alembic upgrade head --sql``) without a DB.

    This is the supported way to review the full DDL offline: no connection
    is opened and the PostgreSQL dialect renders every statement.
    """
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against a live PostgreSQL database."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
