# ADR 0008: Qualification & Team Match Result Storage

**Status:** Accepted.

## Context

Sprint 7 (`docs/Revnara_Sprint_Development_Plan.md` DB7.1) needs somewhere to persist the output of `qualification.py`'s scoring and `team_matching.py`'s matching, and asks explicitly to decide between two shapes:

1. Dedicated `qualification_results`/`team_match_results` tables, one row per opportunity.
2. Denormalized JSONB columns directly on `opportunities`.

This decision also has to work with BE7.6's override capture: a human can correct a qualification score or team selection, and that correction must be recorded as a structured `override_records` row (original value, new value, reason, actor) rather than a silent field overwrite -- see DB7.3 and `app/opportunities/override.py`.

## Decision

Dedicated tables: `qualification_results` and `team_match_results`, each with a unique constraint on `opportunity_id` (one current result per opportunity, replaced -- not appended -- on re-run, mirroring how `Client.research_brief` is a single current value rather than a history). Both follow the same `TenantScopedColumns` shape as every other business table in this codebase, rather than an ad hoc JSONB blob on `Opportunity`.

Reasons:

- **Consistency with the rest of the schema.** Every other structured result in this codebase (portfolio items, case studies, knowledge chunks) is its own table, not a JSONB column bolted onto an unrelated parent row. Following that pattern means one RLS file per table (`supabase/rls/qualification_results.sql`, `team_match_results.sql`) using the exact same tenant-isolation template as everything else, instead of a special case.
- **`override_records` needs something to point at.** An override row references `entity_type` + `entity_id` + `field` (DB7.3) -- with a dedicated `qualification_results` row, `entity_id` is that row's own id and `field` is e.g. `"score"`. With a JSONB column on `opportunities`, the "entity" would have to be the opportunity itself with a JSON-path-shaped field name, which is harder to query and audit.
- **Independent RLS/read-permission shaping.** `explainability_records` (DB7.2) is deliberately generic and reusable for every future "why" decision across the whole plan (pricing, approvals, rejections), not just qualification/team-match. Giving qualification/team-match results their own tables keeps that same generic-reuse option open for them too, rather than coupling their shape to `Opportunity`'s.
- **Cost:** an extra join to read a qualification alongside its opportunity. Judged worth it -- every other read in this codebase already joins for related data (e.g. `Opportunity.client`), and a fresh qualification/match-team result is fetched at most once per opportunity-detail-screen view, not in a hot loop.

## Consequences

- `backend/migrations/versions/<rev>_qualification_matching.py` creates four tables in one migration: `qualification_results`, `team_match_results`, `explainability_records`, `override_records` -- all with RLS in the same PR (per `docs/Revnara_Sprint_Development_Plan.md` §2.2).
- Re-running `POST /opportunities/{id}/qualify` (or `/match-team`) replaces the tenant's current row for that opportunity via upsert, not an insert -- there is no history of past qualification runs, only the current one plus whatever `override_records` capture about corrections to it. If a future sprint needs "show me every qualification this opportunity ever had," that's a new decision, not assumed here.
- `override_records.field` values are the plain result-table column name (e.g. `"score"`, `"selected_team_member_ids"`), not a JSON path -- kept simple because these are dedicated columns, not JSONB internals.

## Review

Revisit if a future sprint needs qualification/team-match history rather than "current result only" -- that would likely mean adding a `superseded_at`/versioning scheme to these tables rather than changing this ADR's core table-vs-JSONB decision.
