import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.config import get_settings


class TenantRateLimitMiddleware(BaseHTTPMiddleware):
    """Per-tenant request-rate ceiling (BE3.6) -- technical abuse/
    noisy-neighbor protection, independent of and in addition to Sprint
    15.6's plan-based entitlement limits (those are commercial usage
    caps; this is infrastructure protection regardless of plan).

    In-memory fixed-window counter, keyed by the `X-Organization-Id`
    header if present (falling back to client IP for pre-tenant requests
    like `POST /organizations`, which has no tenant yet). In-memory is a
    deliberate MVP simplification: it resets on restart and doesn't share
    state across multiple backend instances -- move to a shared store
    (e.g. Redis) before running more than one backend process behind a
    load balancer.

    A request over the ceiling gets 429 with a Retry-After header, never
    a silent drop or a crash of shared infrastructure (Blueprint §25
    "Tenant rate limits").
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_window: int | None = None,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        settings = get_settings()
        self._limit = requests_per_window or settings.tenant_rate_limit_per_minute
        self._window_seconds = window_seconds
        self._counters: dict[str, tuple[int, float]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_host = request.client.host if request.client else "unknown"
        key = request.headers.get("x-organization-id") or f"ip:{client_host}"

        now = time.monotonic()
        count, window_start = self._counters.get(key, (0, now))

        if now - window_start >= self._window_seconds:
            count, window_start = 0, now

        count += 1
        self._counters[key] = (count, window_start)

        if count > self._limit:
            retry_after = max(1, int(self._window_seconds - (now - window_start)))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded for this tenant."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
