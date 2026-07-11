# ADR 0007: JWT Verification Method

**Status:** Provisional -- confirm against the team's actual Supabase project before Sprint 2 is considered fully done.

## Context

Sprint 2 (`docs/Revnara_Sprint_Development_Plan.md`) requires the backend to verify Supabase-issued JWTs on every authenticated request. Supabase supports two verification approaches:

1. **HS256, shared secret** -- the project's JWT secret (found in the Supabase dashboard) is used to verify the signature directly. Simple, no network call, but the secret is a long-lived shared credential.
2. **RS256/ES256, JWKS (asymmetric)** -- Supabase publishes public signing keys at a JWKS endpoint; the backend fetches and caches them, verifying without holding a shared secret. Newer Supabase projects default to this; requires network access to the JWKS endpoint and key caching/rotation handling.

No live Supabase project exists yet in this environment (§4 Environment Prerequisites is still open), so which method the team's actual project uses could not be confirmed empirically.

## Decision

Implemented **HS256 shared-secret verification** (`backend/app/auth/jwt.py`) as the initial path: no live network dependency, easy to unit test with a known test secret, and historically the default for Supabase projects.

## Consequences

- `SUPABASE_JWT_SECRET` and `SUPABASE_JWT_AUDIENCE` (defaults to `authenticated`, Supabase's standard claim) must be set from the real project's dashboard once it exists.
- **If the team's Supabase project is actually configured for JWKS/RS256** (check Project Settings -> API -> JWT Settings), `verify_jwt` needs to be extended with a JWKS client (e.g. `PyJWKClient` from PyJWT) before Sprint 2 can be considered done against the real environment -- the HS256 path will simply fail closed (raises `TokenValidationError`) against an RS256-signed token, it will not silently accept it.
- Either way, tokens are rejected fail-closed on any verification failure (missing secret, wrong algorithm, expired, tampered, wrong audience, malformed subject) -- see `backend/tests/unit/test_jwt.py`.

## Review

Revisit once a real Supabase project is provisioned (§4) -- confirm the actual signing method in the dashboard and update this ADR's Status to Final either way.
