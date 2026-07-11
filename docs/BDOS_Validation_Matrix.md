# Revnara Validation Matrix

**Source document:** `BDOS_Enterprise_Architecture_Blueprint_v2_Validated.md`  
**Created:** 2026-07-10  
**Purpose:** Convert the architecture blueprint into a tracked validation register before implementation.

---

# Status Legend

| Status | Meaning |
|---|---|
| Validated | Evidence is available, current, and specific enough to support implementation. |
| Partially validated | Direction is credible, but scope, limits, or evidence must be narrowed. |
| Pending legal | Requires legal interpretation or contractual review before use. |
| Pending technical | Requires API, connector, architecture, or security proof. |
| Pending customer validation | Requires customer interviews, pilots, or willingness testing. |
| Assumption | Useful planning assumption, not yet evidence-backed. |
| Blocked | Cannot proceed until an external dependency changes. |

---

# Executive Validation Summary

| Area | Current status | Decision before build |
|---|---|---|
| Product category | Partially validated | Validate that software houses will accept a governed BD copilot before promising replacement. |
| Upwork automation | Pending legal + technical | Treat proposal submission and restricted actions as human-native unless written approval and exact API scope exist. |
| LinkedIn outreach | Pending legal + technical | Treat personal member outreach, scraping, and browser automation as unsupported. |
| Email automation | Pending technical | Select first provider and define send-rate, consent, and approval policy. |
| CRM integration | Pending customer validation | Pick one first CRM based on target customer usage. |
| Calendar integration | Pending technical | Limit MVP to scheduling support after consent. |
| Tenant isolation | Pending technical | Choose shared logical isolation vs dedicated tenant option for MVP. |
| Company Brain / RAG | Pending technical | Prove tenant-filtered retrieval, deletion propagation, and evidence citation. |
| Proposal quality | Pending customer validation | Benchmark against historical proposals and human BD output. |
| Pricing engine | Assumption | Define deterministic pricing inputs, margin rules, and approval thresholds. |
| Risk engine | Pending technical | Define thresholds, action tiers, damage budgets, and override rules. |
| Approval engine | Pending technical | Bind approvals to immutable payload hashes and policy/capability versions. |
| Compliance roadmap | Assumption | Sequence SOC 2/ISO readiness after product-market and control maturity. |
| MVP scope | Partially validated | Cut MVP to a smaller copilot release with one email provider and one CRM. |

---

# Platform Validation

| ID | Topic | Blueprint claim | Evidence required | Status | Owner | Exit criteria |
|---|---|---|---|---|---|---|
| PV-001 | Upwork commercial API | Commercial API may be enabled with partner approval and exact scopes. | Upwork API approval, terms review, approved use-case record, endpoint/scope list. | Pending legal + technical | Legal + Platform Eng | Written approval and capability map exist for each action. |
| PV-002 | Upwork proposal submission | Do not assume automated proposal submission. | API docs review and Upwork written permission if any automation is planned. | Partially validated | Legal + Product | Default remains human-native; automated path disabled without explicit evidence. |
| PV-003 | Upwork browser tools | Browser assistance only where expressly allowed. | Written platform permission naming exact behavior. | Pending legal | Legal | Upwork browser automation remains disabled unless specific written approval exists. |
| PV-004 | LinkedIn personal outreach | Automated personal messages and connection requests are unsupported. | LinkedIn policy review and API partner program review. | Partially validated | Legal + Platform Eng | Personal outreach is companion drafting only. |
| PV-005 | LinkedIn company/API use | Company-page, marketing, ads, lead sync, or Sales Navigator APIs may be possible with approvals. | LinkedIn product approval, permission grant, partner status. | Pending technical | Platform Eng | Each LinkedIn capability has its own PlatformCapability record. |
| PV-006 | External-state sync | Outcomes may be synced only through approved API/webhook/manual entry. | Connector capability manifest and policy evidence. | Pending technical | Platform Eng | No page scraping/session-token sync is used. |

---

# Architecture Validation

| ID | Topic | Risk | Validation method | Status | Exit criteria |
|---|---|---|---|---|---|
| AV-001 | Tenant isolation | Cross-tenant data exposure. | RLS tests, repository tests, cache/queue/object/vector negative tests, support-access audit tests. | Pending technical | All isolation tests pass in CI and staging. |
| AV-002 | Vector/RAG isolation | Retrieval leakage across tenants or classifications. | Tenant-filtered vector queries, metadata enforcement, deletion propagation tests. | Pending technical | No retrieval result can bypass tenant, role, classification, or external-use filters. |
| AV-003 | Credential broker | Secrets enter model context or logs. | Secret redaction tests, connector process boundary tests, audit sampling. | Pending technical | Tokens are injected only into connector workers and never returned to agents. |
| AV-004 | Approval binding | Approved content changes before execution. | Payload hash, approval expiry, policy version, capability version, recipient binding. | Pending technical | Execution fails if any bound attribute changes. |
| AV-005 | Workflow durability | Lost, duplicated, or retried external actions. | Worker crash tests, idempotency-key tests, transactional outbox tests. | Pending technical | External actions are exactly-once by business key or safely deduplicated. |
| AV-006 | Audit completeness | Missing evidence during disputes. | Audit schema review and sampling. | Pending technical | 100% of external actions have tenant, actor, policy, capability, approval, payload hash, and result. |
| AV-007 | Disaster recovery | RPO/RTO targets are aspirational. | Restore test and cost model. | Pending technical | Targets are tier-specific and proven by restore drill. |

---

# Product And Market Validation

| ID | Topic | Question | Method | Status | Exit criteria |
|---|---|---|---|---|---|
| MV-001 | Human-native acceptance | Will customers tolerate native submission for Upwork/LinkedIn? | 10-15 customer interviews and 2 pilots. | Pending customer validation | At least 60% of target customers accept this workflow for MVP. |
| MV-002 | Proposal quality | Does Revnara improve output quality or speed? | Historical replay against won/lost proposals. | Pending customer validation | Better or equal human rating, faster draft cycle, zero unsupported claims. |
| MV-003 | Channel priority | Which channels matter first? | Customer interviews and CRM/email usage survey. | Pending customer validation | First CRM and email provider are selected by usage. |
| MV-004 | Pricing willingness | What packaging is acceptable? | Pricing interviews and pilot LOIs. | Pending customer validation | Paid pilot terms are validated before broad buildout. |
| MV-005 | BD replacement framing | Is "replacement" commercially attractive or threatening? | Buyer interviews. | Assumption | Positioning adjusted to match buyer language. |

---

# Required Decisions Before Phase 1 Build

1. Select first email provider: Gmail or Microsoft Graph.
2. Select first CRM: HubSpot, Salesforce, Pipedrive, Zoho, or custom import.
3. Choose MVP tenant isolation model.
4. Define approval payload binding rules.
5. Define action risk thresholds and damage budgets.
6. Define proposal quality benchmark set.
7. Define legal/policy evidence review owner.
8. Freeze MVP scope and defer non-MVP capabilities.

