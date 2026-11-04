import {
  brand,
  err,
  ok,
  type Brand,
  type ISODateTime,
  type Result,
} from "../shared/index";
import { persistenceError, type PersistenceError } from "./errors";
import { corePersistenceValidationRecord, type CorePersistenceValidationDetail } from "./diagnostics";

/** A product record is available to ordinary reads unless it is logically deleted. */
export type RecordLifecycleState = "active" | "deleted";

/** A product-owned reference to its reviewed retention, erasure, and legal-hold policy. */
export type RecordRetentionPolicyReference = Brand<string, "RecordRetentionPolicyReference">;

/**
 * The small, portable policy declaration required before a product can use
 * logical deletion. The policy deliberately names a reference rather than a
 * universal retention period: legal, privacy, and recovery requirements are
 * product and data-classification decisions.
 */
export interface RecordLifecyclePolicy {
  readonly recoveryWindowMs: number;
  readonly retentionPolicy: RecordRetentionPolicyReference;
  readonly legalHoldCheckRequired: true;
}

/**
 * Lifecycle facts held beside a product row. `deleted` is reversible only
 * until `restoreEligibleUntil`; immutable change history belongs in
 * `RecordChange`, not this current-state projection.
 */
export type RecordLifecycle =
  | { readonly state: "active" }
  | {
      readonly state: "deleted";
      readonly deletedAt: ISODateTime;
      readonly restoreEligibleUntil: ISODateTime;
      /** The reviewed policy that governed this particular deletion. */
      readonly retentionPolicy: RecordRetentionPolicyReference;
    };

/** A purge decision is an explanation; this Core contract never deletes data. */
export type RecordPurgeEligibility =
  | "not-deleted"
  | "within-recovery-window"
  | "retention-not-met"
  | "legal-hold"
  | "eligible";

/** Make the one active lifecycle state explicit in product repositories. */
export function activeRecordLifecycle(): RecordLifecycle {
  return { state: "active" };
}

/** Validate a product-owned lifecycle policy without deciding its legal retention duration. */
export function recordLifecyclePolicy(input: {
  readonly recoveryWindowMs: number;
  readonly retentionPolicy: RecordRetentionPolicyReference;
  readonly legalHoldCheckRequired: true;
}): Result<RecordLifecyclePolicy, PersistenceError> {
  if (!Number.isSafeInteger(input.recoveryWindowMs)) {
    return invalidLifecycle("Recovery window must be a positive whole number of milliseconds.", "recovery_window.invalid", "lifecycle-policy", "recovery-window", "not-safe-integer");
  }
  if (input.recoveryWindowMs <= 0) {
    return invalidLifecycle("Recovery window must be a positive whole number of milliseconds.", "recovery_window.invalid", "lifecycle-policy", "recovery-window", "not-positive");
  }

  if (input.legalHoldCheckRequired !== true) {
    return invalidLifecycle("Logical deletion policy must require a legal-hold check before purge.", "legal_hold_check.required", "lifecycle-policy", "legal-hold-check", "required");
  }

  return ok({
    recoveryWindowMs: input.recoveryWindowMs,
    retentionPolicy: input.retentionPolicy,
    legalHoldCheckRequired: true,
  });
}

/** Brand a reviewed policy reference; it is a name, never a free-form retention rule. */
export function recordRetentionPolicyReference(value: string): Result<RecordRetentionPolicyReference, PersistenceError> {
  if (!recordRetentionPolicyPattern.test(value)) {
    return invalidLifecycle("Retention policy reference must use lowercase identifier segments.", "retention_policy.invalid", "retention-reference", "retention-policy", "invalid-format");
  }

  return ok(brand<string, "RecordRetentionPolicyReference">(value));
}

/** Logically delete an active record and calculate its policy-governed restore boundary. */
export function logicallyDeleteRecord(input: {
  readonly current: RecordLifecycle;
  readonly deletedAt: ISODateTime;
  readonly policy: RecordLifecyclePolicy;
}): Result<RecordLifecycle, PersistenceError> {
  if (input.current.state === "deleted") {
    return invalidLifecycle("An already deleted record cannot be deleted again.", "already_deleted", "delete", "state", "already-deleted");
  }

  const deletedAtMs = Date.parse(input.deletedAt);
  const restoreEligibleUntil = new Date(deletedAtMs + input.policy.recoveryWindowMs);
  if (!Number.isFinite(deletedAtMs)) {
    return invalidLifecycle("Deletion time and recovery window must form a valid restore boundary.", "restore_boundary.invalid", "delete", "deleted-at", "invalid-time");
  }
  if (Number.isNaN(restoreEligibleUntil.getTime())) {
    return invalidLifecycle("Deletion time and recovery window must form a valid restore boundary.", "restore_boundary.invalid", "delete", "restore-boundary", "unrepresentable-boundary");
  }

  return ok({
    state: "deleted",
    deletedAt: input.deletedAt,
    restoreEligibleUntil: brand<string, "ISODateTime">(restoreEligibleUntil.toISOString()),
    retentionPolicy: input.policy.retentionPolicy,
  });
}

/** Restore only a logically deleted record whose policy recovery window has not elapsed. */
export function restoreLogicallyDeletedRecord(input: {
  readonly current: RecordLifecycle;
  readonly restoredAt: ISODateTime;
}): Result<RecordLifecycle, PersistenceError> {
  if (input.current.state !== "deleted") {
    return err(persistenceError({
      code: "PERSISTENCE_RECORD_NOT_DELETED",
      defaultMessage: "Only a logically deleted record can be restored.",
      messageKey: "persistence.lifecycle.restore.not_deleted",
      diagnosticRecord: corePersistenceValidationRecord({ operation: "restore", field: "state", reason: "not-deleted" }),
    }));
  }

  if (Date.parse(input.restoredAt) > Date.parse(input.current.restoreEligibleUntil)) {
    return err(persistenceError({
      code: "PERSISTENCE_RESTORE_WINDOW_EXPIRED",
      defaultMessage: "The configured recovery window has expired.",
      messageKey: "persistence.lifecycle.restore.window_expired",
      diagnosticRecord: corePersistenceValidationRecord({ operation: "restore", field: "restore-time", reason: "window-expired" }),
    }));
  }

  return ok(activeRecordLifecycle());
}

/** Tell a repository/query layer whether ordinary reads should include the current row. */
export function isRecordLifecycleActive(value: RecordLifecycle): boolean {
  return value.state === "active";
}

/**
 * Determine whether a product may begin its separately governed purge or
 * anonymisation operation. This helper never removes a row, bypasses a legal
 * hold, or treats a provider TTL as a retention decision.
 */
export function recordPurgeEligibility(input: {
  readonly current: RecordLifecycle;
  readonly asOf: ISODateTime;
  readonly retentionSatisfied: boolean;
  readonly legalHold: boolean;
}): RecordPurgeEligibility {
  if (input.current.state !== "deleted") return "not-deleted";
  if (Date.parse(input.asOf) <= Date.parse(input.current.restoreEligibleUntil)) return "within-recovery-window";
  if (input.legalHold) return "legal-hold";
  if (!input.retentionSatisfied) return "retention-not-met";
  return "eligible";
}

const recordRetentionPolicyPattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*$/;

function invalidLifecycle(defaultMessage: string, reason: string, operation: CorePersistenceValidationDetail["operation"], field: CorePersistenceValidationDetail["field"], predicate: CorePersistenceValidationDetail["reason"]): Result<never, PersistenceError> {
  return err(persistenceError({
    code: "PERSISTENCE_INVALID_RECORD_LIFECYCLE",
    defaultMessage,
    messageKey: "persistence.lifecycle.invalid",
    params: { reason },
    diagnosticRecord: corePersistenceValidationRecord({ operation, field, reason: predicate }),
  }));
}
