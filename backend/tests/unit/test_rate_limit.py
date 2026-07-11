from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.tenancy.rate_limit import TenantRateLimitMiddleware


def _build_test_app(limit: int) -> FastAPI:
    app = FastAPI()
    app.add_middleware(TenantRateLimitMiddleware, requests_per_window=limit, window_seconds=60)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"pong": "ok"}

    return app


def test_requests_under_the_limit_pass_through() -> None:
    client = TestClient(_build_test_app(limit=5))

    for _ in range(5):
        response = client.get("/ping", headers={"X-Organization-Id": "tenant-a"})
        assert response.status_code == 200


def test_requests_over_the_limit_get_429_with_retry_after() -> None:
    client = TestClient(_build_test_app(limit=3))

    for _ in range(3):
        client.get("/ping", headers={"X-Organization-Id": "tenant-a"})

    response = client.get("/ping", headers={"X-Organization-Id": "tenant-a"})

    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert int(response.headers["Retry-After"]) > 0


def test_rate_limits_are_tracked_independently_per_tenant() -> None:
    """A different tenant hitting its own limit must not be affected by
    another tenant's usage -- the noisy-neighbor scenario BE3.6 exists to
    prevent."""
    client = TestClient(_build_test_app(limit=2))

    for _ in range(2):
        client.get("/ping", headers={"X-Organization-Id": "tenant-a"})
    blocked = client.get("/ping", headers={"X-Organization-Id": "tenant-a"})
    assert blocked.status_code == 429

    # Tenant B has made zero requests -- still allowed.
    allowed = client.get("/ping", headers={"X-Organization-Id": "tenant-b"})
    assert allowed.status_code == 200


def test_requests_without_an_organization_header_are_rate_limited_by_ip() -> None:
    """Pre-tenant requests (e.g. POST /organizations) have no
    X-Organization-Id yet -- confirms the IP fallback key actually
    engages instead of silently exempting these requests from any limit."""
    client = TestClient(_build_test_app(limit=2))

    for _ in range(2):
        client.get("/ping")
    blocked = client.get("/ping")

    assert blocked.status_code == 429
