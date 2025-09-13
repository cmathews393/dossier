"""Database helper utilities and dependency providers."""

from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, sessionmaker

from dossier.models import AsyncSessionLocal, Base

# Synchronous engine for sync DB access (used by auth)
SQLALCHEMY_DATABASE_URL = (
    "postgresql+psycopg2://dossuser:dosspass@localhost:5432/dossier"
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get the async database session."""
    async with AsyncSessionLocal() as session:
        yield session


def get_db_sync() -> Generator[Session, None, None]:
    """Dependency to get the sync database session (for sync routes)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Expose Base so Alembic env can import metadata from `dossier.db` if desired
__all__ = ["Base", "SessionLocal", "engine", "get_db", "get_db_sync"]
