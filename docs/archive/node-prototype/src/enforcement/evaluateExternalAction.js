import {
  BLOCKING_CAPABILITY_STATUSES,
  CapabilityStatus,
  ConnectorMode,
  isKnownCapabilityStatus,
  isKnownConnectorMode,
  riskTierRank,
} from "../domain/capabilities.js";

const Decision = Object.freeze({
  ALLOW: "allow",
  BLOCK: "block",
  REQUIRE_HUMAN_NATIVE: "require_human_native",
  REQUIRE_APPROVAL: "require_approval",
});

export function evaluateExternalAction(request, now = new Date()) {
  const reasons = [];
  const requiredApprovals = [];

  const block = (code, message) => ({
    decision: Decision.BLOCK,
    code,
    reasons: [...reasons, message],
    requiredApprovals,
  });

  if (!request?.tenant?.id || request.tenant.status !== "active") {
    return block("TENANT_INACTIVE", "Tenant must be resolved and active.");
  }

  if (!request.actor?.id || request.actor.authenticated !== true) {
    return block("ACTOR_UNAUTHENTICATED", "Actor must be authenticated.");
  }

  if (request.authorization?.allowed !== true) {
    return block("ACTION_UNAUTHORIZED", "Actor or agent is not authorized for this action.");
  }

  const capability = request.platformCapability;
  if (!capability?.id) {
    return block("CAPABILITY_MISSING", "Platform capability record is required.");
  }

  if (!isKnownCapabilityStatus(capability.status)) {
    return block("CAPABILITY_STATUS_UNKNOWN", `Unknown capability status: ${capability.status}`);
  }

  if (!isKnownConnectorMode(capability.connectorMode)) {
    return block("CONNECTOR_MODE_UNKNOWN", `Unknown connector mode: ${capability.connectorMode}`);
  }

  if (request.killSwitches?.globalAutonomy === true) {
    return block("GLOBAL_KILL_SWITCH", "Global autonomous action kill switch is enabled.");
  }

  if (request.killSwitches?.capabilityIds?.includes(capability.id)) {
    return block("CAPABILITY_KILL_SWITCH", "Capability kill switch is enabled.");
  }

  if (capability.expiresAt && new Date(capability.expiresAt) <= now) {
    return block("CAPABILITY_EXPIRED", "Capability has expired and requires review.");
  }

  if (BLOCKING_CAPABILITY_STATUSES.has(capability.status)) {
    return block("CAPABILITY_NOT_EXECUTABLE", `Capability status blocks execution: ${capability.status}`);
  }

  if (
    capability.status === CapabilityStatus.AVAILABLE_HUMAN_NATIVE_ONLY &&
    request.executionMode !== "human_native_record"
  ) {
    return {
      decision: Decision.REQUIRE_HUMAN_NATIVE,
      code: "HUMAN_NATIVE_REQUIRED",
      reasons: [
        ...reasons,
        "This capability is human-native only and cannot be executed by an agent or connector.",
      ],
      requiredApprovals,
    };
  }

  if (request.requestedConnectorMode !== capability.connectorMode) {
    return block("CONNECTOR_MODE_MISMATCH", "Requested connector mode does not match capability.");
  }

  const policyDecision = request.policyDecision;
  if (!policyDecision?.decision) {
    return block("POLICY_DECISION_MISSING", "Policy decision is required.");
  }

  if (policyDecision.decision === "deny") {
    return block("POLICY_DENIED", "Policy engine denied this action.");
  }

  if (policyDecision.decision === "require_review") {
    return block("POLICY_REVIEW_REQUIRED", "Policy requires review before execution.");
  }

  if (!request.riskAssessment?.tier) {
    return block("RISK_ASSESSMENT_MISSING", "Risk assessment is required.");
  }

  const riskRank = riskTierRank(request.riskAssessment.tier);
  const maxRank = riskTierRank(request.riskAssessment.maxAllowedTier ?? "R3");
  if (riskRank > maxRank) {
    return block("RISK_EXCEEDS_LIMIT", "Risk tier exceeds allowed execution limit.");
  }

  const approvalRequired =
    capability.status === CapabilityStatus.AVAILABLE_WITH_APPROVAL ||
    policyDecision.decision === "require_approval" ||
    riskRank >= riskTierRank("R4");

  if (approvalRequired) {
    requiredApprovals.push(...(policyDecision.requiredApprovals ?? ["business_owner"]));
    const approvalCheck = validateApprovalBinding(request, now);
    if (!approvalCheck.valid) {
      return {
        decision: approvalCheck.missing ? Decision.REQUIRE_APPROVAL : Decision.BLOCK,
        code: approvalCheck.code,
        reasons: [...reasons, approvalCheck.reason],
        requiredApprovals,
      };
    }
  }

  if (capability.connectorMode === ConnectorMode.OFFICIAL_API && !request.credentialGrant?.id) {
    return block("CREDENTIAL_GRANT_MISSING", "Official API execution requires a credential grant.");
  }

  if (!request.idempotencyKey) {
    return block("IDEMPOTENCY_KEY_MISSING", "External actions require an idempotency key.");
  }

  if (request.audit?.enabled !== true) {
    return block("AUDIT_REQUIRED", "Audit must be enabled before execution.");
  }

  return {
    decision: Decision.ALLOW,
    code: "ACTION_ALLOWED",
    reasons: ["Action passed enforcement checks."],
    requiredApprovals,
  };
}

function validateApprovalBinding(request, now) {
  const approval = request.approval;
  if (!approval?.id) {
    return {
      valid: false,
      missing: true,
      code: "APPROVAL_REQUIRED",
      reason: "Approval is required for this action.",
    };
  }

  if (approval.status !== "approved") {
    return {
      valid: false,
      code: "APPROVAL_NOT_APPROVED",
      reason: "Approval exists but is not approved.",
    };
  }

  if (approval.expiresAt && new Date(approval.expiresAt) <= now) {
    return {
      valid: false,
      code: "APPROVAL_EXPIRED",
      reason: "Approval has expired.",
    };
  }

  const expected = {
    tenantId: request.tenant.id,
    platformCapabilityId: request.platformCapability.id,
    capabilityVersion: request.platformCapability.version,
    policyVersion: request.policyDecision.policyVersion,
    payloadHash: request.payloadHash,
  };

  for (const [key, value] of Object.entries(expected)) {
    if (approval.binding?.[key] !== value) {
      return {
        valid: false,
        code: "APPROVAL_BINDING_MISMATCH",
        reason: `Approval binding mismatch for ${key}.`,
      };
    }
  }

  return { valid: true };
}

