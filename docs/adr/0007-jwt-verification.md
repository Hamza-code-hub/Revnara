# ADR 0007: JWT Verification Method

**Status:** Final -- confirmed against a real, live Supabase project (see Decision).

## Context

Sprint 2 (`docs/Revnara_Sprint_Development_Plan.md`) requires the backend to verify Supabase-issued JWTs on every authenticated request. Supabase supports two verification approaches:

1. **HS256, shared secret** -- the project's JWT secret (found in the Supabase dashboard) is used to verify the signature directly. Simple, no network call, but the secret is a long-lived shared credential.
2. **RS256/ES256, JWKS (asymmetric)** -- Supabase publishes public signing keys at a JWKS endpoint; the backend fetches and caches them, verifying without holding a shared secret. Newer Supabase projects default to this; requires network access to the JWKS endpoint and key caching/rotation handling.

No live Supabase project existed at the time this was first written (Sprint 2), so which method the team's actual project uses could not be confirmed empirically. A real project was provisioned in Sprint 4 (`nbnmlfsxtiivvvoxuhdr`) -- **Project Settings -> API -> JWT Keys shows an ECC (P-256) key as the current signing key**, with a legacy HS256 shared secret listed only under "previously used keys" (retired, kept solely to verify already-issued tokens until they individually expire). This project is on the newer asymmetric-signing path, not the legacy HS256 one.

## Decision

`backend/app/auth/jwt.py`'s `verify_jwt` branches on the token's own `alg` header:

- **`alg: ES256` (or `RS256`)** -- verified against the project's JWKS endpoint (`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`) via `PyJWKClient`, which caches fetched keys by `kid` so this isn't a network round-trip on every request. **This is the path real tokens from the live project take.**
- **`alg: HS256`** -- verified against `SUPABASE_JWT_SECRET` directly. Kept for two reasons: (1) any already-issued tokens from before this project's key rotation are still HS256-signed until they individually expire, and a project that hasn't rotated at all would need this path entirely; (2) `backend/tests/conftest.py`'s `make_token` test helper uses a local HS256 secret specifically so the test suite doesn't need network access to a real JWKS endpoint.

Both branches fail closed on any error -- a token with neither a configured secret (HS256) nor a reachable JWKS endpoint (ES256/RS256) is rejected, not silently accepted.

## Consequences

- `SUPABASE_URL` must be set to the real project's URL for the ES256/JWKS path to work at all -- this is the path that matters for real sign-ins now.
- `SUPABASE_JWT_SECRET` is no longer required for real traffic against this project (its legacy key is retired), but is still read if present -- e.g. for tests, or a different Supabase project that hasn't migrated to asymmetric keys.
- `backend/tests/unit/test_jwt.py` covers both branches: the existing HS256 tests unchanged, plus new ES256 tests that generate a throwaway EC keypair and stub `PyJWKClient` so no real network call happens in the test suite.

## Review

Confirmed Final as of Sprint 4 against the real `nbnmlfsxtiivvvoxuhdr` project. Revisit only if the project's signing method changes again (e.g. a full rotation away from HS256 entirely, at which point the HS256 branch could be removed).
