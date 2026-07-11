import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _is_postgres(db: AsyncSession) -> bool:
    return db.get_bind().dialect.name == "postgresql"


async def set_pg_actor_context(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID | None = None,
) -> None:
    """Sets Postgres session-local variables RLS policies read via
    `current_actor_user_id()` / `current_tenant_id()` (supabase/rls/00_functions.sql),
    scoping every subsequent query in the current transaction at the
    database level -- not just via each query's own WHERE clause
    (`scoped_to_tenant`, tenancy/repository.py). This is what makes RLS a
    real enforcement layer for the backend's own connection, rather than
    only a theoretical backstop for some other, hypothetical
    direct-Postgres access path.

    Uses `set_config(..., true)` rather than a literal `SET LOCAL`
    statement: Postgres's `SET` command does not accept bind parameters
    at all (`SET LOCAL app.x = $1` is a syntax error, discovered by
    actually running this against a real Postgres connection, not just
    reading the docs) -- `set_config` is a normal function call and
    supports parameter binding like any other.

    `user_id` is set on every authenticated request, independent of
    tenant -- `GET /me` and account bootstrap (`get_or_create_user`)
    intentionally span multiple tenants or run before any tenant is
    established, and RLS policies allow "see/create your own row"
    unconditionally alongside "see rows in your current tenant".

    `tenant_id` is set only once a single definite tenant context exists
    for the request (`resolve_tenant_context`, or explicitly during
    org-creation bootstrap right after the new organization's id is
    known -- see organizations/service.py).

    No-op on SQLite (the local test stand-in, see backend/tests/README.md)
    -- SQLite has no RLS and doesn't understand session variables at all;
    `scoped_to_tenant`'s WHERE-filtering is the only enforcement that
    applies there, which is exactly why RLS needs a real Postgres
    connection to verify (backend/tests/rls/).
    """
    if not _is_postgres(db):
        return

    await db.execute(
        text("SELECT set_config('app.current_user_id', :user_id, true)"),
        {"user_id": str(user_id)},
    )
    if tenant_id is not None:
        await db.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )


async def set_pg_tenant_context(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Sets only the tenant session variable -- used by the org-creation
    bootstrap flow (organizations/service.py) once the new organization's
    id is known, without re-setting the actor (already set earlier in
    that same request). No-op on SQLite, same as set_pg_actor_context.
    """
    if not _is_postgres(db):
        return

    await db.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )
