export const failureKinds = [
  "user_input",
  "validation",
  "authentication",
  "authorization",
  "configuration",
  "dependency_unavailable",
  "timeout",
  "rate_limited",
  "resource_exhausted",
  "conflict",
  "data_integrity",
  "bug",
  "unknown",
] as const;
export type FailureKind = (typeof failureKinds)[number];

export const failureSources = ["user", "app", "platform", "provider", "infra", "external", "unknown"] as const;
export type FailureSource = (typeof failureSources)[number];

export const failureSeverities = ["info", "warning", "error", "critical"] as const;
export type FailureSeverity = (typeof failureSeverities)[number];

export const recoveryDispositions = [
  "not_recoverable",
  "user_correctable",
  "automation_retryable",
  "automation_repairable",
  "manual_investigation",
  "escalated",
] as const;
export type RecoveryDisposition = (typeof recoveryDispositions)[number];

export const recoveryActions = ["none", "ask_user", "retry", "repair", "rollback", "dead_letter", "escalate"] as const;
export type RecoveryAction = (typeof recoveryActions)[number];

export type DiagnosticFactValue = string | number | boolean | null;
export type DiagnosticFacts = Readonly<Record<string, DiagnosticFactValue>>;

export const defaultDiagnosticFactCountLimit = 32;
export const defaultDiagnosticFactStringLengthLimit = 256;

export interface DiagnosticFactOptions {
  readonly maxFactCount?: number;
  readonly maxStringLength?: number;
}

export interface DiagnosticDescriptor {
  readonly failureKind: FailureKind;
  readonly failureSource: FailureSource;
  readonly severity: FailureSeverity;
  readonly recovery: RecoveryDisposition;
  readonly retryable: boolean;
  readonly userCorrectable: boolean;
  readonly action?: RecoveryAction;
  readonly messageKey?: string;
  readonly facts?: DiagnosticFacts;
}

export function diagnosticDescriptor(input: {
  readonly failureKind: FailureKind;
  readonly failureSource: FailureSource;
  readonly severity: FailureSeverity;
  readonly recovery: RecoveryDisposition;
  readonly retryable?: boolean;
  readonly userCorrectable?: boolean;
  readonly action?: RecoveryAction;
  readonly messageKey?: string;
  readonly facts?: DiagnosticFacts;
}): DiagnosticDescriptor {
  assertKnownValue("failure kind", input.failureKind, failureKinds);
  assertKnownValue("failure source", input.failureSource, failureSources);
  assertKnownValue("failure severity", input.severity, failureSeverities);
  assertKnownValue("recovery disposition", input.recovery, recoveryDispositions);

  if (input.action !== undefined) {
    assertKnownValue("recovery action", input.action, recoveryActions);
  }

  if (input.recovery === "automation_retryable" && input.retryable === false) {
    throw new TypeError("automation_retryable diagnostics must be retryable.");
  }

  if (input.recovery === "user_correctable" && input.userCorrectable === false) {
    throw new TypeError("user_correctable diagnostics must be user-correctable.");
  }

  return {
    failureKind: input.failureKind,
    failureSource: input.failureSource,
    severity: input.severity,
    recovery: input.recovery,
    retryable: input.retryable ?? (input.recovery === "automation_retryable"),
    userCorrectable: input.userCorrectable ?? (input.recovery === "user_correctable"),
    ...(input.action === undefined ? {} : { action: input.action }),
    ...(input.messageKey === undefined ? {} : { messageKey: requireNonEmpty(input.messageKey, "diagnostic messageKey") }),
    ...(input.facts === undefined ? {} : { facts: copyDiagnosticFacts(input.facts) }),
  };
}

export function isRetryableDiagnostic(descriptor: DiagnosticDescriptor): boolean {
  return descriptor.retryable;
}

export function isUserCorrectableDiagnostic(descriptor: DiagnosticDescriptor): boolean {
  return descriptor.userCorrectable;
}

export function copyDiagnosticFacts<TFacts extends DiagnosticFacts>(
  facts: TFacts,
  options: DiagnosticFactOptions = {},
): TFacts {
  const maxFactCount = options.maxFactCount ?? defaultDiagnosticFactCountLimit;
  const maxStringLength = options.maxStringLength ?? defaultDiagnosticFactStringLengthLimit;
  assertPositiveInteger("diagnostic fact count limit", maxFactCount);
  assertPositiveInteger("diagnostic fact string length limit", maxStringLength);

  const entries = Object.entries(facts);
  if (entries.length > maxFactCount) {
    throw new TypeError(`diagnostic facts must contain no more than ${maxFactCount} entries.`);
  }

  const copied: Record<string, DiagnosticFactValue> = {};

  for (const [key, value] of entries) {
    requireNonEmpty(key, "diagnostic fact key");
    copied[key] = copyDiagnosticFactValue(value, key, maxStringLength);
  }

  return copied as TFacts;
}

function copyDiagnosticFactValue(value: DiagnosticFactValue, key: string, maxStringLength: number): DiagnosticFactValue {
  if (typeof value === "number" && !Number.isFinite(value)) {
    throw new TypeError(`diagnostic fact "${key}" must be a finite number.`);
  }

  if (typeof value === "string" && value.length > maxStringLength) {
    throw new TypeError(`diagnostic fact "${key}" must be ${maxStringLength} characters or fewer.`);
  }

  return value;
}

function assertKnownValue<const TValues extends readonly string[]>(label: string, value: string, values: TValues): void {
  if (!values.includes(value)) {
    throw new TypeError(`${label} must be one of: ${values.join(", ")}.`);
  }
}

function requireNonEmpty(value: string, label: string): string {
  if (value.trim().length === 0) {
    throw new TypeError(`${label} must not be empty.`);
  }

  return value;
}

function assertPositiveInteger(label: string, value: number): void {
  if (!Number.isInteger(value) || value <= 0) {
    throw new TypeError(`${label} must be a positive integer.`);
  }
}
