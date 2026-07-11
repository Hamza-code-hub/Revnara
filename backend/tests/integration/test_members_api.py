import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.organizations.models import MemberStatus, OrganizationMember, Role
from tests.conftest import auth_headers


async def _create_org_and_headers(client: AsyncClient) -> tuple[uuid.UUID, dict[str, str]]:
    owner_id = uuid.uuid4()
    headers = auth_headers(user_id=owner_id, email="owner@example.test")
    response = await client.post("/organizations", json={"name": "Acme"}, headers=headers)
    org_id = uuid.UUID(response.json()["organization"]["id"])
    headers["X-Organization-Id"] = str(org_id)
    return org_id, headers


@pytest.mark.asyncio
async def test_invite_list_and_role_change_flow(client: AsyncClient) -> None:
    org_id, owner_headers = await _create_org_and_headers(client)

    invite_response = await client.post(
        f"/organizations/{org_id}/invitations",
        json={"email": "newperson@acme.io", "role_name": "member"},
        headers=owner_headers,
    )
    assert invite_response.status_code == 201
    member = invite_response.json()
    assert member["status"] == "pending"
    assert member["invited_email"] == "newperson@acme.io"

    list_response = await client.get(
        f"/organizations/{org_id}/members", headers=owner_headers
    )
    assert list_response.status_code == 200
    emails = {m["email"] for m in list_response.json()}
    assert "newperson@acme.io" in emails

    role_change = await client.patch(
        f"/organizations/{org_id}/members/{member['id']}",
        json={"role_name": "admin"},
        headers=owner_headers,
    )
    assert role_change.status_code == 200
    assert role_change.json()["role_name"] == "admin"


@pytest.mark.asyncio
async def test_deactivate_member_blocks_further_access(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """BE2.9 end to end: deactivate a second, *active* member, confirm
    their very next authenticated request is rejected -- and specifically
    because of deactivation, not merely because no membership exists.

    Seeded directly as active (not via the invitations endpoint): an
    invited member's row has no `user_id` until they accept, since no
    `User` row exists for an email that hasn't authenticated yet (see
    get_or_create_user). Going through the invite flow here would make
    this test pass for the wrong reason -- an unmatched `user_id`, not an
    enforced deactivation -- which is exactly the kind of test bug worth
    avoiding deliberately.
    """
    org_id, owner_headers = await _create_org_and_headers(client)

    member_role = (
        await db_session.execute(
            select(Role).where(Role.tenant_id == org_id, Role.name == "member")
        )
    ).scalar_one()

    second_user_id = uuid.uuid4()
    membership = OrganizationMember(
        tenant_id=org_id,
        user_id=second_user_id,
        role_id=member_role.id,
        status=MemberStatus.ACTIVE,
    )
    db_session.add(membership)
    await db_session.commit()

    second_headers = auth_headers(user_id=second_user_id, email="second@example.test")
    second_headers["X-Organization-Id"] = str(org_id)

    # Confirm access works *before* deactivation, so the later 403 is
    # attributable to deactivation specifically.
    pre_deactivation = await client.get("/workspaces", headers=second_headers)
    assert pre_deactivation.status_code == 200

    deactivate_response = await client.delete(
        f"/organizations/{org_id}/members/{membership.id}", headers=owner_headers
    )
    assert deactivate_response.status_code == 204

    blocked_response = await client.get("/workspaces", headers=second_headers)
    assert blocked_response.status_code == 403


@pytest.mark.asyncio
async def test_member_without_permission_cannot_invite(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A plain "member" role has no `members.invite` grant by default
    (permissions_catalog.DEFAULT_ROLE_PERMISSIONS) -- seeded directly as
    an *active* membership, since there's no accept-invite flow yet to
    reach this state through the API (see invitations.py's note on
    Supabase Admin API being required for that)."""
    org_id, owner_headers = await _create_org_and_headers(client)

    member_role = (
        await db_session.execute(
            select(Role).where(Role.tenant_id == org_id, Role.name == "member")
        )
    ).scalar_one()

    plain_user_id = uuid.uuid4()
    db_session.add(
        OrganizationMember(
            tenant_id=org_id,
            user_id=plain_user_id,
            role_id=member_role.id,
            status=MemberStatus.ACTIVE,
        )
    )
    await db_session.commit()

    plain_headers = auth_headers(user_id=plain_user_id, email="plain@example.test")
    plain_headers["X-Organization-Id"] = str(org_id)

    response = await client.post(
        f"/organizations/{org_id}/invitations",
        json={"email": "someone@acme.io", "role_name": "member"},
        headers=plain_headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_missing_token_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_workspaces_requires_organization_header(client: AsyncClient) -> None:
    response = await client.get("/workspaces", headers=auth_headers())
    assert response.status_code == 422  # missing required X-Organization-Id header
