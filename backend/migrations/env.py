import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import get_settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Real database URL comes from app settings (env vars), never hardcoded in
# alembic.ini, so local/staging/prod all use the same migration scripts
# against their own DATABASE_URL (§2.8 Configuration Over Hardcoding).
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# Import every model module so its tables register on Base.metadata before
# autogenerate/`alembic check` diff against it -- a model that isn't
# imported here is invisible to Alembic regardless of whether the file
# exists.
from app.agents import models as _agents_models  # noqa: E402, F401
from app.audit import models as _audit_models  # noqa: E402, F401
from app.company import models as _company_models  # noqa: E402, F401
from app.database import Base  # noqa: E402
from app.explainability import models as _explainability_models  # noqa: E402, F401
from app.files import models as _files_models  # noqa: E402, F401
from app.opportunities import models as _opportunities_models  # noqa: E402, F401
from app.organizations import models as _organizations_models  # noqa: E402, F401
from app.rag import models as _rag_models  # noqa: E402, F401

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
