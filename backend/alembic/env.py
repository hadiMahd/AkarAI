from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Phase 2 foundation models so Alembic can detect them for autogenerate
from app.auth.models import Base as AuthBase  # noqa: F401
from app.users.models import Base as UsersBase  # noqa: F401
from app.audit.models import Base as AuditBase  # noqa: F401
from app.common.events import Base as EventsBase  # noqa: F401
from app.notifications.models import Base as NotificationsBase  # noqa: F401

target_metadata = [
    AuthBase.metadata,
    UsersBase.metadata,
    AuditBase.metadata,
    EventsBase.metadata,
    NotificationsBase.metadata,
]


def run_migrations_offline() -> None:
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
