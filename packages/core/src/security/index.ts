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

export type SecretString = Brand<string, "SecretString">;
export type HashAlgorithm = Brand<string, "HashAlgorithm">;
export type HashValue = Brand<string, "HashValue">;
export type SecurityPolicyId = Brand<string, "SecurityPolicyId">;

export const dataSensitivities = ["public", "internal", "confidential", "restricted", "secret"] as const;
export type DataSensitivity = (typeof dataSensitivities)[number];

export const sensitiveValueKinds = [
  "credential",
  "token",
  "api-key",
  "private-key",
  "secret",
  "personal-data",
  "tenant-data",
  "financial-data",
  "security-evidence",
] as const;
export type SensitiveValueKind = (typeof sensitiveValueKinds)[number];

export type SecurityPolicyViolationCode =
  | "SECURITY_POLICY_DENIED"
  | "SECURITY_SECRET_REQUIRED"
  | "SECURITY_INVALID_HASH"
  | "SECURITY_UNSUPPORTED_ALGORITHM"
  | "SECURITY_SENSITIVE_VALUE_REJECTED";

export type SecurityPolicyEvidenceValue = JsonValue;
export type SecurityPolicyEvidence = Readonly<Record<string, SecurityPolicyEvidenceValue>>;

export interface Hash {
  readonly algorithm: HashAlgorithm;
  readonly value: HashValue;
}

export interface Hasher {
  hash(value: SecretString): Promise<Hash>;
  verify(value: SecretString, expected: Hash): Promise<boolean>;
}

export interface DataClassification {
  readonly kind: SensitiveValueKind;
  readonly sensitivity: DataSensitivity;
  readonly reason?: MessageDescriptor;
}

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

export function secretString(value: string): SecretString {
  assertNonEmpty("secret string", value);
  return brand<string, "SecretString">(value);
}

export function hashAlgorithm(value: string): HashAlgorithm {
  assertToken("hash algorithm", value);
  return brand<string, "HashAlgorithm">(value);
}

export function hashValue(value: string): HashValue {
  assertToken("hash value", value);
  return brand<string, "HashValue">(value);
}

export function hash(input: { readonly algorithm: string | HashAlgorithm; readonly value: string | HashValue }): Hash {
  return {
    algorithm: hashAlgorithm(input.algorithm),
    value: hashValue(input.value),
  };
}

export function securityPolicyId(value: string): SecurityPolicyId {
  assertToken("security policy id", value);
  return brand<string, "SecurityPolicyId">(value);
}

export function dataClassification(input: {
  readonly kind: SensitiveValueKind;
  readonly sensitivity: DataSensitivity;
  readonly reason?: MessageDescriptor;
}): DataClassification {
  assertKnownValue("sensitive value kind", input.kind, sensitiveValueKinds);
  assertKnownValue("data sensitivity", input.sensitivity, dataSensitivities);

  return {
    kind: input.kind,
    sensitivity: input.sensitivity,
    ...(input.reason === undefined ? {} : { reason: input.reason }),
  };
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

function assertKnownValue<TValue extends string>(
  label: string,
  value: string,
  allowedValues: readonly TValue[],
): asserts value is TValue {
  if (!allowedValues.includes(value as TValue)) {
    throw new TypeError(`${label} must be one of: ${allowedValues.join(", ")}.`);
  }
}
