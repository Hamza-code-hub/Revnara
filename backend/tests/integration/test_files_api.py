import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.files.router import get_storage_provider
from app.files.storage import SignedUpload, StorageProvider
from tests.conftest import auth_headers


class _FakeStorageProvider(StorageProvider):
    """Test double for Sprint 4's real Supabase Storage call -- no real
    Supabase project is available in this environment (see
    app/files/storage.py's SupabaseStorageProvider docstring), so the
    HTTP call itself is replaced here; path construction and file-record
    handling (the part the backend fully controls) run for real."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def create_signed_upload_url(self, *, bucket: str, path: str) -> SignedUpload:
        self.calls.append((bucket, path))
        return SignedUpload(upload_url=f"https://storage.test/{bucket}/{path}", token="fake-token")


async def _create_org_and_headers(client: AsyncClient) -> tuple[uuid.UUID, dict[str, str]]:
    owner_id = uuid.uuid4()
    # A unique email per call -- this helper is used more than once within
    # a single test here (unlike test_members_api.py's identically-named
    # helper), and users.email is unique.
    headers = auth_headers(user_id=owner_id, email=f"owner-{owner_id}@example.test")
    response = await client.post("/organizations", json={"name": "Acme"}, headers=headers)
    org_id = uuid.UUID(response.json()["organization"]["id"])
    headers["X-Organization-Id"] = str(org_id)
    return org_id, headers


@pytest.fixture(autouse=True)
def _override_storage_provider(app_under_test: FastAPI) -> None:
    fake = _FakeStorageProvider()
    app_under_test.dependency_overrides[get_storage_provider] = lambda: fake


@pytest.mark.asyncio
async def test_signed_upload_then_confirm_flow(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    signed_response = await client.post(
        f"/organizations/{org_id}/files/signed-upload",
        json={"filename": "proposal.pdf", "content_type": "application/pdf"},
        headers=headers,
    )
    assert signed_response.status_code == 201
    body = signed_response.json()
    assert body["storage_path"].startswith(f"{org_id}/")
    assert body["storage_path"].endswith("_proposal.pdf")

    confirm_response = await client.post(
        f"/organizations/{org_id}/files/{body['file_id']}/confirm",
        json={"size_bytes": 1024},
        headers=headers,
    )
    assert confirm_response.status_code == 200
    confirmed = confirm_response.json()
    assert confirmed["status"] == "uploaded"
    assert confirmed["size_bytes"] == 1024

    list_response = await client.get(f"/organizations/{org_id}/files", headers=headers)
    assert list_response.status_code == 200
    assert any(f["id"] == body["file_id"] for f in list_response.json())


@pytest.mark.asyncio
async def test_confirming_an_already_uploaded_file_is_rejected(client: AsyncClient) -> None:
    """BE4.3 security testing task ("signed URL replay ... denial"): a
    second confirm on an already-finalized file must not silently
    succeed."""
    org_id, headers = await _create_org_and_headers(client)

    signed_response = await client.post(
        f"/organizations/{org_id}/files/signed-upload",
        json={"filename": "proposal.pdf"},
        headers=headers,
    )
    file_id = signed_response.json()["file_id"]

    first_confirm = await client.post(
        f"/organizations/{org_id}/files/{file_id}/confirm", json={}, headers=headers
    )
    assert first_confirm.status_code == 200

    replay_confirm = await client.post(
        f"/organizations/{org_id}/files/{file_id}/confirm", json={}, headers=headers
    )
    assert replay_confirm.status_code == 409


@pytest.mark.asyncio
async def test_path_traversal_filename_is_sanitized_in_the_stored_path(client: AsyncClient) -> None:
    org_id, headers = await _create_org_and_headers(client)

    response = await client.post(
        f"/organizations/{org_id}/files/signed-upload",
        json={"filename": "../../other-tenant/secret.pdf"},
        headers=headers,
    )

    assert response.status_code == 201
    storage_path = response.json()["storage_path"]
    assert storage_path.startswith(f"{org_id}/")
    assert "other-tenant" not in storage_path
    assert ".." not in storage_path


@pytest.mark.asyncio
async def test_confirming_a_file_in_a_different_organization_is_rejected(
    client: AsyncClient,
) -> None:
    org_id, headers = await _create_org_and_headers(client)
    other_org_id, other_headers = await _create_org_and_headers(client)

    signed_response = await client.post(
        f"/organizations/{org_id}/files/signed-upload",
        json={"filename": "proposal.pdf"},
        headers=headers,
    )
    file_id = signed_response.json()["file_id"]

    cross_tenant_confirm = await client.post(
        f"/organizations/{other_org_id}/files/{file_id}/confirm",
        json={},
        headers=other_headers,
    )

    assert cross_tenant_confirm.status_code == 404
