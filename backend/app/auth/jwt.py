import uuid
from dataclasses import dataclass
from functools import lru_cache

import jwt
from jwt import PyJWKClient

from app.config import get_settings


class TokenValidationError(Exception):
    """Raised for any JWT verification failure (missing, expired, tampered,
    wrong audience, malformed subject). Callers should treat every subtype
    the same way: reject the request. See dependencies.py."""


@dataclass(frozen=True)
class TokenClaims:
    user_id: uuid.UUID
    email: str | None


@lru_cache
def _jwks_client(jwks_url: str) -> PyJWKClient:
    """One [PyJWKClient] per JWKS URL, reused across requests -- it caches
    fetched keys internally (keyed by `kid`), so this doesn't hit the
    network on every authenticated request, only once per signing key
    actually seen."""
    return PyJWKClient(jwks_url)


def verify_jwt(token: str) -> TokenClaims:
    """Verify a Supabase-issued JWT and return its claims.

    Branches on the token's own `alg` header (docs/adr/0007-jwt-verification.md,
    now Final):

    - **HS256** -- legacy shared-secret verification. Real Supabase
      projects are moving off this, but a project mid-migration still has
      already-issued tokens signed this way until they individually
      expire, and this is also what backend/tests/conftest.py's
      `make_token` uses for fast, network-free test tokens.
    - **ES256/RS256** -- asymmetric verification against the project's
      JWKS endpoint. Confirmed (Sprint 4) to be this project's actual,
      current signing method (Project Settings -> API -> JWT Keys shows
      an ECC P-256 key as current) -- this is the path real, live tokens
      take today.

    Either branch fails closed on any error (missing config, wrong
    algorithm, expired, tampered, wrong audience, malformed subject) --
    see backend/tests/unit/test_jwt.py.
    """
    settings = get_settings()

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise TokenValidationError(str(exc)) from exc

    try:
        if header.get("alg") == "HS256":
            if not settings.supabase_jwt_secret:
                raise TokenValidationError(
                    "Received an HS256 token but SUPABASE_JWT_SECRET is not configured."
                )
            payload = jwt.decode(
                token,
                key=settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience=settings.supabase_jwt_audience,
            )
        else:
            if not settings.supabase_url:
                raise TokenValidationError("SUPABASE_URL is not configured.")
            jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                key=signing_key.key,
                algorithms=["ES256", "RS256"],
                audience=settings.supabase_jwt_audience,
            )
    except jwt.PyJWTError as exc:
        raise TokenValidationError(str(exc)) from exc

    subject = payload.get("sub")
    if not subject:
        raise TokenValidationError("Token has no subject (sub) claim.")

    try:
        user_id = uuid.UUID(subject)
    except (ValueError, TypeError) as exc:
        raise TokenValidationError("Token subject is not a valid UUID.") from exc

    return TokenClaims(user_id=user_id, email=payload.get("email"))
