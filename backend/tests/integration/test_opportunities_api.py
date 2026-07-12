import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.opportunities.models import (
    Opportunity,
    OpportunityStatus,
    SafetyScreeningStatus,
)
from app.organizations.models import MemberStatus, OrganizationMember, Role
from tests.conftest import auth_headers


async def _create_org_and_headers(
    client: AsyncClient, *, name: str = "Acme"
) -> tuple[uuid.UUID, dict[str, str]]:
    owner_id = uuid.uuid4()
    headers = auth_headers(user_id=owner_id, email=f"owner-{owner_id}@example.test")
    response = await client.post("/organizations", json={"name": name}, headers=headers)
    org_id = uuid.UUID(response.json()["organization"]["id"])
    headers["X-Organization-Id"] = str(org_id)
    return org_id, headers


@pytest.mark.asyncio
async def test_manual_create_clean_opportunity_is_screened_clear(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    response = await client.post(
        f"/organizations/{org_id}/opportunities",
        json={
            "title": "Inventory Sync Platform Rebuild",
            "description": "Replace a legacy inventory sync job.",
            "budget_min": 40000,
            "budget_max": 65000,
            "budget_currency": "USD",
            "client_name": "Meridian Retail",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == OpportunityStatus.SCREENING.value
    assert body["safety_screening_status"] == SafetyScreeningStatus.CLEAR.value
    assert body["safety_screening_flags"] is None
    assert body["client_id"] is not None


@pytest.mark.asyncio
async def test_manual_create_suspicious_opportunity_is_flagged(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    response = await client.post(
        f"/organizations/{org_id}/opportunities",
        json={
            "title": "Wire Transfer Only Required - Urgent, Start Today",
            "description": "Payment will be made via wire transfer only.",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["safety_screening_status"] == SafetyScreeningStatus.FLAGGED.value
    assert "suspicious_payment_terms" in body["safety_screening_flags"]
    assert "urgency_pressure_language" in body["safety_screening_flags"]


@pytest.mark.asyncio
async def test_import_link_never_calls_out_stores_metadata_only(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    response = await client.post(
        f"/organizations/{org_id}/opportunities/import-link",
        json={
            "url": "https://www.upwork.com/jobs/~unreachable-example-should-never-be-fetched",
            "title": "Data Warehouse Modernization",
            "budget_min": 50000,
            "budget_max": 90000,
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Data Warehouse Modernization"
    assert body["safety_screening_status"] == SafetyScreeningStatus.CLEAR.value


@pytest.mark.asyncio
async def test_csv_import_partial_success(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    csv_content = (
        "title,description,budget_min\n"
        "Good Row One,First imported opportunity,1000\n"
        ",Missing title on purpose,2000\n"
        "Good Row Two,Second imported opportunity,not-a-number\n"
    )
    response = await client.post(
        f"/organizations/{org_id}/opportunities/import",
        headers=headers,
        files={"file": ("opportunities.csv", csv_content, "text/csv")},
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["created"]) == 1
    assert body["created"][0]["title"] == "Good Row One"
    assert len(body["errors"]) == 2
    assert body["errors"][0]["row_number"] == 3
    assert body["errors"][1]["row_number"] == 4


@pytest.mark.asyncio
async def test_list_and_get_opportunity(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    create_response = await client.post(
        f"/organizations/{org_id}/opportunities",
        json={"title": "First Opportunity"},
        headers=headers,
    )
    opportunity_id = create_response.json()["id"]

    list_response = await client.get(f"/organizations/{org_id}/opportunities", headers=headers)
    assert list_response.status_code == 200
    assert any(o["id"] == opportunity_id for o in list_response.json())

    get_response = await client.get(
        f"/organizations/{org_id}/opportunities/{opportunity_id}", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "First Opportunity"


@pytest.mark.asyncio
async def test_get_opportunity_client_generates_research_brief_once(
    client: AsyncClient,
) -> None:
    org_id, headers = await _create_org_and_headers(client)

    create_response = await client.post(
        f"/organizations/{org_id}/opportunities",
        json={"title": "Website Redesign", "client_name": "Acme Retail"},
        headers=headers,
    )
    opportunity_id = create_response.json()["id"]

    first = await client.get(
        f"/organizations/{org_id}/opportunities/{opportunity_id}/client", headers=headers
    )
    assert first.status_code == 200
    brief = first.json()["research_brief"]
    assert brief is not None
    assert "Acme Retail" in brief
    # The opportunity being viewed is itself already "prior history" by
    # the time the brief is generated (it was created and committed
    # first), so it shows up in its own client's brief.
    assert "1 opportunity on file" in brief

    # A second request must not regenerate the brief (only persisted once).
    second = await client.get(
        f"/organizations/{org_id}/opportunities/{opportunity_id}/client", headers=headers
    )
    assert second.json()["research_brief"] == brief


@pytest.mark.asyncio
async def test_member_without_opportunities_manage_permission_is_forbidden(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Unlike company.manage, opportunities.manage IS granted to plain
    members by default (permissions_catalog.DEFAULT_ROLE_PERMISSIONS) --
    so this test uses a role with no permissions at all to prove the
    dependency actually enforces something, rather than asserting
    behavior that would pass even with the check removed."""
    org_id, owner_headers = await _create_org_and_headers(client)

    member_role = (
        await db_session.execute(
            select(Role).where(Role.tenant_id == org_id, Role.name == "member")
        )
    ).scalar_one()

    # Strip the default opportunities.manage grant from the member role to
    # get a role with genuinely zero permissions for this negative test.
    from app.organizations.models import RolePermission

    await db_session.execute(
        RolePermission.__table__.delete().where(RolePermission.role_id == member_role.id)
    )
    await db_session.commit()

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
        f"/organizations/{org_id}/opportunities",
        json={"title": "Should be forbidden"},
        headers=plain_headers,
    )
    assert response.status_code == 403

    # But list/get (read) only requires active membership.
    read_response = await client.get(
        f"/organizations/{org_id}/opportunities", headers=plain_headers
    )
    assert read_response.status_code == 200


@pytest.mark.asyncio
async def test_member_with_default_permissions_can_create_opportunity(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """The Sprint 6 permission decision: opportunity creation is granted
    to plain members by default, unlike company.manage."""
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
        f"/organizations/{org_id}/opportunities",
        json={"title": "Member-created opportunity"},
        headers=plain_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_cannot_access_opportunities_for_a_different_organization(
    client: AsyncClient,
) -> None:
    org_id, headers = await _create_org_and_headers(client)
    other_org_id = uuid.uuid4()

    response = await client.get(f"/organizations/{other_org_id}/opportunities", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_opportunities_are_tenant_isolated(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    org_a_id, headers_a = await _create_org_and_headers(client, name="Acme")
    org_b_id, headers_b = await _create_org_and_headers(client, name="Beta")

    create_response = await client.post(
        f"/organizations/{org_a_id}/opportunities",
        json={"title": "Tenant A's opportunity"},
        headers=headers_a,
    )
    opportunity_id = create_response.json()["id"]

    # Tenant B genuinely cannot see tenant A's opportunity in its own list.
    list_response = await client.get(f"/organizations/{org_b_id}/opportunities", headers=headers_b)
    assert all(o["id"] != opportunity_id for o in list_response.json())

    result = await db_session.execute(
        select(Opportunity).where(Opportunity.id == uuid.UUID(opportunity_id))
    )
    assert result.scalar_one().tenant_id == org_a_id
