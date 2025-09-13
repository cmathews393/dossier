"""SQLAlchemy async engine, session factory, and base model for the project."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Async DB URL (asyncpg) used by the application
DATABASE_URL = "postgresql+asyncpg://dossuser:dosspass@localhost:5432/dossier"

# Async engine and session factory
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Declarative base for models
Base = declarative_base()

__all__ = ["DATABASE_URL", "AsyncSessionLocal", "Base", "engine"]
