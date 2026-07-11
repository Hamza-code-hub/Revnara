import uuid
from dataclasses import dataclass

import jwt

from app.config import get_settings


class TokenValidationError(Exception):
    """Raised for any JWT verification failure (missing, expired, tampered,
    wrong audience, malformed subject). Callers should treat every subtype
    the same way: reject the request. See dependencies.py."""


@dataclass(frozen=True)
class TokenClaims:
    user_id: uuid.UUID
    email: str | None


def verify_jwt(token: str) -> TokenClaims:
    """Verify a Supabase-issued JWT and return its claims.

    Uses HS256 shared-secret verification (docs/adr/0007-jwt-verification.md)
    -- Supabase also supports RS256/JWKS asymmetric verification, which
    requires fetching and caching a live JWKS endpoint; that path isn't
    implemented here and should be revisited if the team's Supabase project
    is configured for asymmetric signing (confirm against the actual
    project's Auth settings, not assumed).
    """
    settings = get_settings()
    if not settings.supabase_jwt_secret:
        raise TokenValidationError("SUPABASE_JWT_SECRET is not configured.")

    try:
        payload = jwt.decode(
            token,
            key=settings.supabase_jwt_secret,
            algorithms=["HS256"],
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
