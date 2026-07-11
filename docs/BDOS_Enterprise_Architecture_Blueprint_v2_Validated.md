# Revnara — Governed AI Business Development Platform
## Complete Enterprise Product, Architecture, Security, Platform-Compliance, Risk, and Delivery Blueprint

**Document version:** 2.0  
**Status:** Reviewed foundational architecture; implementation validation pending  
**Verification date:** 2026-07-10  
**Audience:** Founders, CEO, CTO, Product, Architecture, AI Engineering, Security, Legal, Compliance, Sales Operations, and Delivery Leadership  
**Product category:** Governed AI Business Development Platform for Software Houses  
**Product name:** Revnara

**Companion implementation artifacts:**

- `BDOS_Validation_Matrix.md`
- `BDOS_MVP_Cut.md`
- `BDOS_Enforcement_Spec.md`

---

# Document Purpose

This document defines a complete enterprise-grade architecture for an agentic AI platform intended to automate the operational responsibilities of a software-house Business Development department.

It incorporates:

- Product vision
- External account and channel integration
- Upwork and LinkedIn policy constraints
- Platform capability governance
- Multi-agent architecture
- Durable workflow orchestration
- Company knowledge and RAG
- Security and multi-tenant isolation
- Risk and liability controls
- Human approval and legal authority
- Reliability and disaster recovery
- Data privacy and deletion mechanics
- Explainability and auditability
- LLM cost governance
- Evaluation and continuous improvement
- SaaS pricing and commercial packaging
- Enterprise compliance roadmap
- Implementation phases
- MVP definition
- Acceptance criteria

This document intentionally avoids the unsafe assumption that every external platform can be automated merely because OAuth, an API, a browser extension, or customer consent exists.

---

# Table of Contents

1. Executive Summary  
2. Product Vision  
3. Product Positioning  
4. Core Business Objective  
5. What Full BD Replacement Means  
6. Enterprise Design Principles  
7. Realistic Reliability Standard  
8. Scope and Non-Scope  
9. Platform Dependency Is a First-Class Risk  
10. Platform Capability Governance Layer  
11. Platform Integration Modes  
12. Upwork Operating Model  
13. LinkedIn Operating Model  
14. Email, CRM, Calendar, and Approved Channels  
15. Unsupported Capability Policy  
16. External Account Connection Experience  
17. Identity, Account, Connection, Persona, and Authorization  
18. Credential Broker and Secret Management  
19. Platform Policy Evidence Vault  
20. Capability Review and Expiration  
21. Platform Restriction and Account Enforcement Response  
22. Customer Liability and Contractual Boundaries  
23. Complete Enterprise Architecture  
24. Control Plane and Data Plane Separation  
25. Multi-Tenant Architecture  
26. Organization Onboarding  
27. Company Brain  
28. Core Data Model  
29. Agent Architecture  
30. Agent Registry and Contracts  
31. Planner–Executor–Verifier Pattern  
32. Durable Workflow Engine  
33. Full Opportunity-to-Project Pipeline  
34. Lead Discovery  
35. Opportunity Normalization  
36. Safety Screening  
37. Client Research  
38. Qualification and Scoring  
39. Capability and Team Matching  
40. Pursuit Strategy  
41. Requirement Analysis  
42. Estimation  
43. Pricing and Profitability  
44. Proposal Generation  
45. Verification and Quality Gates  
46. Approval Engine  
47. Human-Native Submission  
48. Approved API Execution  
49. Communication Management  
50. Follow-Up Engine  
51. Meeting Intelligence  
52. Negotiation  
53. Contract and Closing  
54. Delivery Handover  
55. Outcome Learning  
56. Context Engineering  
57. RAG Architecture  
58. Tool Registry and Tool Discovery  
59. Connector Architecture  
60. Model Gateway  
61. Policy Engine  
62. Risk Engine  
63. Security Architecture  
64. Zero-Trust Architecture  
65. Prompt Injection and Agentic Threat Defense  
66. Privacy and Data Lifecycle  
67. GDPR/CCPA Deletion Mechanics  
68. External-State Reconciliation  
69. Explainability  
70. Human Audit Sampling  
71. Observability and Audit  
72. Reliability and Failure Containment  
73. Disaster Recovery and Business Continuity  
74. Sandbox and Staging Environments  
75. Notification and Approval UX  
76. LLM Cost Governance  
77. Evaluation Framework  
78. SaaS Pricing and Packaging  
79. Competitive Landscape Methodology  
80. Standards and Compliance Roadmap  
81. Deployment Architecture  
82. Codebase Structure  
83. Event and API Architecture  
84. Development Phases  
85. MVP Definition  
86. Quality Gates  
87. Architecture Decision Records  
88. Open Risks and Required Validation  
89. Final Architectural Doctrine  
90. Official Reference Sources

---

# 1. Executive Summary

Revnara is a secure, multi-tenant, enterprise agentic AI platform designed to automate and progressively transform Business Development operations for software houses.

The platform should:

- Discover relevant opportunities
- Research clients
- Qualify and prioritize leads
- Match requirements with company capabilities
- Select feasible teams
- Create pursuit strategies
- Estimate delivery
- Price projects
- Produce evidence-grounded proposals
- Draft communication
- Manage follow-up
- Prepare meetings
- Support negotiation
- Assist with contracts
- Coordinate closing
- Transfer won work to delivery
- Learn from outcomes

The product is not:

- A lead scraper
- A mass-messaging bot
- A generic proposal generator
- A browser automation wrapper
- A single autonomous agent with unrestricted tools
- A system that stores customers’ marketplace passwords
- A system that impersonates human platform users

The platform must operate according to a central rule:

> No external action exists as a product capability unless it is technically supported, contractually permitted, currently reviewed, and authorized for that exact tenant, account, scope, and use case.

For restricted channels such as Upwork and LinkedIn, Revnara should default to:

```text
AI researches and prepares
        ↓
Human reviews
        ↓
Human executes through the native platform
        ↓
Revnara records the outcome
```

Full autonomy is not a universal maturity stage. Some actions have a permanent human-native ceiling because external platform policy, legal authority, or reputational risk requires it.

---

# 2. Product Vision

> Build the enterprise operating system for software-house revenue acquisition: a governed network of AI agents that can discover, evaluate, pursue, and help close profitable software projects while respecting platform rules, company policy, delivery capacity, legal authority, and customer trust.

The company provides:

- Company identity
- Services
- Technology stacks
- Industry specialization
- Team members
- Skills and certifications
- Team availability
- Cost and billing rates
- Pricing rules
- Minimum profit margin
- Portfolio and case studies
- Disclosure permissions
- Previous proposals
- Won and lost project history
- Client conversations
- Follow-up history
- Contracts and templates
- Approval hierarchy
- Connected accounts
- Platform permissions
- Risk appetite

Revnara turns these assets into a continuously operating, policy-governed revenue system.

---

# 3. Product Positioning

A useful market description is:

> An autonomous revenue operations and business development intelligence platform for software houses.

A useful conceptual analogy is:

> A Claude Code or Codex-style operating environment for Business Development, but with stronger governance because it interacts with client communication, commercial terms, platform accounts, legal commitments, and company reputation.

The defensible value is not access to an LLM.

The defensible value is:

- Company-specific operational memory
- Platform capability governance
- Evidence-grounded proposal production
- Opportunity and profitability scoring
- Durable workflows
- Account-safe execution
- Policy enforcement
- Outcome learning
- Multi-channel orchestration
- Auditable autonomy
- Delivery feasibility validation

---

# 4. Core Business Objective

The product should optimize expected business value.

```text
Expected Business Value
=
Win Probability
× Expected Gross Profit
× Client Quality
× Delivery Feasibility
× Strategic Value
× Relationship Potential
− Acquisition Cost
− Delivery Risk
− Payment Risk
− Platform Risk
− Legal Risk
− Reputation Risk
```

The product should not optimize only for:

- Proposal count
- Message count
- Lead count
- Connection count
- Automated-action count

Primary outcome metrics:

- Qualified opportunity rate
- Proposal response rate
- Meeting conversion
- Win rate
- Gross margin
- Client lifetime value
- Delivery success
- Repeat project rate
- Time to qualified response
- Cost per won deal
- Platform-account health

---

# 5. What Full BD Replacement Means

Full BD replacement means covering the combined operational responsibilities of:

- Lead researcher
- Business Development Associate
- Business Development Executive
- Proposal writer
- Sales development representative
- Sales operations coordinator
- Account executive
- CRM administrator
- Follow-up coordinator
- Meeting coordinator
- Estimation coordinator
- Commercial analyst
- Handover coordinator
- Win/loss analyst

It does not mean eliminating all humans.

Humans remain necessary for:

- Legal authority
- Native submission on restricted platforms
- High-value relationship building
- Exceptional negotiation
- Policy creation
- Financial exceptions
- Contract signing
- Ethical oversight
- Platform appeals
- Strategic direction

The correct long-term model is:

```text
Humans define objectives, policies, authority, and exceptions.

Agents perform research, reasoning, preparation, coordination,
low-risk execution, monitoring, and optimization.
```

---

# 6. Enterprise Design Principles

## 6.1 Deterministic Control, Probabilistic Intelligence

Use deterministic systems for:

- Authentication
- Authorization
- Tenant isolation
- Pricing calculations
- Workflow state
- Approval rules
- Legal authority
- Rate limits
- Idempotency
- Audit
- Data retention
- Capability availability

Use AI for:

- Research
- Requirement understanding
- Strategy
- Drafting
- Summarization
- Objection analysis
- Recommendation
- Pattern discovery
- Scenario comparison

## 6.2 Fail Closed

When permission, platform policy, confidence, data, or approval is unclear:

```text
Do not execute.
Create a review item.
Preserve context.
Explain why execution stopped.
```

## 6.3 No Agent Self-Authorization

An agent cannot:

- Grant itself tools
- Modify its own permission
- Change its own risk tier
- Change platform capability status
- Change commercial policy
- Disable audit
- Access raw credentials
- approve its own high-risk action

## 6.4 Every Important Action Must Be

- Authorized
- Evidence-backed
- Schema-valid
- Policy-valid
- Risk-classified
- Auditable
- Idempotent where applicable
- Recoverable
- Attributable to a human or service identity
- Reversible where technically possible

## 6.5 Database as Source of Truth

LLM conversation memory is not authoritative.

Authoritative state lives in:

- Relational database
- Durable workflow store
- Approval records
- Event store
- Audit store
- External platform confirmations

---

# 7. Realistic Reliability Standard

The platform cannot honestly promise:

- 100% accuracy
- 100% uptime
- Zero hallucinations
- Zero restrictions
- Zero legal risk
- An unbreakable architecture
- Autonomous legal judgment

The correct target is:

> The system cannot fail silently, cannot exceed authority, cannot create unlimited damage, and can be stopped, inspected, recovered, and improved.

Reliability targets should be expressed as measurable service objectives:

- Availability SLO
- Workflow recovery rate
- Duplicate-action rate
- Policy violation rate
- Unsupported-claim rate
- Mean time to detect
- Mean time to recover
- Audit coverage
- Cross-tenant isolation test pass rate

---

# 8. Scope and Non-Scope

## In Scope

- Company onboarding
- Team and portfolio ingestion
- Historical sales learning
- Lead ingestion
- Opportunity research
- Qualification
- Proposal preparation
- Pricing support
- Email and CRM integration
- Calendar integration
- Approval workflows
- Human-native restricted-platform support
- Low-risk approved API execution
- Audit and analytics
- Delivery handover

## Out of Scope by Default

- Password collection
- Session-cookie collection
- CAPTCHA bypass
- Unauthorized scraping
- Automated LinkedIn personal messaging
- Automated LinkedIn connection requests
- Automated Upwork proposal submission without explicit approval
- AI-created platform identity
- Account sharing
- Contract signing by an LLM
- Unlimited financial authority
- Automatic production policy modification

---

# 9. Platform Dependency Is a First-Class Risk

External platforms may change:

- Terms
- APIs
- Scopes
- Rate limits
- Partner requirements
- UI
- Enforcement behavior
- Pricing
- Account roles
- Geographic access
- Data retention

Therefore, external-platform access must not be hardcoded as a permanent product assumption.

Every platform is treated as an independent dependency with:

- Capability inventory
- Contract inventory
- Policy evidence
- Review date
- Expiration date
- Technical health
- Enforcement risk
- Fallback mode
- Customer impact
- Kill switch

---

# 10. Platform Capability Governance Layer

The Platform Capability Governance Layer decides what the product may actually do.

## PlatformCapability Entity

```yaml
platform_capability:
  id: cap_upwork_submit_proposal_tenant_44
  tenant_id: tenant_44
  platform: upwork
  capability: submit_proposal

  status: available_human_native_only
  connector_mode: companion_drafting

  authority:
    type: public_policy
    evidence_ids:
      - evidence_upwork_automation_policy
      - evidence_upwork_api_commercial_policy
    written_partner_approval_id: null

  technical:
    official_endpoint: null
    required_scopes: []
    supported_connector_version: null

  risk:
    terms_violation: high
    account_restriction: high
    reputation: high
    data_loss: medium

  review:
    reviewed_by: compliance_user_7
    reviewed_at: 2026-07-10
    expires_at: 2026-10-10
    next_review_reason: quarterly_review

  fallback:
    mode: generate_submission_package
    notify_role: upwork_business_manager
```

## Capability Statuses

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

## Mandatory Invariants

```text
PLATFORM-001
No connector executes a capability without an active PlatformCapability record.

PLATFORM-002
Customer consent does not override a platform's terms.

PLATFORM-003
Human approval does not legalize prohibited automation.

PLATFORM-004
A capability expires into review_required automatically.

PLATFORM-005
Written partner permission must be stored as evidence.

PLATFORM-006
A platform warning suspends relevant actions immediately.

IDENTITY-001
An AI agent cannot impersonate a human platform user.

CREDENTIAL-001
Personal marketplace passwords and browser session cookies are prohibited.
```

---

# 11. Platform Integration Modes

## Mode 1 — Officially Authorized API

Requirements:

- Official API
- Approved commercial use
- Exact granted scopes
- Tenant authorization
- Current policy review
- Official endpoint
- Contract or written permission where required

Examples may include:

- Gmail
- Microsoft Graph
- HubSpot
- Salesforce
- Google Calendar
- Slack
- Approved Upwork API scopes
- Approved LinkedIn partner products

## Mode 2 — Native Organizational Delegation

A real human receives a role through the external platform’s own organizational model.

```text
Customer organization
→ Invites real authorized person
→ Platform assigns native role
→ Human performs native action
→ Revnara provides intelligence and preparation
```

## Mode 3 — Companion Drafting

Revnara prepares content outside the restricted platform.

```text
AI researches
→ AI drafts
→ Human reviews
→ Human manually opens platform
→ Human manually executes
→ Revnara records outcome
```

This is the default for:

- Upwork proposal submission
- LinkedIn personal outreach
- LinkedIn connection requests
- Other restricted member interactions

## Mode 4 — Explicitly Approved Browser Assistance

Permitted only where the platform expressly allows the exact browser integration.

For Upwork and LinkedIn, this mode must remain disabled unless written partner permission names the exact browser integration and the exact permitted behavior.

Requirements:

- Written or published permission
- Narrow capability
- No scraping
- No session-token extraction
- No CAPTCHA bypass
- No autonomous navigation
- Human confirmation
- Audited extension version

## Mode 5 — Unsupported

```text
No approved API
+ No valid native delegation
+ No permitted browser integration
= Capability disabled
```

Unsupported is a valid product state.

---

# 12. Upwork Operating Model

## 12.1 Default Position

Upwork commercial API access is not assumed.

The Upwork connector starts as:

```yaml
upwork_default:
  opportunity_discovery: conditional
  read_account_data: conditional
  proposal_drafting: automatic_internal
  proposal_submission: available_human_native_only
  client_message_drafting: automatic_internal
  client_message_sending: available_human_native_only
  client_message_sending_api_exception: partner_contract_required
  offer_acceptance: human_authority_required
  contract_acceptance: human_authority_required
```

## 12.2 Commercial API Access

Commercial API capability may be enabled only when:

- The company is accepted as a selected commercial partner
- Prior written permission exists
- The approved use case matches the implemented behavior
- The API key is active
- The required scope is documented
- The endpoint is official
- The capability has not expired

## 12.3 Proposal Submission

Do not assume a public proposal-submission endpoint.

Default flow:

```text
Opportunity identified
→ Revnara qualifies
→ Revnara prepares proposal
→ Revnara prepares screening answers
→ Revnara prepares price and team recommendation
→ Human business manager opens Upwork
→ Human reviews all content
→ Human selects member and Connects
→ Human submits natively
→ Human or approved official API/webhook sync records outcome
```

## 12.4 Agency Delegation

A real human may receive Upwork agency permissions through Upwork’s native agency roles.

The system itself must not:

- Create a fictional AI agency member
- Share one platform login across customers
- Store the member’s password
- Operate through browser session cookies
- Pretend an AI is a verified person

## 12.5 Rate Limits

Rate limits do not create permission.

```yaml
submit_upwork_proposal:
  automated_permission: false
  automated_daily_limit: 0

draft_upwork_proposal:
  automated_permission: true
  tenant_configurable_limit: true
```

## 12.6 Upwork Enforcement Response

On warning, API disablement, or restriction:

- Suspend Upwork actions
- Stop active workflow leases
- Preserve evidence
- Notify customer owner
- Export recent action log
- Require compliance review
- Generate appeal-support package
- Do not auto-retry prohibited actions

---

# 13. LinkedIn Operating Model

## 13.1 Default Position

```yaml
linkedin_default:
  sign_in_with_linkedin: permitted_if_configured
  approved_company_page_operations: conditional
  approved_marketing_api_operations: conditional
  member_profile_scraping: unsupported
  automated_profile_browsing: unsupported
  automated_connection_requests: unsupported
  automated_personal_messages: unsupported
  browser_extension_automation: unsupported
  companion_drafting: permitted_internal
```

## 13.2 Personal Member Outreach

Safe default:

```text
Revnara prepares target rationale and draft
→ Human finds or selects recipient manually
→ Human reviews draft
→ Human manually enters or pastes content
→ Human clicks Send
```

Human final click alone is not enough when earlier steps were automated inside LinkedIn.

The system must not programmatically:

- Search members
- Open member profiles
- Extract profile data
- Add contacts
- Send invitations
- Fill and send personal messages
- Navigate results
- Modify LinkedIn pages through unapproved extensions

## 13.3 Approved LinkedIn APIs

Narrow approved products may exist for:

- OAuth sign-in
- Company-page administration
- Marketing
- Advertising
- Lead synchronization
- Recruiting partnerships
- Compliance partnerships

Each is a separate capability with separate scopes and approval.

Do not infer personal outreach rights from basic OAuth.

---

# 14. Email, CRM, Calendar, and Approved Channels

These channels are generally more suitable for governed API integration, subject to provider scopes and customer authorization.

## Email

- Gmail API
- Google Workspace
- Microsoft Graph
- Shared mailboxes

Capabilities:

- Read authorized threads
- Draft replies
- Send within policy
- Label
- Archive
- Detect responses
- Record correspondence

## CRM

- HubSpot
- Salesforce
- Pipedrive
- Zoho
- Custom CRM

Capabilities:

- Read contacts
- Create opportunity
- Update stage
- Log communication
- Store notes
- Create tasks

## Calendar

- Google Calendar
- Microsoft Calendar
- Calendly
- Cal.com

Capabilities:

- Read availability
- Propose times
- Create meeting after consent
- Update meeting
- Generate preparation brief

## Messaging

- Slack
- Microsoft Teams
- WhatsApp Business API where approved
- Approved SMS providers

---

# 15. Unsupported Capability Policy

When a capability is unsupported:

- UI shows why
- Agent cannot request its tool
- Workflow uses a fallback
- No hidden browser workaround exists
- Customer cannot enable it with a simple toggle
- Support staff cannot override it without compliance evidence

Example:

```text
LinkedIn personal message automation
Status: Unsupported
Reason: Platform policy
Fallback: Generate draft and notify assigned human
```

---

# 16. External Account Connection Experience

## Standard OAuth Flow

```text
User signs in to Revnara
→ Opens Accounts & Channels
→ Selects provider
→ Reviews requested capabilities
→ Redirects to provider
→ Authenticates at provider
→ Grants scopes
→ Provider redirects to Revnara
→ Credential Broker stores encrypted grant
→ Capability Engine evaluates actual scopes
→ Only verified capabilities become active
```

## Restricted Platform Flow

```text
User configures Upwork or LinkedIn workspace
→ Revnara explains human-native restrictions
→ User assigns responsible human
→ Optional approved data connection is established
→ Drafting and notification workflow is enabled
→ Submission automation remains disabled
```

---

# 17. Identity, Account, Connection, Persona, and Authorization

## External Account

The actual account at the provider.

## Connection

The technical grant:

- OAuth
- API key
- Service account
- Webhook
- Approved extension grant

## Operating Persona

The business identity represented:

- Company
- CEO
- Sales manager
- Agency owner
- Shared sales mailbox

## Human Actor

A real authenticated person with authority.

## Agent Authorization

The exact actions an agent may request.

```text
Human identity
≠ External account
≠ OAuth connection
≠ Operating persona
≠ Agent permission
```

---

# 18. Credential Broker and Secret Management

Credentials never enter model context.

```text
Agent requests:
send_email(connection_id, draft_id)

Tool Gateway:
- Validates agent
- Validates tenant
- Validates policy
- Validates approval
- Calls Connector Worker

Credential Broker:
- Retrieves short-lived token
- Injects it into connector process
- Never returns it to agent
```

Controls:

- Secrets vault
- Envelope encryption
- Per-tenant encryption context
- Key rotation
- Short-lived tokens
- Refresh-token rotation
- Scope minimization
- Revocation
- Reauthorization
- Access audit
- Secret redaction
- No credential logging
- No browser-cookie storage

---

# 19. Platform Policy Evidence Vault

Store:

- Public policy URL
- Retrieved copy or content hash
- Effective date
- Review date
- Legal interpretation
- Capability mapping
- Partner agreement
- API approval email
- Scope grant
- Expiration
- Reviewer
- Change history

Evidence record:

```yaml
policy_evidence:
  id: evidence_upwork_automation_policy
  platform: upwork
  source_type: official_public_policy
  source_url: https://support.upwork.com/...
  content_hash: sha256:...
  effective_date: unknown
  retrieved_at: 2026-07-10
  reviewed_by:
    - compliance_user_7
    - legal_user_2
  supports:
    - cap_upwork_automation_limit
```

---

# 20. Capability Review and Expiration

Review triggers:

- Quarterly review
- Terms change
- API version change
- Scope change
- Connector release
- Customer warning
- API key disablement
- New jurisdiction
- New automation behavior
- Security incident

Expired capabilities become:

```text
review_required
```

They do not remain active silently.

---

# 21. Platform Restriction and Account Enforcement Response

## Detection Sources

- API error
- Email alert
- Customer report
- Webhook
- Authentication failure
- Restriction page
- Partner notice

## Response Workflow

```text
Restriction detected
→ Suspend affected connector
→ Cancel active external action leases
→ Freeze retries
→ Preserve audit and evidence
→ Notify customer owner and Revnara compliance
→ Classify likely cause
→ Review recent actions
→ Produce incident report
→ Produce appeal-support package
→ Require authorized reactivation
```

## Evidence Package

- Timeline
- User identity
- Agent runs
- Tool actions
- Policies evaluated
- Approvals
- External responses
- Connector version
- IP and device metadata where lawful
- Relevant customer instructions
- Applicable platform policy

---

# 22. Customer Liability and Contractual Boundaries

Customer agreement should define:

- Customer owns and controls external accounts
- Revnara does not guarantee protection from false-positive restrictions
- Customer must not share passwords
- Customer must use true identity
- Customer must follow provider rules
- Restricted actions remain human-native
- Customer is responsible for native submission
- Revnara may suspend connectors for compliance
- Customer must report warnings
- Platform changes may remove features
- Liability caps
- Indemnification
- Cooperation in investigation
- Data preservation
- Appeal responsibility
- Insurance expectations

Company risk program should consider:

- Technology E&O
- Cyber insurance
- Professional liability
- Contractual review by jurisdiction
- Platform-specific legal opinion

---

# 23. Complete Enterprise Architecture

```text
┌───────────────────────────────────────────────────────────────┐
│ EXPERIENCE LAYER                                              │
│ Command Center | Pipeline | AI Workspace | Approval Inbox      │
│ Accounts | Company Brain | Analytics | Security | Admin        │
└───────────────────────────────┬───────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│ IDENTITY AND ACCESS                                            │
│ SSO | MFA | OIDC | SAML | SCIM | RBAC | ABAC | Sessions       │
└───────────────────────────────┬───────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│ API GATEWAY                                                    │
│ Tenant Resolution | WAF | Rate Limit | Validation | Routing    │
└───────────────────────────────┬───────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│ CONTROL PLANE                                                  │
│ Agent Registry | Tool Registry | Model Registry               │
│ Policy Engine | Risk Engine | Approval Engine                 │
│ Platform Capability Governance | Prompt Registry              │
│ Workflow Registry | Budget Manager | Feature Flags            │
│ Kill Switches | Tenant Configuration                          │
└───────────────────────────────┬───────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│ DURABLE WORKFLOW PLANE                                         │
│ Opportunity | Pursuit | Proposal | Communication              │
│ Meeting | Negotiation | Contract | Handover | Enforcement     │
│ Timers | Retry | Idempotency | Replay | Recovery              │
└───────────────────────────────┬───────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│ AGENT INTELLIGENCE PLANE                                       │
│ Orchestrator | Research | Qualification | Strategy            │
│ Estimation | Pricing | Proposal | Communication               │
│ Negotiation | Compliance | Verification | Learning            │
└──────────────┬───────────────────────────┬────────────────────┘
               │                           │
┌──────────────▼──────────────┐ ┌─────────▼────────────────────┐
│ CONTEXT AND KNOWLEDGE       │ │ ACTION AND CONNECTOR PLANE   │
│ Company Brain | RAG         │ │ Tool Gateway                 │
│ Evidence Graph | Memory     │ │ Credential Broker            │
│ Context Compression         │ │ Connector Workers            │
│ Permission-Aware Retrieval  │ │ Human-Native Handoff         │
└──────────────┬──────────────┘ └─────────┬────────────────────┘
               │                           │
┌──────────────▼───────────────────────────▼────────────────────┐
│ DATA PLANE                                                     │
│ PostgreSQL | Object Store | Search | Vector Index             │
│ Event Store | Audit Store | Analytics | Secrets Vault          │
└───────────────────────────────────────────────────────────────┘
```

---

# 24. Control Plane and Data Plane Separation

The control plane manages:

- Permissions
- Models
- Agents
- Tools
- Capabilities
- Policies
- Risk
- Budgets
- Releases
- Kill switches

The data plane processes:

- Opportunities
- Conversations
- Proposals
- Documents
- Client records
- Agent runs
- Tool actions

Agents cannot modify the control plane.

---

# 25. Multi-Tenant Architecture

## Isolation Controls

- Tenant ID on every domain record
- PostgreSQL row-level security
- Tenant-aware repositories
- Separate object prefixes
- Isolated vector namespaces
- Per-tenant encryption keys or key context
- Tenant-specific connector credentials
- Tenant budgets
- Tenant audit partitioning
- Tenant rate limits
- Cross-tenant negative tests
- Tenant-aware caches
- Tenant-aware queues

## Enterprise Deployment Options

- Shared SaaS with logical isolation
- Dedicated database
- Dedicated worker pool
- Dedicated VPC
- Private cloud
- On-premises

## Mandatory Test

```text
No user, agent, service, tool, retrieval query, export,
or support function may access another tenant's data
without an explicit audited administrative process.
```

---

# 26. Organization Onboarding

## Step 1 — Organization

- Legal entity
- Brand
- Country
- Regions
- Time zone
- Currency
- Data residency
- Workspaces
- Departments
- Users
- Roles
- Approval hierarchy

## Step 2 — Business Profile

- Services
- Stacks
- Industries
- Project ranges
- Minimum budget
- Margin rules
- Working hours
- Delivery models
- Restricted industries
- Prohibited services

## Step 3 — Team

- CV
- Skills
- Seniority
- Certifications
- Cost
- Billing rate
- Availability
- Time zone
- Language
- Portfolio evidence
- Active workload
- Backup role

## Step 4 — Portfolio

- Case studies
- Results
- Screenshots
- Demo
- Testimonials
- Technology
- Team
- Client permission
- Confidentiality

## Step 5 — History

- Proposals
- Wins
- Losses
- Conversations
- Follow-ups
- Prices
- Objections
- Profitability
- Delivery outcome

## Step 6 — Accounts

- Email
- CRM
- Calendar
- Website
- Approved platforms
- Restricted-platform human owners

## Step 7 — Policies

- Autonomy
- Approvals
- Pricing
- Legal
- Security
- Platform

## Step 8 — Simulation

- Historical replay
- Shadow mode
- Security testing
- Prompt-injection testing
- Cost testing
- Failure testing
- Human comparison

---

# 27. Company Brain

The Company Brain includes:

## Structured Knowledge

- Services
- Skills
- Rates
- Availability
- Certifications
- Policies
- Capacity

## Portfolio Knowledge

- Case studies
- Outcomes
- Approved claims
- Testimonials
- Technical evidence

## Sales Knowledge

- Previous proposals
- Objections
- Follow-ups
- Win/loss patterns

## Commercial Knowledge

- Pricing
- Margins
- Discounts
- Payment terms
- Contract templates

## Relationship Knowledge

- Client preferences
- Communication style
- History
- Decision-makers
- Reliability

## Operational Knowledge

- Active delivery
- Capacity
- Deadlines
- Resource conflicts

---

# 28. Core Data Model

```text
Organization
Workspace
Department
User
Role
Permission
TeamMember
Skill
Capability
PortfolioItem
CaseStudy
Client
Contact
Opportunity
OpportunitySource
Platform
PlatformCapability
PolicyEvidence
ChannelAccount
Connection
CredentialGrant
OperatingPersona
HumanActor
Conversation
Message
Meeting
Proposal
Estimate
PricingDecision
Approval
Contract
Deal
ProjectHandover
AgentDefinition
AgentRun
ToolDefinition
ToolAction
Evidence
RiskAssessment
AuditEvent
Outcome
Evaluation
RestrictionIncident
Notification
DeletionRequest
```

Common metadata:

```text
tenant_id
workspace_id
classification
data_region
created_by
created_at
updated_at
version
retention_policy
legal_hold
```

---

# 29. Agent Architecture

Recommended agents:

1. Revenue Orchestrator
2. Discovery Agent
3. Ingestion Agent
4. Research Agent
5. Qualification Agent
6. Scam Detection Agent
7. Capability Matching Agent
8. Team Selection Agent
9. Strategy Agent
10. Requirement Analyst
11. Estimation Agent
12. Pricing Agent
13. Proposal Agent
14. Factual Verifier
15. Compliance Verifier
16. Communication Agent
17. Follow-Up Agent
18. Meeting Preparation Agent
19. Meeting Intelligence Agent
20. Negotiation Agent
21. Contract Review Agent
22. Closing Coordinator
23. Handover Agent
24. Win/Loss Agent
25. Learning Agent
26. Platform Policy Agent
27. Enforcement Response Agent

Agents are specialized modules, not unrestricted independent employees.

---

# 30. Agent Registry and Contracts

```yaml
agent:
  id: proposal-agent
  version: 2.0.0
  owner: proposal-domain
  purpose: Produce evidence-grounded proposals

  inputs:
    - opportunity_id
    - client_id
    - strategy_id
    - estimate_id

  tools:
    allowed:
      - portfolio.search
      - evidence.read
      - team.match
      - pricing.read
      - proposal.save

    prohibited:
      - linkedin.send_message
      - upwork.submit_proposal
      - contract.sign
      - pricing.override
      - credential.read

  outputs:
    schema: ProposalDraftV2

  limits:
    max_tool_calls: 15
    max_runtime_seconds: 120
    max_tokens: 12000
    max_cost_usd: 1.50

  validations:
    - evidence_grounding
    - claim_validation
    - pricing_policy
    - confidentiality
    - platform_format

  escalation:
    confidence_below: 0.80
    missing_evidence: true
    pricing_exception: always
```

---

# 31. Planner–Executor–Verifier Pattern

```text
Planner
Determines required work, evidence, and constraints
        ↓
Executor
Uses approved tools and produces structured output
        ↓
Verifier
Checks evidence, policy, security, and completeness
        ↓
Workflow
Transitions state or requests correction/approval
```

For critical actions, planner and verifier should use:

- Separate prompts
- Independent context
- Deterministic checks
- Different model routes where beneficial
- Human approval

---

# 32. Durable Workflow Engine

Required capabilities:

- Persistent state
- Retry
- Backoff
- Timeout
- Idempotency
- Timers
- Pause/resume
- Human task
- Compensation
- Dead-letter queue
- Versioning
- Replay
- Recovery

Workflow state must not depend on a chat transcript.

---

# 33. Full Opportunity-to-Project Pipeline

```text
Discover
→ Normalize
→ Safety Screen
→ Research
→ Qualify
→ Match Capability
→ Match Team
→ Build Strategy
→ Analyze Requirements
→ Estimate
→ Price
→ Draft Proposal
→ Verify
→ Approve
→ Human-Native Submit or Approved API Execute
→ Monitor
→ Follow Up
→ Meet
→ Negotiate
→ Contract
→ Close
→ Handover
→ Learn
```

---

# 34. Lead Discovery

Sources:

- Email
- CRM
- Website forms
- Referrals
- Partners
- Public tender feeds
- Approved APIs
- Manual imports
- Customer-provided Upwork job links
- Human-selected LinkedIn prospects
- Existing client expansion signals

Each source declares:

- Authority
- Data rights
- Refresh method
- Rate limit
- Retention
- Reliability
- Restriction risk

---

# 35. Opportunity Normalization

Normalized fields:

```json
{
  "id": "opp_9277",
  "source": "upwork_human_import",
  "external_id": "job_9277",
  "title": "AI Cybersecurity Platform",
  "description": "...",
  "budget": {
    "minimum": 10000,
    "maximum": 20000,
    "currency": "USD"
  },
  "requirements": [],
  "attachments": [],
  "client_id": null,
  "source_confidence": 0.95,
  "discovered_at": "2026-07-10T09:30:00Z"
}
```

Processing:

- Deduplicate
- Detect repost
- Extract requirements
- Detect language
- Classify attachment
- Assign tenant
- Store source lineage

---

# 36. Safety Screening

Before model processing:

- Malware scan
- File-type validation
- URL reputation
- Prompt-injection scan
- PII classification
- Secret detection
- Scam signals
- Prohibited-industry classification
- Platform-policy validation

External content is untrusted data.

It cannot:

- Override system policy
- Grant tools
- Change pricing
- Request secrets
- Authorize external action

---

# 37. Client Research

Research may include legally and contractually permitted:

- Website
- Product
- Industry
- Region
- Public company facts
- Public funding
- CRM history
- Marketplace history if authorized
- Payment reliability if available
- Previous engagement
- Communication patterns

Every fact stores:

- Source
- Retrieval time
- Confidence
- Permission
- Visibility
- Expiration

---

# 38. Qualification and Scoring

Example dimensions:

```text
Strategic Fit             15%
Technical Fit             20%
Budget Fit                15%
Client Quality            10%
Win Probability           10%
Profitability             10%
Delivery Feasibility      10%
Payment Risk               5%
Platform Risk              3%
Long-Term Potential        2%
```

Output:

- Score
- Reasons
- Evidence
- Uncertainty
- Missing information
- Recommendation

Possible decisions:

- Reject
- Need information
- Qualified
- High priority
- Strategic pursuit

---

# 39. Capability and Team Matching

Checks:

- Required skills
- Industry experience
- Compliance
- Seniority
- Availability
- Cost
- Time zone
- Language
- Workload
- Deadline
- Backup resources

Output:

```text
recommended_team
backup_team
skill_gaps
capacity_status
estimated_cost
delivery_risk
```

No proposal may commit unavailable people.

---

# 40. Pursuit Strategy

The strategy agent defines:

- Client pain
- Value proposition
- Differentiation
- Case studies
- Team positioning
- Technical approach
- Questions
- Pricing model
- Risk-reduction approach
- Tone
- Call to action
- Competitor position
- Disclosure restrictions

---

# 41. Requirement Analysis

Produce:

- Functional requirements
- Non-functional requirements
- Integrations
- Security needs
- Compliance needs
- Unknowns
- Assumptions
- Dependencies
- Acceptance criteria
- Scope exclusions

---

# 42. Estimation

```text
Requirements
→ Work Breakdown Structure
→ Tasks
→ Dependencies
→ Role Hours
→ Confidence Range
→ Risk Reserve
→ Delivery Schedule
→ Internal Cost
```

AI decomposes.

Deterministic systems calculate.

---

# 43. Pricing and Profitability

Pricing engine includes:

- Labor
- Infrastructure
- Third-party services
- Platform fees
- Tax assumptions
- Currency risk
- Contingency
- Margin
- Discount
- Payment risk
- Acquisition cost

```text
Final Price
=
Direct Cost
+ Overhead Allocation
+ Risk Reserve
+ Target Profit
+ External Fees
```

Pricing output explains:

- Inputs
- Assumptions
- Margin
- Sensitivity
- Approval need

---

# 44. Proposal Generation

Inputs:

- Opportunity
- Research
- Strategy
- Estimate
- Price
- Team
- Portfolio
- Template
- Platform format
- Conversation

Outputs:

- Personalized opening
- Problem understanding
- Solution
- Approach
- Evidence
- Team fit
- Timeline
- Price
- Assumptions
- Questions
- Risks
- Next step
- Citations
- Confidence

---

# 45. Verification and Quality Gates

```text
Draft
→ Schema Check
→ Factual Check
→ Evidence Check
→ Portfolio Claim Check
→ Technical Review
→ Pricing Review
→ Legal Language Review
→ Confidentiality Review
→ Platform Policy Review
→ Quality Score
```

Blocking failures:

- Invented experience
- Unsupported claim
- Confidential disclosure
- Unavailable team
- Margin violation
- Unauthorized guarantee
- Prohibited platform action
- Missing approval

---

# 46. Approval Engine

Approval dimensions:

- Value
- Confidence
- Discount
- Margin
- Client risk
- Legal exposure
- Team commitment
- Reputation
- Platform risk

Approvers:

- Sales manager
- Technical lead
- Finance
- Legal
- CEO
- Security
- Customer account owner

---

# 47. Human-Native Submission

For restricted platforms:

```text
Proposal package ready
→ Assigned human notified
→ Human opens native platform
→ Human reviews content
→ Human selects account/member
→ Human submits
→ Human confirms result
→ Revnara updates pipeline
```

Human-native tasks have:

- Owner
- Deadline
- Checklist
- Evidence
- Native link where platform policy permits
- Completion confirmation
- Audit record

---

# 48. Approved API Execution

```text
Agent tool request
→ Tool schema validation
→ Tenant authorization
→ Platform capability validation
→ Policy validation
→ Risk classification
→ Approval validation
→ Idempotency
→ Credential injection
→ API execution
→ Response validation
→ Audit
```

---

# 49. Communication Management

Incoming communication:

```text
Webhook/Poll
→ Normalize
→ Match client
→ Match opportunity
→ Classify intent
→ Classify urgency
→ Classify risk
→ Draft/Approve/Execute
```

Intents:

- Question
- Portfolio request
- Budget objection
- Technical question
- Meeting request
- Scope change
- Contract request
- Rejection
- Scam
- Sensitive request

---

# 50. Follow-Up Engine

Inputs:

- Last interaction
- Client activity
- Consent
- Channel
- Time zone
- Opportunity value
- Previous follow-ups
- Platform policy
- Value addition

Follow-up is not a fixed spam sequence.

It adapts to context and stops when:

- Opt-out
- Rejection
- Platform limit
- Risk signal
- Too many attempts
- Opportunity closed

---

# 51. Meeting Intelligence

Before:

- Client brief
- Stakeholders
- Questions
- Objections
- Pricing boundaries
- Agenda

During:

- Consent-aware recording
- Transcription
- Requirement extraction
- Commitment detection
- Objection detection
- Action items

After:

- Summary
- CRM update
- Scope update
- Re-estimate
- Follow-up
- Approval requests

---

# 52. Negotiation

```yaml
negotiation:
  preferred_price: 18000
  target_price: 16500
  minimum_price: 14500
  minimum_margin: 25
  maximum_discount: 8
  scope_reduction: allowed

  permitted_terms:
    - milestone
    - monthly
    - 40-30-30

  prohibited:
    - unlimited_revisions
    - unreviewed_legal_terms
    - source_code_before_payment
    - unavailable_team_commitment
```

Outside limits:

```text
Pause
→ Explain
→ Recommend
→ Request approval
```

---

# 53. Contract and Closing

Revnara may:

- Generate SOW
- Populate templates
- Compare clauses
- Flag deviations
- Route approval
- Track revision
- Request signature
- Confirm payment

Revnara may not independently:

- Sign as a legal person
- Accept unlimited liability
- Accept unapproved indemnity
- Waive IP protection
- Change governing law
- Commit unavailable resources

---

# 54. Delivery Handover

```text
Won
→ Create project
→ Attach proposal
→ Attach scope
→ Attach contract
→ Assign team
→ Transfer history
→ Transfer risks
→ Create kickoff
→ Create milestones
→ Notify delivery
```

Handover package:

- Requirements
- Scope
- Exclusions
- Proposal
- Contract
- Price
- Payment
- Timeline
- Team
- Expectations
- Commitments
- Risks
- Open questions
- Conversation history

---

# 55. Outcome Learning

Outcomes:

- Won
- Lost
- No response
- Budget mismatch
- Technical mismatch
- Risk rejection
- Payment concern
- Delivery decline

Learning dimensions:

- Channel
- Proposal style
- Length
- Response time
- Price
- Team
- Case study
- Follow-up
- Objections
- Profitability
- Delivery outcome

Recommendations require evaluation and approval before policy changes.

---

# 56. Context Engineering

```text
Task
→ Determine knowledge domains
→ Apply tenant permission
→ Retrieve structured data
→ Retrieve semantic evidence
→ Rank
→ Deduplicate
→ Compress
→ Build cited context
→ Execute
```

Only task-relevant data enters context.

---

# 57. RAG Architecture

Chunk metadata:

```json
{
  "tenant_id": "tenant_123",
  "workspace_id": "workspace_ai",
  "document_id": "case_77",
  "classification": "confidential",
  "allowed_roles": ["sales_manager", "proposal_agent"],
  "approved_for_external_use": true,
  "source_version": "4",
  "retention_policy": "three_years"
}
```

Controls:

- Tenant filter
- Permission filter
- Classification filter
- External-use filter
- Citation
- Versioning
- Deletion propagation
- Poisoning detection
- Instruction/data separation

---

# 58. Tool Registry and Tool Discovery

Do not load all tools into all agents.

```text
Task
→ Agent permission filter
→ Capability filter
→ Relevance search
→ Shortlist
→ Load schemas
```

Tool definition:

- Name
- Version
- Owner
- Input
- Output
- Risk
- Permission
- Approval
- Rate
- Timeout
- Idempotency
- Audit
- Data class
- Platform capability dependency

---

# 59. Connector Architecture

```text
integrations/
├── gmail/
├── microsoft-graph/
├── hubspot/
├── salesforce/
├── google-calendar/
├── slack/
├── upwork/
│   ├── approved-api/
│   ├── human-native-handoff/
│   ├── capability-map/
│   └── enforcement-response/
└── linkedin/
    ├── approved-api/
    ├── companion-drafting/
    ├── capability-map/
    └── enforcement-response/
```

Every connector publishes a capability manifest.

---

# 60. Model Gateway

Responsibilities:

- Provider abstraction
- Routing
- Failover
- Cost
- Latency
- Data-region enforcement
- Prompt versioning
- Token accounting
- Caching
- Redaction
- Output schema validation
- Model allowlist
- Provider health

Routing examples:

- Extraction → small model
- Public research → economical model
- Confidential proposal → approved enterprise model
- Contract review → restricted model
- Final strategy → strong reasoning model

---

# 61. Policy Engine

Policy domains:

- Business
- Pricing
- Communication
- Legal
- Security
- Privacy
- Platform
- Model
- Data
- Approval
- Retention

Policies are versioned and testable.

---

# 62. Risk Engine

Risk categories:

- Security
- Privacy
- Legal
- Financial
- Reputation
- Platform
- Delivery
- Fraud
- AI accuracy
- Cross-tenant
- Credential
- Insider
- Model outage

Action tiers:

| Tier | Example | Execution |
|---|---|---|
| R0 | Internal search | Automatic |
| R1 | Public research | Automatic |
| R2 | Draft proposal | Automatic + validation |
| R3 | Approved email follow-up | Constrained |
| R4 | Commercial submission | Approval or human-native |
| R5 | Price/scope exception | Human approval |
| R6 | Contract/legal acceptance | Authorized human |

---

# 63. Security Architecture

- Encryption in transit
- Encryption at rest
- KMS
- Tenant key context
- MFA
- SSO
- RBAC
- ABAC
- WAF
- API gateway
- DLP
- Malware scan
- Egress control
- Secret vault
- Key rotation
- Dependency scan
- Container scan
- SBOM
- Signed artifacts
- Penetration testing
- Incident response
- Immutable audit
- Secure backup
- Secure deletion

---

# 64. Zero-Trust Architecture

Verify:

- User
- Device
- Session
- Tenant
- Service
- Agent
- Tool
- Capability
- Credential
- Resource
- Action

Use:

- Short-lived identity
- Least privilege
- Network segmentation
- Service authentication
- Continuous authorization
- Explicit egress allowlist

---

# 65. Prompt Injection and Agentic Threat Defense

Threats:

- Direct prompt injection
- Indirect injection
- Tool manipulation
- RAG poisoning
- Memory poisoning
- Data exfiltration
- Excessive agency
- Malicious attachment
- Insecure output
- Resource exhaustion

Controls:

- Treat external content as data
- Separate trusted instructions
- Allowlist tools
- Structured tool calls
- Validate input/output
- No secrets in context
- DLP
- Sandboxing
- Egress limits
- Approval
- Red-team evaluation

---

# 66. Privacy and Data Lifecycle

Lifecycle:

```text
Collect
→ Classify
→ Store
→ Use
→ Share
→ Retain
→ Archive
→ Delete
```

Controls:

- Purpose limitation
- Data minimization
- Consent
- Retention schedule
- Legal hold
- Export
- Correction
- Deletion
- Subprocessor tracking
- Regional processing

---

# 67. GDPR/CCPA Deletion Mechanics

Deletion is not only a field.

Workflow:

```text
Deletion request
→ Verify requester
→ Identify tenant and subjects
→ Check legal hold
→ Locate relational data
→ Locate objects
→ Locate search documents
→ Locate vector chunks
→ Locate analytics copies
→ Locate backups policy
→ Delete or anonymize
→ Rebuild affected indexes
→ Notify subprocessors
→ Produce deletion certificate
```

Maintain:

- Deletion job status
- Systems affected
- Exceptions
- Legal basis
- Completion evidence
- Backup expiration date

---

# 68. External-State Reconciliation

External state may change outside Revnara:

- Job withdrawn
- Message deleted
- Meeting canceled
- Contract modified
- Account permission removed
- Token revoked
- Client stage changed

Reconciliation:

```text
Webhook or scheduled sync
→ Compare external and internal version
→ Detect conflict
→ Apply conflict policy
→ Pause dependent workflows
→ Notify owner
→ Record reconciliation event
```

Conflict policies:

- External wins
- Internal wins
- Human review
- Merge
- Terminal close

---

# 69. Explainability

Every important decision stores:

- Decision
- Inputs
- Evidence
- Rules
- Model
- Confidence
- Alternatives
- Missing data
- Human override
- Outcome

Examples:

- Why score is 75
- Why price is 18,000
- Why opportunity was rejected
- Why approval was required
- Why team member was selected

---

# 70. Human Audit Sampling

Even automatic actions require sampling.

Sampling policies:

- Random sample
- Risk-weighted sample
- New agent version
- New model
- New tenant
- New connector
- Low confidence
- High value
- High complaint rate

Audit outcomes:

- Correct
- Minor correction
- Major correction
- Policy violation
- Security incident

Sampling results affect autonomy level.

---

# 71. Observability and Audit

Record:

- Tenant
- User
- Agent
- Agent version
- Model
- Prompt
- Workflow
- Input
- Evidence
- Tool
- Capability
- Policy
- Approval
- Cost
- Latency
- Output
- Confidence
- Error
- External result

Dashboards:

- System health
- Agent quality
- Connector health
- Platform risk
- Cost
- Workflow backlog
- Approval delay
- Security events

---

# 72. Reliability and Failure Containment

Patterns:

- Durable queue
- Retry
- Backoff
- Circuit breaker
- Dead letter
- Bulkhead
- Timeout
- Idempotency
- Transactional outbox
- Provider failover
- Graceful degradation
- Feature flag
- Canary release
- Rollback

Kill switches:

- Agent
- Tool
- Model
- Connection
- Platform
- Tenant
- External communication
- All autonomous actions

---

# 73. Disaster Recovery and Business Continuity

Define:

- RPO
- RTO
- Backup frequency
- Restore test
- Region failure
- Provider outage
- Credential-vault outage
- Model-provider outage
- Queue outage
- Database corruption

Example target classes:

```text
Critical workflow state:
RPO ≤ 5 minutes
RTO ≤ 1 hour

Analytics:
RPO ≤ 24 hours
RTO ≤ 24 hours
```

Targets must be validated against cost and customer tier.

---

# 74. Sandbox and Staging Environments

Provide:

- Internal development
- Integration test
- Staging
- Customer sandbox
- Production

Sandbox rules:

- Synthetic data by default
- Separate credentials
- Separate keys
- No production message send
- No native restricted-platform execution
- Agent version testing
- Policy simulation
- Historical replay

---

# 75. Notification and Approval UX

Delivery channels:

- In-app inbox
- Email
- Slack
- Microsoft Teams
- Mobile push
- Daily digest
- Escalation call integration for critical events

Approval item includes:

- Requested action
- Client
- Opportunity
- Risk
- Price
- Evidence
- Changes
- Expiration
- Approve
- Reject
- Edit
- Delegate

Escalation:

```text
Primary approver
→ Backup approver
→ Manager
→ Auto-expire or safe rejection
```

---

# 76. LLM Cost Governance

Per tenant:

- Monthly budget
- Daily budget
- Agent budget
- Workflow budget
- Opportunity budget
- Model allowlist
- Maximum tokens
- Maximum retries
- Cache policy

Cost controls:

- Small-model first
- Context compression
- Retrieval limits
- Response limits
- Batch extraction
- Semantic cache
- Budget alerts
- Circuit breaker

---

# 77. Evaluation Framework

## Offline

- Historical opportunities
- Winning proposals
- Losing proposals
- Pricing edge cases
- Objections
- Prompt injection
- Missing information
- Confidentiality
- Platform-policy cases

## Online

- Response rate
- Meeting rate
- Win rate
- Margin
- Human correction
- Hallucinated claim
- Policy violation
- Duplicate action
- Cost per win
- Platform warnings
- Delivery success

Release gates require regression pass.

---

# 78. SaaS Pricing and Packaging

Possible pricing models:

## Seat-Based

- User seats
- Admin seats
- Reviewer seats

## Usage-Based

- Opportunities
- Agent runs
- Documents
- Email actions
- Tokens
- Storage

## Value-Based

- Pipeline managed
- Won revenue
- Success fee

## Enterprise

- Dedicated tenant
- Private models
- Data residency
- SSO
- SCIM
- Audit export
- Custom retention
- Premium support

Recommended commercial strategy:

```text
Base platform subscription
+ usage allowance
+ enterprise security add-ons
+ optional success-based component
```

Avoid a pure revenue-share model initially because attribution and contract complexity are high.

---

# 79. Competitive Landscape Methodology

Do not assume competitor compliance from marketing claims.

Evaluate competitors by:

- Integration method
- Official API approval
- Browser automation
- Human submission
- Data source
- Account restriction reports
- Pricing
- Target customer
- Proposal quality
- Governance
- Audit
- Security
- Outcome evidence

Competitor categories:

- Proposal assistants
- Marketplace bid tools
- LinkedIn outreach tools
- Sales engagement platforms
- AI SDR platforms
- CRM copilots
- Revenue intelligence
- Agent orchestration platforms

Revnara differentiation should focus on:

- Governed multi-agent operations
- Software-house-specific knowledge
- Delivery feasibility
- Profitability
- Platform capability governance
- Security and audit
- Full handover to delivery

---

# 80. Standards and Compliance Roadmap

Target frameworks:

- ISO/IEC 27001
- ISO/IEC 42001
- SOC 2
- NIST AI RMF
- NIST GenAI Profile
- NIST Zero Trust Architecture
- NIST SSDF
- OWASP LLM Top 10
- OWASP Agentic Applications guidance
- OWASP ASVS
- GDPR
- CCPA/CPRA where applicable
- EU AI Act where applicable
- ISO 22301 principles
- Cloud Security Alliance controls

Roadmap:

## Phase A

- Policies
- Asset inventory
- Access control
- Risk register
- Incident response
- SDLC
- Vendor management

## Phase B

- Evidence collection
- Internal audit
- Penetration test
- Business continuity test
- AI governance records

## Phase C

- SOC 2 Type I
- ISO readiness

## Phase D

- SOC 2 Type II
- ISO certification where commercially justified

---

# 81. Deployment Architecture

Start with:

- Modular monolith for domains
- Separate agent workers
- Separate workflow workers
- Isolated connector workers
- Event bus
- Managed database
- Object storage
- Vector index
- Search
- Vault
- Observability

Split services when required by:

- Security
- Scale
- Failure isolation
- Regulatory needs
- Team ownership
- Deployment frequency

---

# 82. Codebase Structure

```text
Revnara/
├── apps/
│   ├── web-console/
│   ├── admin-console/
│   ├── public-api/
│   └── worker-runtime/
├── platform/
│   ├── identity/
│   ├── tenancy/
│   ├── authorization/
│   ├── platform-capabilities/
│   ├── policy-engine/
│   ├── risk-engine/
│   ├── approval-engine/
│   ├── audit/
│   ├── billing/
│   └── notifications/
├── agent-runtime/
│   ├── orchestrator/
│   ├── planner/
│   ├── executor/
│   ├── verifier/
│   ├── agent-registry/
│   ├── tool-registry/
│   ├── model-gateway/
│   ├── context-engine/
│   └── evaluation-engine/
├── domains/
│   ├── organizations/
│   ├── teams/
│   ├── capabilities/
│   ├── opportunities/
│   ├── clients/
│   ├── proposals/
│   ├── pricing/
│   ├── communications/
│   ├── meetings/
│   ├── negotiations/
│   ├── contracts/
│   ├── handover/
│   └── learning/
├── integrations/
│   ├── gmail/
│   ├── microsoft/
│   ├── hubspot/
│   ├── salesforce/
│   ├── upwork/
│   └── linkedin/
├── governance/
│   ├── policy-evidence/
│   ├── platform-risk/
│   ├── data-retention/
│   ├── model-inventory/
│   └── compliance-evidence/
├── security/
│   ├── threat-models/
│   ├── dlp/
│   ├── secrets/
│   ├── isolation-tests/
│   └── red-team/
├── evals/
└── infrastructure/
```

---

# 83. Event and API Architecture

Events:

```text
OrganizationConfigured
AccountConnected
CapabilityActivated
CapabilityExpired
CapabilityRevoked
OpportunityDiscovered
OpportunityQualified
ProposalDrafted
ProposalValidated
ApprovalRequested
ApprovalGranted
HumanSubmissionRequested
HumanSubmissionConfirmed
ClientReplied
MeetingScheduled
NegotiationEscalated
ContractApproved
DealWon
DealLost
RestrictionDetected
ConnectorSuspended
DeletionCompleted
ProjectHandedOver
```

Use:

- Transactional outbox
- Idempotent consumers
- Event versioning
- Correlation ID
- Causation ID
- Dead-letter handling
- Replay permission

---

# 84. Development Phases

## Phase 0 — Validation

- Legal review
- Platform policy matrix
- Customer interviews
- Competitive analysis
- Architecture decisions
- Risk register

## Phase 1 — Intelligence Copilot

- Company Brain
- Opportunity intake
- Research
- Qualification
- Proposal drafting
- Human submission
- Basic audit

## Phase 2 — Supervised Operations

- Email
- CRM
- Calendar
- Approval center
- Follow-up drafting
- Platform capability governance
- Cost controls

## Phase 3 — Constrained Autonomy

- Low-risk email actions
- CRM updates
- Scheduling
- Policy-based execution
- Human audit sampling
- Connector health

## Phase 4 — Outcome-Driven Platform

- Revenue objectives
- Multi-channel prioritization
- Dynamic strategy
- Learning
- Profitability optimization

## Phase 5 — Enterprise Autonomous Operations

- Broad approved autonomy
- Human exception handling
- Dedicated deployment
- Compliance certification
- Strategic account expansion

Restricted platforms remain human-native where required.

---

# 85. MVP Definition

Include:

- Multi-tenant organizations
- Roles and permissions
- Company profile
- Team
- Portfolio
- Historical proposals
- Opportunity intake
- Qualification
- Team matching
- Proposal drafting
- Pricing rules
- Approval
- Gmail or Microsoft integration
- One CRM
- Calendar
- Human-native Upwork workflow
- LinkedIn companion drafting
- Audit
- Basic analytics
- Platform capability registry

Exclude:

- Automated Upwork submission
- Automated LinkedIn outreach
- Browser automation
- Contract signing
- Autonomous legal decisions
- Automatic production policy changes

---

# 86. Quality Gates

Before production:

- 100% external actions audited
- 100% high-risk actions approved
- Zero known cross-tenant path
- No duplicate submission
- Every claim has evidence
- Pricing passes policy
- Workflow recovers after worker failure
- Model and prompt are versioned
- Tool permissions are explicit
- Secrets never enter context
- Platform capability is active
- Restricted actions remain human-native
- Regression suite passes
- Kill switches work
- Restore test passes
- Deletion workflow passes
- Human audit sampling is configured

---

# 87. Architecture Decision Records

Maintain ADRs for:

- Modular monolith vs microservices
- Workflow engine
- Model gateway
- Vector database
- Tenant isolation
- Encryption
- Upwork operating mode
- LinkedIn operating mode
- Browser automation prohibition
- Human-native task model
- Approval architecture
- Data residency
- Provider failover

Each ADR includes:

- Context
- Decision
- Alternatives
- Consequences
- Risks
- Review date

---

# 88. Open Risks and Required Validation

Before implementation:

1. Obtain legal interpretation of Upwork commercial use.
2. Apply for relevant Upwork partnership if commercially necessary.
3. Confirm exact Upwork API capabilities.
4. Confirm LinkedIn partner programs relevant to company-page use.
5. Validate target customers’ acquisition channels.
6. Validate willingness to use human-native submission.
7. Test proposal quality against historical data.
8. Define E&O and cyber-insurance needs.
9. Select workflow engine.
10. Select tenant isolation model.
11. Define first CRM and email integrations.
12. Define pricing.
13. Build platform dependency risk register.
14. Complete threat model.
15. Define success criteria for the MVP.

---

# 89. Final Architectural Doctrine

```text
External platforms define the available channels.

Platform capability governance defines what is permitted.

Connections provide scoped access.

Credentials provide technical authorization.

Human actors provide native identity and legal authority.

Workflows provide durable execution.

Agents provide intelligence.

Policies define boundaries.

Risk controls limit damage.

Approvals authorize sensitive actions.

Validators provide quality.

Evidence prevents unsupported claims.

Audit provides accountability.

Evaluation determines earned autonomy.

Unsupported actions remain disabled.
```

The product must never be:

> Give the AI passwords and let it operate every account.

The product must be:

> Connect permitted business systems, define company objectives and boundaries, and allow governed AI agents to research, decide, prepare, coordinate, and execute only those actions that are explicitly authorized, technically supported, legally acceptable, and operationally safe.

---

# 90. Official Reference Sources

The following sources were reviewed for the platform-dependent sections of this document as of 2026-07-10. Platform policy may change; the production system must maintain its own reviewed and expiring evidence records.

## Upwork

- Upwork — Use bots and other automation properly  
  https://support.upwork.com/hc/en-us/articles/43342677368467-Use-bots-and-other-automation-properly

- Upwork — API section and commercial API use  
  https://support.upwork.com/hc/en-us/sections/17976982721555-Upwork-API

- Upwork — API documentation  
  https://www.upwork.com/developer/documentation/graphql/api/docs/index.html

- Upwork — Manage agency proposals and offers  
  https://support.upwork.com/hc/en-us/articles/360009524274-How-to-manage-your-agency-proposals-and-offers

- Upwork — API key disabled  
  https://support.upwork.com/hc/en-us/articles/17995826674579--API-key-disabled

## LinkedIn

- LinkedIn User Agreement  
  https://www.linkedin.com/legal/user-agreement

- LinkedIn — Prohibited software and extensions  
  https://www.linkedin.com/help/linkedin/answer/a1341387

- LinkedIn — Automated activity  
  https://www.linkedin.com/help/linkedin/answer/a1340567

- LinkedIn API — Getting access  
  https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access

- LinkedIn OAuth overview  
  https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication

## AI and Security Governance

- NIST AI Risk Management Framework  
  https://www.nist.gov/itl/ai-risk-management-framework

- NIST Generative AI Profile  
  https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

- OWASP Top 10 for LLM Applications 2025  
  https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/

- OWASP Top 10 for Agentic Applications 2026  
  https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

- AICPA Trust Services Criteria  
  https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022

- ISO standards portal  
  https://www.iso.org/standards.html

---

# End of Document
