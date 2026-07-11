import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TenantContext:
    """Resolved once per request (tenancy/middleware.py) and passed
    explicitly to every service function from here on -- never inferred
    from a global/thread-local (Implementation Plan §5 invariant 8, BE2.7).
    """

    tenant_id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    role_name: str
    permissions: frozenset[str] = field(default_factory=frozenset)
    workspace_id: uuid.UUID | None = None

    def has_permission(self, permission_key: str) -> bool:
        return permission_key in self.permissions
