"""Alembic environment configuration.

Reads SYNC_DATABASE_URL from environment (or .env) so that the DB URL is never
hard-coded here. Models' Base.metadata is imported for --autogenerate support
once models are defined.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Load .env so DATABASE_URL is available when running locally ─────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Alembic Config object (gives access to .ini values) ────────────────────
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Override sqlalchemy.url from env ────────────────────────────────────────
# We use SYNC_DATABASE_URL (psycopg2) because Alembic requires a sync driver.
sync_url = os.environ.get("SYNC_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
# If using async driver URL in DATABASE_URL, convert it for Alembic
sync_url = sync_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
config.set_main_option("sqlalchemy.url", sync_url)

# ── Target metadata ─────────────────────────────────────────────────────────
# Import Base from the app so --autogenerate can detect model changes.
# Models are not defined yet; this will be updated when models are added.
try:
    from app.database import Base  # noqa: F401
    target_metadata = Base.metadata
except ImportError:
    target_metadata = None


# ── Offline mode ─────────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (emits SQL to stdout)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode ──────────────────────────────────────────────────────────────
def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
