"""
Async database engine and session factory.

Swapping DATABASE_URL from sqlite+aiosqlite to postgresql+asyncpg in .env
is the ONLY change needed to move from the free pilot setup to a full
Postgres deployment. No other file in the project needs to change.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncSession:
    """Yield a new database session (used by middleware)."""
    async with AsyncSessionLocal() as session:
        yield session
