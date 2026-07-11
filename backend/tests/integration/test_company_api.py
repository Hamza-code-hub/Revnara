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
async def test_get_and_update_organization_profile(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    initial = await client.get(f"/organizations/{org_id}", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["description"] is None

    update_response = await client.patch(
        f"/organizations/{org_id}",
        json={"description": "We build software.", "industry": "Software", "founded_year": 2020},
        headers=headers,
    )
    assert update_response.status_code == 200
    body = update_response.json()
    assert body["name"] == "Acme"
    assert body["description"] == "We build software."
    assert body["founded_year"] == 2020

    fetched_again = await client.get(f"/organizations/{org_id}", headers=headers)
    assert fetched_again.json()["industry"] == "Software"


@pytest.mark.asyncio
async def test_skill_crud_flow(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    create_response = await client.post(
        f"/organizations/{org_id}/skills",
        json={"name": "Flutter", "category": "Frontend"},
        headers=headers,
    )
    assert create_response.status_code == 201
    skill = create_response.json()
    assert skill["name"] == "Flutter"

    list_response = await client.get(f"/organizations/{org_id}/skills", headers=headers)
    assert list_response.status_code == 200
    assert any(s["id"] == skill["id"] for s in list_response.json())

    update_response = await client.patch(
        f"/organizations/{org_id}/skills/{skill['id']}",
        json={"category": "Mobile"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["category"] == "Mobile"

    delete_response = await client.delete(
        f"/organizations/{org_id}/skills/{skill['id']}", headers=headers
    )
    assert delete_response.status_code == 204

    list_after_delete = await client.get(f"/organizations/{org_id}/skills", headers=headers)
    assert all(s["id"] != skill["id"] for s in list_after_delete.json())


@pytest.mark.asyncio
async def test_team_member_crud_with_skill_associations(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    skill_response = await client.post(
        f"/organizations/{org_id}/skills", json={"name": "FastAPI"}, headers=headers
    )
    skill_id = skill_response.json()["id"]

    create_response = await client.post(
        f"/organizations/{org_id}/team-members",
        json={"name": "Alex Rivera", "title": "Engineer", "skill_ids": [skill_id]},
        headers=headers,
    )
    assert create_response.status_code == 201
    member = create_response.json()
    assert member["name"] == "Alex Rivera"
    assert [s["id"] for s in member["skills"]] == [skill_id]

    update_response = await client.patch(
        f"/organizations/{org_id}/team-members/{member['id']}",
        json={"skill_ids": []},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["skills"] == []

    delete_response = await client.delete(
        f"/organizations/{org_id}/team-members/{member['id']}", headers=headers
    )
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_portfolio_item_and_case_study_crud(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    portfolio_response = await client.post(
        f"/organizations/{org_id}/portfolio-items",
        json={"title": "Inventory Rebuild", "classification": "public"},
        headers=headers,
    )
    assert portfolio_response.status_code == 201
    portfolio_item = portfolio_response.json()

    case_study_response = await client.post(
        f"/organizations/{org_id}/case-studies",
        json={
            "portfolio_item_id": portfolio_item["id"],
            "title": "How We Rebuilt Inventory",
            "classification": "confidential",
        },
        headers=headers,
    )
    assert case_study_response.status_code == 201
    case_study = case_study_response.json()
    assert case_study["classification"] == "confidential"

    update_response = await client.patch(
        f"/organizations/{org_id}/case-studies/{case_study['id']}",
        json={"classification": "public"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["classification"] == "public"

    delete_portfolio = await client.delete(
        f"/organizations/{org_id}/portfolio-items/{portfolio_item['id']}", headers=headers
    )
    assert delete_portfolio.status_code == 204


@pytest.mark.asyncio
async def test_member_without_company_manage_permission_cannot_create_skill(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A plain "member" role has no `company.manage` grant by default
    (permissions_catalog.DEFAULT_ROLE_PERMISSIONS) -- same seeding
    approach as test_members_api.py's equivalent test, since there's no
    accept-invite flow yet to reach an active plain-member state through
    the API alone."""
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
        f"/organizations/{org_id}/skills", json={"name": "Flutter"}, headers=plain_headers
    )

    assert response.status_code == 403

    # But a plain member can still read the company brain -- read access
    # only requires an active membership, not company.manage.
    read_response = await client.get(
        f"/organizations/{org_id}/skills", headers=plain_headers
    )
    assert read_response.status_code == 200


@pytest.mark.asyncio
async def test_cannot_manage_skills_for_a_different_organization(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    other_org_id = uuid.uuid4()

    response = await client.post(
        f"/organizations/{other_org_id}/skills", json={"name": "Flutter"}, headers=headers
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bad_input_is_rejected_with_422_not_persisted(client: AsyncClient) -> None:
    """End-to-end version of tests/unit/test_company_schemas.py's
    validation rules -- confirms they actually apply at the API layer,
    not just when constructing the Pydantic model directly."""
    org_id, headers = await _create_org_and_headers(client)

    empty_skill_name = await client.post(
        f"/organizations/{org_id}/skills", json={"name": ""}, headers=headers
    )
    assert empty_skill_name.status_code == 422

    negative_rate = await client.post(
        f"/organizations/{org_id}/team-members",
        json={"name": "Alex Rivera", "hourly_rate": -10},
        headers=headers,
    )
    assert negative_rate.status_code == 422

    list_response = await client.get(f"/organizations/{org_id}/skills", headers=headers)
    assert list_response.json() == []
