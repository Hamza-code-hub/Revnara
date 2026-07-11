export const CapabilityStatus = Object.freeze({
  AVAILABLE_AUTOMATIC: "available_automatic",
  AVAILABLE_WITH_APPROVAL: "available_with_approval",
  AVAILABLE_HUMAN_NATIVE_ONLY: "available_human_native_only",
  AVAILABLE_READ_ONLY: "available_read_only",
  PARTNER_CONTRACT_REQUIRED: "partner_contract_required",
  REVIEW_REQUIRED: "review_required",
  TEMPORARILY_SUSPENDED: "temporarily_suspended",
  UNSUPPORTED: "unsupported",
  REVOKED: "revoked",
});

export const ConnectorMode = Object.freeze({
  OFFICIAL_API: "official_api",
  NATIVE_ORGANIZATIONAL_DELEGATION: "native_organizational_delegation",
  COMPANION_DRAFTING: "companion_drafting",
  APPROVED_BROWSER_ASSISTANCE: "approved_browser_assistance",
  UNSUPPORTED: "unsupported",
});

export const RiskTier = Object.freeze({
  R0: "R0",
  R1: "R1",
  R2: "R2",
  R3: "R3",
  R4: "R4",
  R5: "R5",
  R6: "R6",
});

export const RISK_TIER_ORDER = Object.freeze({
  [RiskTier.R0]: 0,
  [RiskTier.R1]: 1,
  [RiskTier.R2]: 2,
  [RiskTier.R3]: 3,
  [RiskTier.R4]: 4,
  [RiskTier.R5]: 5,
  [RiskTier.R6]: 6,
});

export const BLOCKING_CAPABILITY_STATUSES = new Set([
  CapabilityStatus.PARTNER_CONTRACT_REQUIRED,
  CapabilityStatus.REVIEW_REQUIRED,
  CapabilityStatus.TEMPORARILY_SUSPENDED,
  CapabilityStatus.UNSUPPORTED,
  CapabilityStatus.REVOKED,
]);

export function isKnownCapabilityStatus(status) {
  return Object.values(CapabilityStatus).includes(status);
}

export function isKnownConnectorMode(mode) {
  return Object.values(ConnectorMode).includes(mode);
}

export function riskTierRank(tier) {
  if (!(tier in RISK_TIER_ORDER)) {
    throw new Error(`Unknown risk tier: ${tier}`);
  }

  return RISK_TIER_ORDER[tier];
}

