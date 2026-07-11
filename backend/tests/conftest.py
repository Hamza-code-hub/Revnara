import uuid
from collections.abc import AsyncGenerator

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import Base, get_db_session
from app.main import create_app

TEST_JWT_SECRET = "test-secret-do-not-use-in-any-real-environment"  # noqa: S105


@pytest.fixture(autouse=True)
def _configure_test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test runs with a known JWT secret so make_token() below and
    app/auth/jwt.py agree on how to sign/verify -- get_settings() is
    cached (lru_cache), so this must clear that cache per test.
    """
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("SUPABASE_JWT_AUDIENCE", "authenticated")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """A fresh in-memory SQLite database per test.

    This is a local verification stand-in, not the target database --
    Postgres/Supabase remains the real target (see
    supabase/README.md and backend/tests/README.md). StaticPool keeps a
    single connection alive so every use of the engine sees the same
    in-memory database rather than each connection getting a blank one.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """An httpx AsyncClient wired directly to the FastAPI app (ASGI
    transport, no real network/port) with the DB dependency overridden to
    the per-test SQLite session from [db_session].
    """
    app = create_app()

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession]:
        # Mirrors app.database.get_db_session's real commit/rollback
        # semantics exactly -- an override that always commits regardless
        # of exceptions would silently defeat any rollback/atomicity test.
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db_session] = _override_get_db_session

    # raise_app_exceptions=False: a real deployment's ServerErrorMiddleware
    # converts an unhandled exception into a 500 response rather than
    # crashing the process -- the default ASGITransport instead re-raises
    # into the caller, which would make any "the API returns 500" test
    # (e.g. the rollback/atomicity test) fail for the wrong reason.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def make_token(*, user_id: uuid.UUID | None = None, email: str | None = "user@example.com") -> str:
    """Signs a test JWT with the same shared secret app/auth/jwt.py is
    configured to verify against in tests (see
    _configure_test_settings above).
    """
    subject = str(user_id or uuid.uuid4())
    payload = {"sub": subject, "email": email, "aud": "authenticated"}
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


def auth_headers(
    *, user_id: uuid.UUID | None = None, email: str | None = "user@example.com"
) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user_id=user_id, email=email)}"}
