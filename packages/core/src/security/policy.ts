import {
  brand,
  copyJsonValue,
  messageKey,
  type Brand,
  type JsonValue,
  type MessageDescriptor,
  type MessageKey,
  type MessageParams,
} from "../shared/index";

export type SecurityPolicyId = Brand<string, "SecurityPolicyId">;

export type SecurityPolicyViolationCode =
  | "SECURITY_POLICY_DENIED"
  | "SECURITY_SECRET_REQUIRED"
  | "SECURITY_INVALID_HASH"
  | "SECURITY_UNSUPPORTED_ALGORITHM"
  | "SECURITY_SENSITIVE_VALUE_REJECTED";

export type SecurityPolicyEvidenceValue = JsonValue;
export type SecurityPolicyEvidence = Readonly<Record<string, SecurityPolicyEvidenceValue>>;

export interface SecurityPolicyViolation extends MessageDescriptor {
  readonly code: SecurityPolicyViolationCode;
  readonly details?: SecurityPolicyEvidence;
  readonly cause?: unknown;
}

export type SecurityPolicyDecision =
  | {
      readonly allowed: true;
      readonly policyId?: SecurityPolicyId;
      readonly reason?: MessageDescriptor;
      readonly evidence?: SecurityPolicyEvidence;
    }
  | {
      readonly allowed: false;
      readonly policyId?: SecurityPolicyId;
      readonly violation: SecurityPolicyViolation;
      readonly evidence?: SecurityPolicyEvidence;
    };

export interface SecurityPolicyEvaluator<Input = unknown> {
  evaluate(input: Input): Promise<SecurityPolicyDecision>;
}

export function securityPolicyId(value: string): SecurityPolicyId {
  assertToken("security policy id", value);
  return brand<string, "SecurityPolicyId">(value);
}

export function securityPolicyViolation(input: {
  readonly code: SecurityPolicyViolationCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly details?: SecurityPolicyEvidence;
  readonly cause?: unknown;
}): SecurityPolicyViolation {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.details === undefined ? {} : { details: copySecurityPolicyEvidence(input.details) }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
  };
}

export function securityPolicyAllowed(input: {
  readonly policyId?: SecurityPolicyId;
  readonly reason?: MessageDescriptor;
  readonly evidence?: SecurityPolicyEvidence;
} = {}): SecurityPolicyDecision {
  return {
    allowed: true,
    ...(input.policyId === undefined ? {} : { policyId: input.policyId }),
    ...(input.reason === undefined ? {} : { reason: input.reason }),
    ...(input.evidence === undefined ? {} : { evidence: copySecurityPolicyEvidence(input.evidence) }),
  };
}

export function securityPolicyDenied(input: {
  readonly policyId?: SecurityPolicyId;
  readonly violation: SecurityPolicyViolation;
  readonly evidence?: SecurityPolicyEvidence;
}): SecurityPolicyDecision {
  return {
    allowed: false,
    ...(input.policyId === undefined ? {} : { policyId: input.policyId }),
    violation: input.violation,
    ...(input.evidence === undefined ? {} : { evidence: copySecurityPolicyEvidence(input.evidence) }),
  };
}

export function fixedSecurityPolicyEvaluator<Input = unknown>(
  decision: SecurityPolicyDecision,
): SecurityPolicyEvaluator<Input> {
  return {
    evaluate: async () => decision,
  };
}

function copySecurityPolicyEvidence<TValue extends SecurityPolicyEvidence>(value: TValue): TValue {
  return Object.fromEntries(
    Object.entries(value).map(([key, nestedValue]) => [key, copyJsonValue(nestedValue, "security policy evidence")]),
  ) as TValue;
}

function assertNonEmpty(label: string, value: string): void {
  if (value.length === 0) {
    throw new TypeError(`${label} must be non-empty.`);
  }
}

function assertToken(label: string, value: string): void {
  assertNonEmpty(label, value);

  if (value.trim() !== value || /\s/.test(value)) {
    throw new TypeError(`${label} must not contain whitespace.`);
  }
}
