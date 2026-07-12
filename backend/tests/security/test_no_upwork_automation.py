"""FE6.3/BE6.2's human-native guarantee: Revnara never visits a pasted
Upwork (or any platform) link, and never automates a browser/API against
it -- the user stays the only one who ever submits anything. Two layers
of proof, not one:

1. Static: the opportunities package imports no networking or browser-
   automation library at all, so the *capability* to reach out doesn't
   exist in this code path, regardless of what any future change to the
   import-link handler might try to do accidentally.
2. Dynamic: hitting the real import-link endpoint with a real (but
   unreachable-by-design) URL succeeds without ever opening a socket --
   proven by blocking every socket connection attempt for the duration
   of the request, not by asserting on absence of an error.
"""

import socket
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers

_FORBIDDEN_IMPORTS = (
    "httpx",
    "requests",
    "aiohttp",
    "urllib.request",
    "playwright",
    "selenium",
)

_OPPORTUNITIES_PACKAGE_DIR = Path(__file__).resolve().parents[2] / "app" / "opportunities"


def test_opportunities_package_imports_no_networking_library() -> None:
    for path in _OPPORTUNITIES_PACKAGE_DIR.glob("*.py"):
        source = path.read_text()
        for forbidden in _FORBIDDEN_IMPORTS:
            assert f"import {forbidden}" not in source, (
                f"{path.name} imports {forbidden!r} -- the opportunity intake/import-link "
                "path must never gain the capability to make outbound network calls."
            )


@pytest.mark.asyncio
async def test_import_link_never_opens_a_real_socket(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _blocked_connect(self: socket.socket, address: object) -> None:
        raise AssertionError(
            f"opportunity import-link made a real socket connection to {address!r} -- "
            "this handler must only ever store the pasted link, never fetch it."
        )

    monkeypatch.setattr(socket.socket, "connect", _blocked_connect)

    owner_id = uuid.uuid4()
    headers = auth_headers(user_id=owner_id, email="owner@example.test")
    org_response = await client.post("/organizations", json={"name": "Acme"}, headers=headers)
    org_id = org_response.json()["organization"]["id"]
    headers["X-Organization-Id"] = org_id

    response = await client.post(
        f"/organizations/{org_id}/opportunities/import-link",
        json={
            "url": "https://www.upwork.com/jobs/~this-domain-must-never-be-contacted",
            "title": "Some listing",
        },
        headers=headers,
    )

    assert response.status_code == 201
