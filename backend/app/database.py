from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for every SQLAlchemy model in the app.

    All Alembic migrations (backend/migrations/) are the sole schema
    source of truth (see supabase/README.md) -- this Base's metadata is
    used for local/test table creation and for Alembic autogenerate, never
    to create tables directly against a real environment.
    """


_engine = create_async_engine(get_settings().database_url)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped AsyncSession.

    Commits on clean handler completion, rolls back on any exception --
    centralized here so an individual route can never forget to commit
    (and the rollback test from Sprint 2's testing tasks exercises this
    path directly, not each handler's own error handling).
    """
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
