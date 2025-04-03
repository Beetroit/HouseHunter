from contextlib import asynccontextmanager
from typing import AsyncGenerator

from config import config  # Import config from the root config.py
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Create the SQLAlchemy async engine
try:
    engine = create_async_engine(
        config.SQLALCHEMY_DATABASE_URI,
        echo=config.SQLALCHEMY_ECHO,
        pool_pre_ping=True,  # Helps prevent connection errors after long idle times
    )
except Exception as e:
    print(f"Error creating database engine: {e}")
    # Handle error appropriately, maybe exit or log critical error
    raise

# Create a configured "Session" class
# autocommit=False and autoflush=False are standard for web applications
# expire_on_commit=False prevents attributes from being expired after commit
AsyncSessionFactory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional scope around a series of operations.
    Handles session creation, commit, rollback, and closing.
    """
    session: AsyncSession = AsyncSessionFactory()
    try:
        yield session
        # Optional: If you want automatic commit on successful exit
        # await session.commit()
    except SQLAlchemyError as e:
        print(f"Database error occurred: {e}")
        await session.rollback()
        raise  # Re-raise the exception after rollback
    except Exception as e:
        print(f"An unexpected error occurred in get_session: {e}")
        await session.rollback()
        raise  # Re-raise the exception after rollback
    finally:
        await session.close()


async def init_db():
    """
    (Optional) Initialize the database - typically handled by Alembic migrations.
    This function might be useful for creating tables during testing or initial setup
    if not using migrations immediately.
    """
    # Import Base from models.base AFTER models are defined to avoid circular imports
    # from models.base import Base
    # async with engine.begin() as conn:
    #     # await conn.run_sync(Base.metadata.drop_all) # Use with caution!
    #     await conn.run_sync(Base.metadata.create_all)
    print("Database initialization skipped (handled by Alembic).")


# Example of how to run init_db if needed (e.g., in a startup script)
# if __name__ == "__main__":
#     asyncio.run(init_db())
