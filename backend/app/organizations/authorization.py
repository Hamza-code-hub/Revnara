from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status

from app.tenancy.context import TenantContext
from app.tenancy.middleware import resolve_tenant_context


def require_permission(permission_key: str) -> Callable[[TenantContext], Awaitable[TenantContext]]:
    """FastAPI dependency factory: `Depends(require_permission("members.invite"))`
    in place of `Depends(resolve_tenant_context)` directly on any route that
    needs a specific permission, not just an active membership.

    Formalizes Sprint 2's inline `_require_permission` check (previously
    duplicated per-route in invitations.py) into the single reusable
    dependency the sprint plan calls for -- callers didn't change their
    permission-key strings, only how the check is wired in.
    """

    async def _check(
        tenant: TenantContext = Depends(resolve_tenant_context),
    ) -> TenantContext:
        if not tenant.has_permission(permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission_key}",
            )
        return tenant

    return _check
