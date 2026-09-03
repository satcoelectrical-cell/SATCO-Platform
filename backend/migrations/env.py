import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.engine import URL
from sqlalchemy.engine import make_url

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def get_database_url() -> str:
    explicit_url = os.getenv("ALEMBIC_DATABASE_URL")
    if not explicit_url:
        raise RuntimeError("Alembic requires explicit ALEMBIC_DATABASE_URL")
    migration_role = make_url(explicit_url).username
    runtime_role = os.getenv("RUNTIME_DATABASE_ROLE") or os.getenv("DATABASE_USER")
    if not runtime_role:
        raise RuntimeError("Alembic requires RUNTIME_DATABASE_ROLE to identify the runtime role")
    if migration_role == runtime_role:
        raise RuntimeError("Alembic migration role must differ from the runtime role")
    return explicit_url


config.set_main_option(
    "sqlalchemy.url",
    get_database_url().replace("%", "%%"),
)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.core.database import Base
from app.models import audit_log  # noqa: F401
from app.models import contact  # noqa: F401
from app.models import customer  # noqa: F401
from app.models import engineering_context  # noqa: F401
from app.models import engineering_context_relationship  # noqa: F401
from app.models import project  # noqa: F401
from app.models import user  # noqa: F401
from app.models import evidence  # noqa: F401
from app.models import evidence_command  # noqa: F401
from app.models import engineering_relationship  # noqa: F401
from app.models import engineering_relationship_command  # noqa: F401
from app.models import engineering_experience_capture  # noqa: F401
from app.models import engineering_experience_capture_command  # noqa: F401
from app.models import technical_report  # noqa: F401
from app.models import technical_report_command  # noqa: F401
from app.models import supporting_file  # noqa: F401
from app.models import discipline_package  # noqa: F401

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


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
