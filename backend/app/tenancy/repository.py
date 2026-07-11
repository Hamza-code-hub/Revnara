import uuid
from typing import Any

from sqlalchemy import Select


def scoped_to_tenant[RowT: tuple[Any, ...]](
    stmt: Select[RowT], model: type[Any], tenant_id: uuid.UUID
) -> Select[RowT]:
    """The single place a tenant filter gets applied to a query -- route
    every tenant-scoped `select()` through this rather than writing
    `.where(Model.tenant_id == tenant_id)` inline at each call site.

    This is defense in depth alongside RLS (Blueprint §25
    "tenant-aware repositories"), not a replacement for it: RLS protects
    against a query that skips this helper entirely; this helper is what
    makes "does this query call scoped_to_tenant, and if not, why not?" a
    one-line code-review question instead of an inline judgment call
    scattered across every service file.

    `model` takes the class (not `model.tenant_id`) so a missing
    `tenant_id` column on a model raises here immediately, at the
    call site, rather than silently matching zero rows. `RowT` (bound to
    a row tuple, matching Select's own generic parameter) preserves the
    specific row type through this function -- a plain `Select[Any]`
    here would silently turn every caller's `scalar_one_or_none()` result
    into `Any` too, defeating strict mypy for every query that uses this
    helper.
    """
    return stmt.where(model.tenant_id == tenant_id)
