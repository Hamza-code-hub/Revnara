import test from "node:test";
import assert from "node:assert/strict";

import { CapabilityStatus, ConnectorMode } from "../src/domain/capabilities.js";
import { evaluateExternalAction } from "../src/enforcement/evaluateExternalAction.js";

const now = new Date("2026-07-10T12:00:00.000Z");

function baseRequest(overrides = {}) {
  const request = {
    tenant: { id: "tenant_1", status: "active" },
    actor: { id: "agent_1", authenticated: true },
    authorization: { allowed: true },
    platformCapability: {
      id: "cap_email_send",
      version: "1",
      status: CapabilityStatus.AVAILABLE_WITH_APPROVAL,
      connectorMode: ConnectorMode.OFFICIAL_API,
      expiresAt: "2026-10-10T00:00:00.000Z",
    },
    requestedConnectorMode: ConnectorMode.OFFICIAL_API,
    executionMode: "connector_execute",
    policyDecision: {
      decision: "require_approval",
      policyVersion: "policy-v1",
      requiredApprovals: ["sales_manager"],
    },
    riskAssessment: { tier: "R4", maxAllowedTier: "R4" },
    payloadHash: "sha256:proposal-v1",
    approval: {
      id: "approval_1",
      status: "approved",
      expiresAt: "2026-07-11T12:00:00.000Z",
      binding: {
        tenantId: "tenant_1",
        platformCapabilityId: "cap_email_send",
        capabilityVersion: "1",
        policyVersion: "policy-v1",
        payloadHash: "sha256:proposal-v1",
      },
    },
    credentialGrant: { id: "grant_1" },
    idempotencyKey: "idem_1",
    audit: { enabled: true },
    killSwitches: {},
  };

  return deepMerge(request, overrides);
}

test("allows approved official API action when all enforcement checks pass", () => {
  const result = evaluateExternalAction(baseRequest(), now);

  assert.equal(result.decision, "allow");
  assert.equal(result.code, "ACTION_ALLOWED");
});

test("requires human-native flow for human-native capability", () => {
  const result = evaluateExternalAction(
    baseRequest({
      platformCapability: {
        id: "cap_upwork_submit",
        status: CapabilityStatus.AVAILABLE_HUMAN_NATIVE_ONLY,
        connectorMode: ConnectorMode.COMPANION_DRAFTING,
      },
      requestedConnectorMode: ConnectorMode.COMPANION_DRAFTING,
      executionMode: "connector_execute",
      riskAssessment: { tier: "R3", maxAllowedTier: "R3" },
      policyDecision: { decision: "allow", policyVersion: "policy-v1" },
      approval: null,
      credentialGrant: null,
    }),
    now,
  );

  assert.equal(result.decision, "require_human_native");
  assert.equal(result.code, "HUMAN_NATIVE_REQUIRED");
});

test("blocks unsupported platform capability", () => {
  const result = evaluateExternalAction(
    baseRequest({
      platformCapability: {
        status: CapabilityStatus.UNSUPPORTED,
      },
    }),
    now,
  );

  assert.equal(result.decision, "block");
  assert.equal(result.code, "CAPABILITY_NOT_EXECUTABLE");
});

test("blocks execution when approved payload has drifted", () => {
  const result = evaluateExternalAction(
    baseRequest({
      payloadHash: "sha256:proposal-v2",
    }),
    now,
  );

  assert.equal(result.decision, "block");
  assert.equal(result.code, "APPROVAL_BINDING_MISMATCH");
});

test("fails closed when audit is disabled", () => {
  const result = evaluateExternalAction(
    baseRequest({
      audit: { enabled: false },
    }),
    now,
  );

  assert.equal(result.decision, "block");
  assert.equal(result.code, "AUDIT_REQUIRED");
});

function deepMerge(target, source) {
  if (source === null || typeof source !== "object" || Array.isArray(source)) {
    return source;
  }

  const output = { ...target };
  for (const [key, value] of Object.entries(source)) {
    output[key] =
      value && typeof value === "object" && !Array.isArray(value)
        ? deepMerge(target?.[key] ?? {}, value)
        : value;
  }

  return output;
}

