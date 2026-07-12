import uuid

import pytest
from httpx import AsyncClient

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


async def _create_skill(client: AsyncClient, org_id: uuid.UUID, headers: dict, name: str) -> str:
    response = await client.post(
        f"/organizations/{org_id}/skills", json={"name": name}, headers=headers
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_team_member(
    client: AsyncClient, org_id: uuid.UUID, headers: dict, *, name: str, skill_ids: list[str]
) -> dict:
    response = await client.post(
        f"/organizations/{org_id}/team-members",
        json={"name": name, "skill_ids": skill_ids},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


async def _create_opportunity(client: AsyncClient, org_id: uuid.UUID, headers: dict, **kw) -> dict:
    response = await client.post(
        f"/organizations/{org_id}/opportunities",
        json={"title": "Website Redesign", "description": "Needs Flutter expertise.", **kw},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_qualify_persists_score_reasons_and_explainability(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    await _create_skill(client, org_id, headers, "Flutter")
    opportunity = await _create_opportunity(
        client, org_id, headers, budget_min=1000, budget_max=2000
    )

    qualify_response = await client.post(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualify", headers=headers
    )
    assert qualify_response.status_code == 200
    body = qualify_response.json()
    assert body["score"] == 100
    assert body["reasons"]
    assert body["evidence"]

    explainability_response = await client.get(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualification/explainability",
        headers=headers,
    )
    assert explainability_response.status_code == 200
    explain_body = explainability_response.json()
    assert explain_body["decision"] == "qualification_score"
    assert explain_body["rules_applied"]
    assert explain_body["confidence"] == 1.0

    get_response = await client.get(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualification", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json()["score"] == 100


@pytest.mark.asyncio
async def test_requalifying_replaces_the_current_result_not_appends(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    opportunity = await _create_opportunity(client, org_id, headers)

    first = await client.post(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualify", headers=headers
    )
    second = await client.post(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualify", headers=headers
    )
    assert first.json()["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_cannot_qualify_a_flagged_opportunity(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    opportunity = await _create_opportunity(
        client,
        org_id,
        headers,
        title="Wire Transfer Only Required - Urgent, Start Today",
        description="Payment will be made via wire transfer only.",
    )
    assert opportunity["safety_screening_status"] == "screened_flagged"

    response = await client.post(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualify", headers=headers
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_match_team_recommends_matching_member_and_flags_gaps(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    flutter_id = await _create_skill(client, org_id, headers, "Flutter")
    await _create_skill(client, org_id, headers, "FastAPI")
    member = await _create_team_member(
        client, org_id, headers, name="Alex", skill_ids=[flutter_id]
    )
    opportunity = await _create_opportunity(
        client, org_id, headers, description="Needs Flutter and FastAPI expertise."
    )

    match_response = await client.post(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/match-team", headers=headers
    )
    assert match_response.status_code == 200
    body = match_response.json()
    assert body["recommended_team_member_ids"] == [member["id"]]
    assert body["delivery_risk"] == "medium"
    assert body["gaps"] == ["FastAPI"]

    explainability_response = await client.get(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/team-match/explainability",
        headers=headers,
    )
    assert explainability_response.status_code == 200
    assert explainability_response.json()["decision"] == "team_match_recommendation"


@pytest.mark.asyncio
async def test_qualification_override_is_recorded_and_applied(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    opportunity = await _create_opportunity(client, org_id, headers)
    await client.post(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualify", headers=headers
    )

    override_response = await client.patch(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualification",
        json={"score": 95, "reason": "Client relationship is stronger than the score suggests."},
        headers=headers,
    )
    assert override_response.status_code == 200
    assert override_response.json()["score"] == 95

    overrides_response = await client.get(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualification/overrides",
        headers=headers,
    )
    assert overrides_response.status_code == 200
    overrides = overrides_response.json()
    assert len(overrides) == 1
    assert overrides[0]["field"] == "score"
    assert overrides[0]["new_value"] == 95
    assert "stronger than the score" in overrides[0]["reason"]


@pytest.mark.asyncio
async def test_qualification_override_requires_a_reason(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    opportunity = await _create_opportunity(client, org_id, headers)
    await client.post(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualify", headers=headers
    )

    response = await client.patch(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/qualification",
        json={"score": 95, "reason": ""},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_team_match_override_is_recorded_and_applied(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    flutter_id = await _create_skill(client, org_id, headers, "Flutter")
    member_a = await _create_team_member(
        client, org_id, headers, name="Alex", skill_ids=[flutter_id]
    )
    member_b = await _create_team_member(client, org_id, headers, name="Jordan", skill_ids=[])
    opportunity = await _create_opportunity(client, org_id, headers)

    await client.post(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/match-team", headers=headers
    )

    override_response = await client.patch(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/team-match",
        json={
            "recommended_team_member_ids": [member_b["id"]],
            "reason": "Alex is already fully booked this sprint.",
        },
        headers=headers,
    )
    assert override_response.status_code == 200
    assert override_response.json()["recommended_team_member_ids"] == [member_b["id"]]

    overrides_response = await client.get(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/team-match/overrides",
        headers=headers,
    )
    overrides = overrides_response.json()
    assert len(overrides) == 1
    assert overrides[0]["field"] == "recommended_team_member_ids"
    assert overrides[0]["original_value"] == [member_a["id"]]


@pytest.mark.asyncio
async def test_legal_status_transition_succeeds(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    opportunity = await _create_opportunity(client, org_id, headers)
    assert opportunity["status"] == "screening"

    response = await client.patch(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/status",
        json={"status": "qualifying"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "qualifying"


@pytest.mark.asyncio
async def test_illegal_status_transition_is_rejected(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    opportunity = await _create_opportunity(client, org_id, headers)

    response = await client.patch(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/status",
        json={"status": "won"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cannot_transition_out_of_a_terminal_status(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)
    opportunity = await _create_opportunity(client, org_id, headers)

    disqualify_response = await client.patch(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/status",
        json={"status": "disqualified"},
        headers=headers,
    )
    assert disqualify_response.status_code == 200

    reopen_response = await client.patch(
        f"/organizations/{org_id}/opportunities/{opportunity['id']}/status",
        json={"status": "screening"},
        headers=headers,
    )
    assert reopen_response.status_code == 400


@pytest.mark.asyncio
async def test_qualification_and_team_match_results_are_tenant_isolated(
    client: AsyncClient,
) -> None:
    org_a_id, headers_a = await _create_org_and_headers(client, name="Acme")
    org_b_id, headers_b = await _create_org_and_headers(client, name="Beta")

    opportunity = await _create_opportunity(client, org_a_id, headers_a)
    await client.post(
        f"/organizations/{org_a_id}/opportunities/{opportunity['id']}/qualify", headers=headers_a
    )

    cross_tenant_response = await client.get(
        f"/organizations/{org_b_id}/opportunities/{opportunity['id']}/qualification",
        headers=headers_b,
    )
    assert cross_tenant_response.status_code == 404
