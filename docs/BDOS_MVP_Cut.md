# Revnara MVP Cut

**Source document:** `BDOS_Enterprise_Architecture_Blueprint_v2_Validated.md`  
**Created:** 2026-07-10  
**Purpose:** Reduce the enterprise blueprint into a buildable first release.

---

# MVP Thesis

The first release should prove that Revnara can help a software house evaluate opportunities, produce evidence-grounded proposals, route approvals, and support human-native submission without violating platform rules.

The MVP is not an autonomous BD department. It is a governed BD copilot with durable workflow, audit, and platform-safe handoff.

---

# MVP Outcome

Within one customer workspace, Revnara should:

1. Ingest company knowledge, team capability, portfolio evidence, and basic pricing rules.
2. Accept opportunities from manual entry, email, CRM, or imported Upwork links.
3. Qualify opportunities with evidence and uncertainty.
4. Recommend team fit and delivery risk.
5. Draft proposal packages with citations and approval state.
6. Route high-risk or commercial decisions to a human.
7. Support human-native Upwork submission and LinkedIn companion drafting.
8. Record outcomes and basic analytics.

---

# P0 Scope

These are required for the MVP.

| Capability | MVP behavior |
|---|---|
| Organization setup | One tenant/workspace model with users, roles, and approval hierarchy. |
| Company profile | Services, stacks, industries, project ranges, margin rules, restricted work. |
| Team model | Team members, skills, rates, availability, seniority, portfolio evidence. |
| Portfolio library | Case studies, approved claims, screenshots/links, confidentiality flags. |
| Opportunity intake | Manual form, CSV/import, email thread import, and customer-provided Upwork links. |
| Qualification | Score, reasons, evidence, missing info, recommendation. |
| Team matching | Skill fit, availability, estimated cost, delivery risk, gaps. |
| Proposal drafting | Evidence-grounded proposal package with assumptions, questions, price, timeline, citations. |
| Pricing rules | Deterministic margin and discount checks; no autonomous exceptions. |
| Approval workflow | Approve/reject/edit/delegate with immutable payload hash. |
| Human-native Upwork | Draft package, checklist, responsible human, manual submission confirmation. |
| LinkedIn companion drafting | Draft only; no member scraping, browsing, connection requests, or sends. |
| One email provider | Choose Gmail or Microsoft Graph, not both. |
| One CRM | Choose the most common CRM among pilot customers. |
| Audit | Agent runs, tool actions, approvals, policy checks, proposal versions. |
| Platform capability registry | Explicit capability status for each platform/action. |

---

# P1 After MVP

These should wait until P0 is proven.

| Capability | Reason to defer |
|---|---|
| Second email provider | Avoid duplicating connector work before workflow value is proven. |
| Second CRM | Same reason; connector expansion should follow customer demand. |
| Calendar scheduling | Useful, but less important than opportunity-to-proposal workflow. |
| Follow-up automation | Requires stronger consent, risk, and channel policy controls. |
| Advanced analytics | Needs real usage data first. |
| Outcome learning | Requires enough win/loss history to avoid false optimization. |
| Enterprise SSO/SCIM | Important for enterprise tier, not required for pilot validation. |
| Dedicated deployment | Enterprise packaging, not MVP proof. |

---

# Explicit Non-Goals

The MVP must not include:

- Automated Upwork proposal submission.
- Automated LinkedIn personal outreach.
- Browser automation for Upwork or LinkedIn.
- Session-cookie capture.
- Password collection.
- Contract signing.
- Autonomous legal decisions.
- Automatic policy changes.
- Multiple CRM/email/calendar integrations in the first release.
- Success-fee billing as the primary pricing model.

---

# MVP Workflow

```text
Configure company
→ Import portfolio/team/pricing rules
→ Create or import opportunity
→ Normalize opportunity
→ Safety screen
→ Research with permitted sources
→ Qualify
→ Match team
→ Estimate and price
→ Draft proposal
→ Verify claims and policy
→ Request approval if needed
→ Generate human-native submission package
→ Human submits outside Revnara where required
→ Human records result
→ Track outcome
```

---

# MVP Data Model Minimum

| Entity | Required in MVP |
|---|---|
| Organization | Yes |
| Workspace | Yes |
| User | Yes |
| Role/Permission | Yes |
| TeamMember | Yes |
| Skill | Yes |
| PortfolioItem/CaseStudy | Yes |
| Opportunity | Yes |
| Client/Contact | Basic |
| Proposal | Yes |
| Estimate | Basic |
| PricingDecision | Yes |
| Approval | Yes |
| PlatformCapability | Yes |
| PolicyEvidence | Basic |
| AgentRun | Yes |
| ToolAction | Yes |
| AuditEvent | Yes |
| Outcome | Basic |
| RestrictionIncident | Basic |
| DeletionRequest | Basic/manual workflow |

---

# MVP Quality Gates

The MVP cannot ship until:

1. Every external action is audited.
2. Every proposal claim has an evidence link or is marked as an assumption.
3. Pricing violations block submission package generation.
4. Approval is bound to payload hash, policy version, capability version, approver, and expiry.
5. Restricted-platform capabilities are disabled by default.
6. Upwork and LinkedIn browser automation is not present in the product.
7. No tenant isolation tests fail.
8. Secrets cannot enter model context or logs.
9. Workflow recovery after worker failure is tested.
10. Manual deletion/export process exists for pilot customers.

---

# MVP Success Metrics

| Metric | Target for pilot |
|---|---|
| Time from opportunity intake to first approved draft | 50% faster than current process. |
| Unsupported proposal claim rate | 0 known unsupported claims in approved packages. |
| Human correction rate | Tracked by section and reason; must trend down during pilot. |
| Proposal response rate | Baseline plus improvement or no degradation. |
| Approval turnaround time | Median under 24 hours for pilot teams. |
| Platform warning count | 0 caused by Revnara automation. |
| Cross-tenant isolation findings | 0 high/critical unresolved. |
| Customer willingness | At least 2 paid or signed pilot continuations. |

---

# Recommended Build Sequence

## Phase 0 - Validation And Design Freeze

- Legal review for Upwork and LinkedIn.
- Customer interviews.
- CRM/email provider selection.
- Tenant isolation decision.
- Proposal benchmark dataset.
- Risk and approval rule definitions.

## Phase 1 - Core Copilot

- Organization and company setup.
- Team, portfolio, and pricing data.
- Manual/imported opportunity intake.
- Qualification, team matching, proposal drafting.
- Evidence grounding and proposal verification.

## Phase 2 - Workflow And Governance

- Approval inbox.
- Platform capability registry.
- Audit events.
- Human-native Upwork package.
- LinkedIn companion drafting.

## Phase 3 - First Integrations

- One email provider.
- One CRM.
- Basic outcome tracking.
- Pilot analytics.

## Phase 4 - Pilot Hardening

- Isolation tests.
- Secret handling tests.
- Worker recovery tests.
- Deletion/export process.
- Evaluation report.

