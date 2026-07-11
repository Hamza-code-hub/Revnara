import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.organizations.models import Organization
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_organization_creates_org_workspace_and_owner_membership(
    client: AsyncClient,
) -> None:
    user_id = uuid.uuid4()

    response = await client.post(
        "/organizations",
        json={"name": "Acme Corp"},
        headers=auth_headers(user_id=user_id, email="owner@acme.test"),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["organization"]["name"] == "Acme Corp"
    assert body["workspace"]["tenant_id"] == body["organization"]["id"]

    me = await client.get("/me", headers=auth_headers(user_id=user_id, email="owner@acme.test"))
    assert me.status_code == 200
    memberships = me.json()["memberships"]
    assert len(memberships) == 1
    assert memberships[0]["organization_name"] == "Acme Corp"
    assert memberships[0]["role_name"] == "owner"
    assert memberships[0]["status"] == "active"


@pytest.mark.asyncio
async def test_get_me_returns_correct_memberships_for_seeded_user(
    client: AsyncClient,
) -> None:
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()

    await client.post(
        "/organizations",
        json={"name": "Org A"},
        headers=auth_headers(user_id=user_a, email="a@example.test"),
    )
    await client.post(
        "/organizations",
        json={"name": "Org B"},
        headers=auth_headers(user_id=user_b, email="b@example.test"),
    )

    headers_a = auth_headers(user_id=user_a, email="a@example.test")
    response_a = await client.get("/me", headers=headers_a)
    names_a = {m["organization_name"] for m in response_a.json()["memberships"]}
    assert names_a == {"Org A"}

    headers_b = auth_headers(user_id=user_b, email="b@example.test")
    response_b = await client.get("/me", headers=headers_b)
    names_b = {m["organization_name"] for m in response_b.json()["memberships"]}
    assert names_b == {"Org B"}


@pytest.mark.asyncio
async def test_create_organization_rolls_back_atomically_on_mid_transaction_failure(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Forces a failure after the organization row has already been
    flushed (but not committed) and confirms nothing persists -- the
    literal "rollback test" called for by Sprint 2's testing tasks.
    """
    call_count = {"n": 0}
    original_flush = db_session.flush

    async def flaky_flush() -> None:
        call_count["n"] += 1
        # 1st flush: permission catalog. 2nd: organization insert (assigns
        # its id). Raising on the 3rd -- after the role objects have been
        # added to the session but before their flush completes -- proves
        # even an already-flushed-but-uncommitted organization row is
        # rolled back, not just data that never reached the DB at all.
        if call_count["n"] == 3:
            raise RuntimeError("Simulated failure mid-transaction")
        await original_flush()

    monkeypatch.setattr(db_session, "flush", flaky_flush)

    response = await client.post(
        "/organizations",
        json={"name": "Should Not Persist"},
        headers=auth_headers(),
    )

    assert response.status_code == 500

    monkeypatch.setattr(db_session, "flush", original_flush)
    result = await db_session.execute(
        select(Organization).where(Organization.name == "Should Not Persist")
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_organization_creation_fails_closed_when_audit_write_fails(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BE3.4/Enforcement Spec Core Rule #12, at the integration level: if
    the audit event write fails, the entire action it was recording --
    here, organization creation -- must fail closed too, not partially
    succeed with an unrecorded action. This is the same rollback
    mechanism as the test above, specifically targeting the audit
    writer's own flush call (the 5th: permission catalog, organization,
    roles, owner membership, then the audit event) rather than an
    arbitrary earlier one.
    """
    call_count = {"n": 0}
    original_flush = db_session.flush

    async def flaky_flush() -> None:
        call_count["n"] += 1
        if call_count["n"] == 5:
            raise RuntimeError("Simulated audit write failure")
        await original_flush()

    monkeypatch.setattr(db_session, "flush", flaky_flush)

    response = await client.post(
        "/organizations",
        json={"name": "Should Not Persist Either"},
        headers=auth_headers(),
    )

    assert response.status_code == 500

    monkeypatch.setattr(db_session, "flush", original_flush)
    result = await db_session.execute(
        select(Organization).where(Organization.name == "Should Not Persist Either")
    )
    assert result.scalar_one_or_none() is None
