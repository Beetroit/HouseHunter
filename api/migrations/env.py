# Import necessary libraries
import asyncio
from logging.config import fileConfig

from alembic import context
from config import config as config_obj  # Adjust if your config object is elsewhere
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import your Base model and application configuration
# Ensure these paths are correct for your project structure
from models.base import Base  # Adjust if your Base model is elsewhere

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from your application's config object
# This ensures Alembic uses the same database as your app
db_url = config_obj.SQLALCHEMY_DATABASE_URI
config.set_main_option("sqlalchemy.url", db_url)

# Add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata  # Use the metadata from your Base model

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    # Check if the dialect is SQLite
    is_sqlite = url and url.startswith("sqlite")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # Render SQL literals directly (useful for offline mode)
        dialect_opts={"paramstyle": "named"},
        # Enable batch mode for SQLite offline migrations
        render_as_batch=is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Configure and run migrations using the provided database connection.
    Dynamically enables batch mode if the dialect is SQLite.
    """
    # Check the dialect of the current connection
    # Using dialect.name is more reliable than parsing the URL string again
    is_sqlite = connection.dialect.name == "sqlite"

    # Configure the Alembic context
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Enable batch mode for SQLite to handle limitations (e.g., renaming columns)
        # This is crucial for SQLite support.
        render_as_batch=is_sqlite,
        compare_type=True,  # Compare column types during autogenerate
    )

    # Begin a transaction and run the migrations within it
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Set up an asynchronous engine and run migrations online.
    """
    # Create an asynchronous engine from the Alembic configuration
    connectable = async_engine_from_config(
        config.get_section(
            config.config_ini_section, {}
        ),  # Get DB config from alembic.ini
        prefix="sqlalchemy.",  # Prefix for SQLAlchemy settings in the ini file
        poolclass=pool.NullPool,  # Use NullPool for migrations to avoid connection hanging
    )

    # Connect to the database asynchronously
    async with connectable.connect() as connection:
        # Run the synchronous migration function within the async context
        await connection.run_sync(do_run_migrations)

    # Dispose of the engine connection pool
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Run the asynchronous migration function using asyncio
    asyncio.run(run_async_migrations())


# Determine whether to run migrations offline or online
if context.is_offline_mode():
    print("Running migrations offline...")
    run_migrations_offline()
else:
    print("Running migrations online...")
    run_migrations_online()

print("Migration script finished.")
