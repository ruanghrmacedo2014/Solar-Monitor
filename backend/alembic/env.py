from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from app.core.config import settings

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.db.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_tenant import UserTenant
from app.models.customer import Customer
from app.models.tenant_integration import TenantIntegration
from app.models.solar_plant import SolarPlant
from app.models.generation_record import GenerationRecord
from app.models.generation_aggregate import GenerationAggregate
from app.models.notification import Notification
from app.models.solar_device import SolarDevice
from app.models.solar_resource_snapshot import SolarResourceSnapshot
from app.models.generation_sync_log import GenerationSyncLog
from app.models.tag import Tag
from app.models.customer_tag import CustomerTag
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory
from app.models.ticket_message import TicketMessage
from app.models.ticket_message_edit_history import TicketMessageEditHistory
from app.models.ticket_message_mention import TicketMessageMention
from app.models.ticket_attachment import TicketAttachment
from app.models.ticket_tag import TicketTag
from app.models.plant_performance_config import PlantPerformanceConfig
from app.models.tenant_performance_config import TenantPerformanceConfig
from app.models.report import Report
from app.models.password_token import PasswordToken

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
