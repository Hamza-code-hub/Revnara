# Revnara Enforcement Spec

**Source document:** `BDOS_Enterprise_Architecture_Blueprint_v2_Validated.md`  
**Created:** 2026-07-10  
**Purpose:** Convert the blueprint's governance principles into enforceable product and engineering rules.

---

# Core Rule

No external action may execute unless all of the following are true:

1. The tenant is resolved and active.
2. The actor is authenticated.
3. The actor or agent has permission for the action.
4. The platform capability exists and is active.
5. The connector mode matches the capability.
6. The policy engine allows the action.
7. The risk engine classifies the action within allowed limits.
8. Required approval exists and is still valid.
9. Approval is bound to the exact payload and context.
10. Credentials are injected only into the connector worker.
11. Idempotency protection is present.
12. Audit recording succeeds or the action fails closed.

---

# Canonical Capability Status

Use these exact values:

```text
available_automatic
available_with_approval
available_human_native_only
available_read_only
partner_contract_required
review_required
temporarily_suspended
unsupported
revoked
```

Do not use aliases such as `human_native_only`. If product copy needs simpler labels, map them at the UI layer.

---

# Connector Modes

```text
official_api
native_organizational_delegation
companion_drafting
approved_browser_assistance
unsupported
```

For Upwork and LinkedIn, `approved_browser_assistance` must remain disabled unless written partner permission names the exact browser integration and permitted behavior.

---

# PlatformCapability Minimum Schema

```yaml
platform_capability:
  id: string
  tenant_id: string
  platform: string
  capability: string
  status: enum
  connector_mode: enum

  authority:
    source_type: public_policy | contract | partner_approval | internal_policy
    evidence_ids: [string]
    written_partner_approval_id: string | null
    legal_review_id: string | null

  technical:
    official_endpoint: string | null
    required_scopes: [string]
    supported_connector_version: string | null
    supports_idempotency: boolean
    supports_reconciliation: boolean

  risk:
    default_tier: R0 | R1 | R2 | R3 | R4 | R5 | R6
    terms_violation: low | medium | high
    account_restriction: low | medium | high
    reputation: low | medium | high
    data_loss: low | medium | high

  review:
    reviewed_by: string
    reviewed_at: datetime
    expires_at: datetime
    next_review_reason: string

  fallback:
    mode: string
    notify_role: string

  enforcement:
    kill_switch_key: string
    audit_required: true
    approval_required: boolean
    payload_hash_required: boolean
```

---

# Action Risk Tiers

| Tier | Description | Default execution |
|---|---|---|
| R0 | Internal read/search within tenant. | Automatic. |
| R1 | Public research with no external account action. | Automatic with source logging. |
| R2 | Drafting or internal recommendation. | Automatic with validation. |
| R3 | Low-risk approved channel update, such as CRM note or draft email. | Constrained; approval may be policy-dependent. |
| R4 | Commercial external action, such as sending a proposal or follow-up. | Approval or human-native. |
| R5 | Price, scope, margin, team, or legal exception. | Human approval required. |
| R6 | Contract/legal acceptance, account appeal, payment, or binding authority. | Authorized human only. |

Risk can only increase during evaluation. It cannot be downgraded by an agent.

---

# Approval Binding

Approval must bind to:

- Tenant ID.
- Workspace ID.
- Requesting user or agent.
- Target platform and capability.
- Connector mode.
- Recipient/client/opportunity.
- Exact action type.
- Exact payload hash.
- Policy version.
- PlatformCapability version.
- Risk assessment version.
- Price, margin, discount, and scope if commercial.
- Expiration timestamp.
- Approver identity.

Execution must fail if any bound value changes after approval.

---

# Enforcement Pipeline

```text
Request received
→ Resolve tenant
→ Authenticate actor
→ Authorize actor/agent
→ Validate tool schema
→ Load PlatformCapability
→ Check capability status
→ Check connector mode
→ Check policy
→ Classify risk
→ Check approval requirement
→ Verify approval binding
→ Reserve idempotency key
→ Retrieve credential through broker
→ Execute connector action
→ Validate external response
→ Write audit event
→ Publish domain event
→ Reconcile external state if required
```

If any step fails, the action is blocked, an audit event is written, and a review item is created where appropriate.

---

# Human-Native Enforcement

For `available_human_native_only`:

- Agents may prepare drafts, summaries, checklists, and evidence packages.
- Agents may not navigate the restricted platform.
- Agents may not fill fields inside the restricted platform.
- Agents may not click submit/send/connect/accept.
- Agents may not use browser sessions, cookies, or exported tokens.
- The human must perform the native action in the platform UI.
- Revnara may record the outcome by manual entry or approved official API only.

Outcome sync must not use scraping, page polling, session-token reuse, or unofficial browser automation.

---

# Restricted Platform Defaults

## Upwork

| Capability | Default status | Notes |
|---|---|---|
| Proposal drafting | available_automatic | Internal drafting only. |
| Proposal submission | available_human_native_only | No automation without written approval and exact endpoint/scope. |
| Client message drafting | available_automatic | Internal drafting only. |
| Client message sending | available_human_native_only | Unless official API approval explicitly permits the exact behavior. |
| Offer/contract acceptance | available_human_native_only | Authorized human only. |
| Browser automation | unsupported | Unless written partner approval names exact browser behavior. |

## LinkedIn

| Capability | Default status | Notes |
|---|---|---|
| Sign in with LinkedIn | available_read_only | Only for approved OAuth scopes. |
| Company page operations | partner_contract_required | Depends on granted product/scope. |
| Marketing/ads APIs | partner_contract_required | Requires approved program/scope. |
| Personal member scraping | unsupported | Disabled. |
| Automated profile browsing | unsupported | Disabled. |
| Automated connection requests | unsupported | Disabled. |
| Automated personal messages | unsupported | Disabled. |
| Companion drafting | available_automatic | Draft outside LinkedIn only. |
| Browser automation | unsupported | Unless written partner approval names exact browser behavior. |

---

# Policy Engine Requirements

Every policy must have:

- Stable policy ID.
- Version.
- Owner.
- Effective date.
- Review date.
- Input schema.
- Decision output schema.
- Test cases.
- Failure behavior.
- Audit fields.

Policy decisions must return:

```yaml
decision: allow | deny | require_approval | require_human_native | require_review
policy_id: string
policy_version: string
reasons: [string]
blocking_reasons: [string]
required_approvals: [string]
```

---

# Audit Event Minimum Schema

```yaml
audit_event:
  id: string
  tenant_id: string
  workspace_id: string
  actor_type: user | agent | service
  actor_id: string
  agent_run_id: string | null
  workflow_id: string | null
  action_type: string
  platform: string | null
  capability_id: string | null
  connector_mode: string | null
  policy_decisions: [object]
  risk_assessment_id: string
  approval_id: string | null
  payload_hash: string | null
  idempotency_key: string | null
  external_result_id: string | null
  outcome: allowed | blocked | executed | failed | review_required
  error_code: string | null
  created_at: datetime
```

Audit writes are mandatory for all external actions and all blocked attempts.

---

# Kill Switches

Kill switches must exist at these levels:

- Global autonomous actions.
- Tenant.
- Platform.
- Connector.
- Capability.
- Agent.
- Tool.
- Model.
- External communication.
- Credential grant.

Kill-switch state is evaluated before capability status and again immediately before connector execution.

---

# Test Requirements

Before production:

1. Expired capability becomes `review_required`.
2. Revoked capability blocks execution.
3. Unsupported capability cannot be requested by any agent.
4. Approval fails when payload hash changes.
5. Approval fails when policy version changes after approval.
6. Human-native capability cannot execute through API connector.
7. Upwork and LinkedIn browser automation tools are absent or disabled.
8. Credential broker never returns raw secrets to agents.
9. Audit write failure blocks external action.
10. Idempotency prevents duplicate external action after retry.
11. Tenant isolation blocks cross-tenant retrieval, queue consumption, cache reads, object access, and vector search.
12. Kill switch blocks in-flight action before connector execution.

