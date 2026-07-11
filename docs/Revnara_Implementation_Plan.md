# Revnara Implementation Plan

**Product name:** Revnara  
**Tagline:** Governed AI for software-house business development.  
**Stack decision:** Flutter + Python FastAPI + Supabase + Google Cloud Run  
**Created:** 2026-07-10  

---

# 1. Final Stack Decision

Use this as the official Revnara implementation stack:

| Area | Technology |
|---|---|
| Desktop/Web/Mobile app | Flutter + Dart |
| Flutter state | Riverpod |
| Flutter navigation | GoRouter |
| Flutter API client | Dio |
| Local app cache | Drift + SQLite |
| Secure local storage | Platform secure storage plugin |
| Backend API | Python + FastAPI |
| Backend validation | Pydantic 2 |
| Database access | SQLAlchemy 2 + asyncpg |
| Migrations | Alembic |
| AI/agents | Custom Python runtime using official model SDKs |
| Primary database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| Enterprise SSO | Supabase SAML SSO later |
| File storage | Supabase Storage |
| Realtime | Supabase Realtime |
| Vector search | pgvector in Supabase PostgreSQL |
| Background queues | Supabase Queues |
| Scheduled jobs | Supabase Cron |
| API deployment | Google Cloud Run |
| Worker deployment | Google Cloud Run |
| Containers | Docker |
| CI/CD | GitHub Actions |
| Monitoring | Sentry + Google Cloud Logging + Supabase logs |

This stack is good for Revnara because it keeps the product to two application languages:

```text
Dart   -> user experience
Python -> backend, AI, policies, workers, integrations
```

And two main managed platforms:

```text
Supabase        -> data, auth, storage, realtime, queues, cron
Google Cloud Run -> Python execution
```

---

# 2. Architectural Rule

The system boundary is:

```text
Flutter owns presentation.
Python owns business authority and AI execution.
PostgreSQL owns authoritative data.
Supabase owns managed data infrastructure.
Cloud Run owns scalable Python runtime.
```

Do not let Flutter directly execute sensitive operations.

---

# 3. High-Level Architecture

```text
┌───────────────────────────────────────────────┐
│                Revnara App                    │
│ Flutter: Web | Windows | macOS | Linux | iOS  │
│ UI | Local Cache | Notifications | File Picker│
└──────────────────────┬────────────────────────┘
                       │ Supabase Auth JWT
                       ▼
┌───────────────────────────────────────────────┐
│              Python FastAPI API               │
│ AuthZ | Tenancy | Policy | Risk | Pricing     │
│ Approvals | Audit | Agent Commands            │
└──────────────┬────────────────┬───────────────┘
               │                │
               ▼                ▼
┌──────────────────────┐  ┌────────────────────┐
│ Python AI Workers    │  │ Connector Workers  │
│ RAG | Proposals      │  │ Email | CRM        │
│ Research | Evals     │  │ Calendar | Sync    │
└──────────────┬───────┘  └──────────┬─────────┘
               │                     │
               └─────────┬───────────┘
                         ▼
┌───────────────────────────────────────────────┐
│                  Supabase                     │
│ PostgreSQL | Auth | Storage | Realtime        │
│ pgvector | Queues | Cron | RLS                │
└───────────────────────────────────────────────┘
```

---

# 4. Access Model

## Flutter May Directly Use Supabase For

- Authentication.
- User session.
- Realtime subscriptions.
- Personal notification state.
- User preferences.
- Safe signed upload/download flows.
- Low-risk read-only dashboard views if RLS is strict.

## Flutter Must Call Python For

- Opportunity scoring.
- Proposal generation.
- Pricing.
- Discounts.
- Approvals.
- Team commitments.
- Contract operations.
- Agent execution.
- External email sending.
- CRM updates.
- OAuth token use.
- Platform connectors.
- Administrative operations.
- Tenant-wide reporting.
- Audit exports.
- Data deletion/export.

Correct flow:

```text
Flutter
-> FastAPI
-> Authenticate user JWT
-> Resolve tenant/workspace
-> Authorize action
-> Validate policy
-> Classify risk
-> Execute business operation
-> Write audit event
-> Store authoritative state in Supabase PostgreSQL
```

---

# 5. Security Invariants

These are non-negotiable:

1. No Supabase service-role key in Flutter.
2. No model provider keys in Flutter.
3. No external OAuth refresh tokens in Flutter.
4. No pricing, approval, or policy authority in Flutter.
5. Every business table has `tenant_id`.
6. Sensitive operations pass through Python.
7. PostgreSQL RLS is enabled on exposed tables.
8. Python queries are tenant-aware.
9. Every external action creates an audit event.
10. Every AI-generated claim must be evidence-backed or marked as an assumption.
11. Restricted platforms remain human-native unless written partner approval exists.
12. Queue messages contain references, not full documents or secrets.

---

# 6. Repository Structure

```text
revnara/
├── desktop/
│   ├── lib/
│   │   ├── app/
│   │   ├── features/
│   │   │   ├── command_center/
│   │   │   ├── opportunities/
│   │   │   ├── proposals/
│   │   │   ├── approvals/
│   │   │   ├── company_brain/
│   │   │   ├── integrations/
│   │   │   └── settings/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── storage/
│   │   └── shared/
│   └── test/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── tenancy/
│   │   ├── organizations/
│   │   ├── users/
│   │   ├── opportunities/
│   │   ├── clients/
│   │   ├── proposals/
│   │   ├── pricing/
│   │   ├── approvals/
│   │   ├── agents/
│   │   ├── model_gateway/
│   │   ├── rag/
│   │   ├── tools/
│   │   ├── integrations/
│   │   ├── platform_capabilities/
│   │   ├── policy_engine/
│   │   ├── risk_engine/
│   │   ├── audit/
│   │   └── notifications/
│   ├── workers/
│   │   ├── agent_worker/
│   │   ├── document_worker/
│   │   ├── embedding_worker/
│   │   ├── connector_worker/
│   │   └── notification_worker/
│   ├── migrations/
│   ├── tests/
│   └── evals/
│
├── supabase/
│   ├── migrations/
│   ├── rls/
│   ├── seeds/
│   └── config/
│
├── infrastructure/
│   ├── docker/
│   ├── cloud-run/
│   └── github-actions/
│
└── docs/
```

---

# 7. Core Domain Model

## MVP Tables

- organizations
- workspaces
- users
- organization_members
- roles
- permissions
- team_members
- skills
- portfolio_items
- case_studies
- clients
- contacts
- opportunities
- opportunity_sources
- proposals
- proposal_versions
- estimates
- pricing_decisions
- approvals
- platform_capabilities
- policy_evidence
- agent_runs
- tool_actions
- audit_events
- files
- notifications
- outcomes

## Common Columns

Every business table should include:

```sql
id uuid primary key
tenant_id uuid not null
workspace_id uuid
created_at timestamptz not null
updated_at timestamptz not null
created_by uuid
version integer not null default 1
classification text
retention_policy text
legal_hold boolean not null default false
```

---

# 8. MVP Product Scope

## Build In MVP

- Organization/workspace onboarding.
- User authentication through Supabase Auth.
- Role and permission model in Python.
- Company profile.
- Team and skill inventory.
- Portfolio and case-study library.
- Manual opportunity intake.
- Customer-provided Upwork link intake.
- Opportunity qualification.
- Team matching.
- Basic pricing rules.
- Proposal generation.
- Evidence citation.
- Approval workflow.
- Human-native Upwork submission package.
- LinkedIn companion drafting only.
- Audit trail.
- Basic notifications.
- Agent task queue.
- Supabase Storage private buckets.
- pgvector-backed company knowledge retrieval.

## Exclude From MVP

- Automated Upwork submission.
- Automated LinkedIn outreach.
- Browser automation.
- Contract signing.
- Autonomous legal decisions.
- Automatic policy modification.
- Multiple CRM integrations.
- Multiple email providers.
- Temporal.
- Kafka.
- Kubernetes.
- Redis.
- Dedicated vector database.

---

# 9. Implementation Phases

## Phase 0 - Stack Reset And Project Foundation

Goal: align the repository with the chosen stack.

Tasks:

- Keep Revnara as the product name.
- Move existing Markdown architecture docs into `docs/`.
- Remove or archive the temporary Node prototype.
- Create `backend/` Python FastAPI project.
- Create `desktop/` Flutter project.
- Create `supabase/` migration structure.
- Add `README.md` with the final stack.
- Add `.env.example` files.
- Add Dockerfile for backend.
- Add test/lint commands.

Exit criteria:

- `backend` starts locally.
- `desktop` starts locally.
- Empty health endpoint passes.
- CI skeleton exists.

## Phase 1 - Identity, Tenancy, And Authorization

Goal: establish the security foundation.

Tasks:

- Configure Supabase Auth.
- Create organizations, workspaces, members, roles, permissions.
- Implement FastAPI JWT verification.
- Implement tenant resolution.
- Implement authorization checks.
- Add RLS policies for core tables.
- Add tenant isolation tests.

Exit criteria:

- A user can sign in.
- A user can access only their tenant/workspace.
- Cross-tenant reads/writes fail in tests.

## Phase 2 - Company Brain Foundation

Goal: store the business memory Revnara needs.

Tasks:

- Company profile module.
- Team members and skills.
- Portfolio items and case studies.
- File upload through signed storage flow.
- Document parsing task queue.
- Embedding generation queue.
- pgvector retrieval with tenant and permission filters.

Exit criteria:

- Tenant-scoped portfolio search works.
- Uploaded files are private.
- Retrieval never crosses tenant boundaries.

## Phase 3 - Opportunity Pipeline

Goal: create the first BD workflow.

Tasks:

- Opportunity intake form.
- Opportunity source model.
- Safety screening state.
- Qualification scoring.
- Team matching.
- Opportunity status pipeline.
- Flutter opportunity list/detail screens.

Exit criteria:

- A user can create an opportunity.
- Revnara can score and explain it.
- Team match output is saved and auditable.

## Phase 4 - Proposal Generation And Verification

Goal: create evidence-grounded proposals.

Tasks:

- Proposal generation agent.
- Context builder.
- Model gateway wrapper.
- Prompt/version registry.
- Proposal versioning.
- Evidence citations.
- Claim verifier.
- Pricing check.
- Proposal editor in Flutter.

Exit criteria:

- Proposal drafts cite evidence.
- Unsupported claims are blocked or marked.
- Pricing violations block approval.

## Phase 5 - Approval And Human-Native Submission

Goal: keep commercial actions governed.

Tasks:

- Approval request model.
- Approval binding with payload hash.
- Approval inbox in Flutter.
- Human-native Upwork package.
- LinkedIn companion draft package.
- Submission confirmation workflow.
- Audit events for all approval decisions.

Exit criteria:

- Approval is invalidated if content changes.
- Human-native tasks cannot execute via connector.
- Submission package can be completed and recorded.

## Phase 6 - Integrations V1

Goal: add one email provider and one CRM.

Tasks:

- Choose first email provider: Gmail or Microsoft Graph.
- Choose first CRM: HubSpot recommended for MVP unless customer data says otherwise.
- OAuth connection model.
- Credential broker.
- Connector worker queue.
- Email/thread import.
- CRM opportunity sync.
- Connector health checks.

Exit criteria:

- Tokens never reach Flutter or model context.
- Connector actions are policy-checked and audited.
- Sync is idempotent.

## Phase 7 - Evaluation, Analytics, And Pilot Hardening

Goal: prepare for pilot customers.

Tasks:

- Historical proposal benchmark.
- Agent evaluation suite.
- Cost tracking.
- Basic dashboards.
- Sentry monitoring.
- Cloud Run deployment.
- Supabase staging/production separation.
- Backup and restore procedure.
- Deletion/export workflow.

Exit criteria:

- Pilot deployment is usable.
- Restore test is documented.
- Product has measurable quality and safety gates.

---

# 10. Backend API Modules

Initial FastAPI routes:

```text
GET  /health
GET  /me
POST /organizations
GET  /workspaces
POST /opportunities
GET  /opportunities
GET  /opportunities/{id}
POST /opportunities/{id}/qualify
POST /opportunities/{id}/match-team
POST /proposals
GET  /proposals/{id}
POST /proposals/{id}/generate
POST /proposals/{id}/verify
POST /approvals
POST /approvals/{id}/approve
POST /approvals/{id}/reject
GET  /audit-events
POST /files/signed-upload
POST /agent-tasks
```

---

# 11. Worker Queues

Use Supabase Queues:

```text
agent_tasks
document_tasks
embedding_tasks
connector_tasks
notification_tasks
evaluation_tasks
```

Message format:

```json
{
  "tenant_id": "tenant_123",
  "workspace_id": "workspace_123",
  "task_id": "task_999",
  "task_type": "generate_proposal",
  "resource_id": "proposal_782",
  "idempotency_key": "proposal_782:v3:generate"
}
```

Do not put full prompts, documents, secrets, or credentials in queue messages.

---

# 12. Flutter App Modules

Initial Flutter navigation:

```text
/login
/command-center
/opportunities
/opportunities/:id
/proposals/:id
/approvals
/company-brain
/integrations
/settings
```

Primary screens:

- Command Center.
- Opportunity Pipeline.
- Opportunity Detail.
- Proposal Editor.
- Approval Inbox.
- Company Brain.
- Team and Portfolio.
- Integrations.
- Audit Activity.

---

# 13. Testing Strategy

## Backend

- Unit tests for policy, risk, pricing, approvals.
- API tests for authorization and tenancy.
- RLS tests for cross-tenant denial.
- Worker tests for idempotency and retries.
- Agent tests for output schema and unsupported claims.

## Flutter

- Widget tests for core screens.
- Riverpod state tests.
- API client tests with mocked backend.
- Integration test for opportunity-to-proposal flow.

## Supabase

- Migration tests.
- RLS tests.
- Seed data tests.
- Vector retrieval permission tests.

---

# 14. Deployment Plan

## Environments

```text
local
staging
production
```

Each environment should have:

- Separate Supabase project.
- Separate Cloud Run services.
- Separate secrets.
- Separate model provider keys.
- Separate storage buckets.

## Cloud Run Services

```text
revnara-api
revnara-agent-worker
revnara-connector-worker
revnara-document-worker
revnara-notification-worker
```

All services can use the same Docker image with different startup commands.

---

# 15. Backup And Recovery

Minimum production requirements:

- Supabase PITR enabled.
- Daily external PostgreSQL dump.
- Supabase Storage object replication or export.
- Separate immutable audit export for critical events.
- Quarterly restore test.
- Documented RPO/RTO by customer tier.

Important warning:

Database backups do not automatically restore deleted storage objects. Storage needs its own backup/export plan.

---

# 16. First Two Sprints

## Sprint 1 - Foundation

Deliverables:

- Repository reset to `desktop/`, `backend/`, `supabase/`, `docs/`.
- FastAPI health endpoint.
- Supabase local/staging configuration.
- Alembic setup.
- Flutter app shell with login placeholder.
- Auth JWT verification design.
- First database migration for organizations/workspaces/users.
- Backend test runner.
- Flutter test runner.

## Sprint 2 - Tenancy And First Workflow

Deliverables:

- Supabase Auth integration.
- Organization/workspace membership model.
- Role and permission checks.
- RLS policies for core tables.
- Opportunity create/list/detail API.
- Flutter opportunity list/detail screens.
- Audit event writer.
- Cross-tenant negative tests.

---

# 17. Success Criteria For MVP

Revnara MVP is ready for pilot when:

1. A tenant can onboard company, team, and portfolio data.
2. A user can create or import an opportunity.
3. Revnara can qualify the opportunity with evidence and uncertainty.
4. Revnara can recommend a team and delivery risk.
5. Revnara can generate a proposal draft with citations.
6. Unsupported claims are blocked or marked.
7. Approval is required for commercial or risky actions.
8. Approval binds to exact payload and policy/capability versions.
9. Human-native Upwork workflow works without automation.
10. LinkedIn is draft-only.
11. Every sensitive action has an audit event.
12. Cross-tenant isolation tests pass.
13. Secrets never reach Flutter or model context.
14. Pilot deployment has monitoring, backup, and restore procedure.

---

# 18. Decision

The chosen stack is good for Revnara.

The product should move forward with:

```text
Flutter + Dart
Python + FastAPI
Supabase PostgreSQL/Auth/Storage/Realtime/pgvector/Queues/Cron
Google Cloud Run
Docker
GitHub Actions
```

This is the right balance for the current stage: serious enough for enterprise architecture, small enough to build and maintain.

