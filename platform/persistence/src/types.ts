import type { OutboxEntry, OutboxEntryId } from "@kanbien/core/persistence";
import {
  brand,
  err,
  isoDateTimeFromDate,
  ok,
  type Brand,
  type ISODateTime,
  type Result,
} from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError } from "./errors";
import { validatePersistenceLeaseDuration } from "./leasing/index";
import { persistenceLocalRejectionDiagnostic, persistenceLocalRejectionDiagnosticRecord } from "./diagnostics";

export type PlatformPersistenceLeaseOwner = Brand<string, "PlatformPersistenceLeaseOwner">;
export type PlatformPersistenceFence = Brand<number, "PlatformPersistenceFence">;
export type PlatformPersistenceAttempt = Brand<number, "PlatformPersistenceAttempt">;
export type PlatformOutboxState = "pending" | "leased" | "published";
export type PlatformProcessingState = "claimed" | "retry-eligible" | "completed";
export type PlatformProcessingOutcome = "succeeded" | "terminal-failure";

export const initialPlatformPersistenceAttempt: PlatformPersistenceAttempt = brand<
  number,
  "PlatformPersistenceAttempt"
>(0);

export interface PlatformPersistenceLease {
  readonly owner: PlatformPersistenceLeaseOwner;
  readonly fence: PlatformPersistenceFence;
  readonly attempt: PlatformPersistenceAttempt;
  readonly acquiredAt: ISODateTime;
  readonly expiresAt: ISODateTime;
}

export interface PlatformOutboxRecord {
  readonly entry: OutboxEntry;
  readonly state: PlatformOutboxState;
  readonly attempt: PlatformPersistenceAttempt;
  readonly lease?: PlatformPersistenceLease;
  readonly publishedAt?: ISODateTime;
}

export interface PlatformProcessingCompletion {
  readonly outcome: PlatformProcessingOutcome;
  readonly completedAt: ISODateTime;
}

export interface PlatformProcessingRecord {
  readonly outboxEntryId: OutboxEntryId;
  readonly state: PlatformProcessingState;
  readonly attempt: PlatformPersistenceAttempt;
  readonly lease?: PlatformPersistenceLease;
  readonly releasedAt?: ISODateTime;
  readonly completion?: PlatformProcessingCompletion;
}

export function platformPersistenceLeaseOwner(
  value: string,
): Result<PlatformPersistenceLeaseOwner, PlatformPersistenceError> {
  if (!leaseOwnerPattern.test(value)) {
    return err(
      platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_INVALID_LEASE",
        defaultMessage: "Persistence lease owner must use lowercase identifier segments.",
        messageKey: "platform.persistence.lease.owner.invalid",
        diagnosticRecord: persistenceLocalRejectionDiagnosticRecord({ operation: "validate-lease", field: "owner", condition: "pattern", phase: "validation", effect: "not-started" }),
      }),
    );
  }

  return ok(brand<string, "PlatformPersistenceLeaseOwner">(value));
}

export function platformPersistenceFence(
  value: number,
): Result<PlatformPersistenceFence, PlatformPersistenceError> {
  if (!Number.isInteger(value) || value <= 0) {
    return err(
      platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_INVALID_LEASE",
        defaultMessage: "Persistence fence must be a positive integer.",
        messageKey: "platform.persistence.lease.fence.invalid",
        params: { fence: String(value) },
        diagnosticRecord: persistenceLocalRejectionDiagnosticRecord({ operation: "validate-lease", field: "fence", condition: !Number.isInteger(value) ? "not-integer" : "not-positive", phase: "validation", effect: "not-started" }),
      }),
    );
  }

  return ok(brand<number, "PlatformPersistenceFence">(value));
}

export function platformPersistenceAttempt(
  value: number,
): Result<PlatformPersistenceAttempt, PlatformPersistenceError> {
  if (!Number.isInteger(value) || value < 0) {
    return err(
      platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_INVALID_LEASE",
        defaultMessage: "Persistence attempt must be a non-negative integer.",
        messageKey: "platform.persistence.lease.attempt.invalid",
        params: { attempt: String(value) },
        diagnosticRecord: persistenceLocalRejectionDiagnosticRecord({ operation: "validate-lease", field: "attempt", condition: !Number.isInteger(value) ? "not-integer" : "negative", phase: "validation", effect: "not-started" }),
      }),
    );
  }

  return ok(brand<number, "PlatformPersistenceAttempt">(value));
}

export function platformPersistenceLease(input: {
  readonly owner: PlatformPersistenceLeaseOwner;
  readonly fence: PlatformPersistenceFence;
  readonly attempt: PlatformPersistenceAttempt;
  readonly acquiredAt: ISODateTime;
  readonly expiresAt: ISODateTime;
}): Result<PlatformPersistenceLease, PlatformPersistenceError> {
  if (Date.parse(input.expiresAt) <= Date.parse(input.acquiredAt)) {
    return err(
      platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_INVALID_LEASE",
        defaultMessage: "Persistence lease expiry must be after its acquisition time.",
        messageKey: "platform.persistence.lease.expiry.invalid",
        diagnosticRecord: persistenceLocalRejectionDiagnosticRecord({ operation: "validate-lease", field: "expiry", condition: "not-after-acquisition", phase: "validation", effect: "not-started" }),
      }),
    );
  }

  return ok({ ...input });
}

export function nextPlatformPersistenceLease(input: {
  readonly owner: PlatformPersistenceLeaseOwner;
  readonly priorLease?: PlatformPersistenceLease;
  readonly priorAttempt: PlatformPersistenceAttempt;
  readonly acquiredAt: ISODateTime;
  readonly durationMs: number;
}): Result<PlatformPersistenceLease, PlatformPersistenceError> {
  const suppliedDuration = input.durationMs;
  const duration = validatePersistenceLeaseDuration(suppliedDuration);
  if (!duration.ok) {
    return err(
      platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_INVALID_LEASE",
        defaultMessage: "Persistence lease duration must be a positive integer number of milliseconds.",
        messageKey: "platform.persistence.lease.duration.invalid",
        params: { durationMs: typeof suppliedDuration === "number" ? String(suppliedDuration) : "invalid" },
        diagnosticRecord: persistenceLocalRejectionDiagnosticRecord({ operation: "validate-lease", field: "duration", condition: duration.error.reason === "not-positive" ? "not-positive" : "not-integer", phase: "validation", effect: "not-started" }),
      }),
    );
  }

  const fence = platformPersistenceFence((input.priorLease === undefined ? 0 : Number(input.priorLease.fence)) + 1);
  const attempt = platformPersistenceAttempt(Number(input.priorAttempt) + 1);
  if (!fence.ok || !attempt.ok) {
    return err(
      platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_INVALID_LEASE",
        defaultMessage: "Persistence lease sequence could not advance.",
        messageKey: "platform.persistence.lease.sequence.invalid",
        diagnosticRecord: persistenceLocalRejectionDiagnosticRecord({ operation: "validate-lease", field: "sequence", condition: "cannot-advance", phase: "validation", effect: "not-started" }),
        relatedDiagnosticRecords: [...(fence.ok || fence.error.diagnosticRecord === undefined ? [] : [fence.error.diagnosticRecord]),
          ...(attempt.ok || attempt.error.diagnosticRecord === undefined ? [] : [attempt.error.diagnosticRecord])],
        relatedDiagnosticDefinitions: [persistenceLocalRejectionDiagnostic],
      }),
    );
  }

  return platformPersistenceLease({
    owner: input.owner,
    fence: fence.value,
    attempt: attempt.value,
    acquiredAt: input.acquiredAt,
    expiresAt: isoDateTimeFromDate(new Date(Date.parse(input.acquiredAt) + duration.value)),
  });
}

export function platformOutboxRecord(input: {
  readonly entry: OutboxEntry;
  readonly state?: PlatformOutboxState;
  readonly attempt?: PlatformPersistenceAttempt;
  readonly lease?: PlatformPersistenceLease;
  readonly publishedAt?: ISODateTime;
}): PlatformOutboxRecord {
  return {
    entry: { ...input.entry, subject: { ...input.entry.subject } },
    state: input.state ?? "pending",
    attempt: input.attempt ?? initialPlatformPersistenceAttempt,
    ...(input.lease === undefined ? {} : { lease: { ...input.lease } }),
    ...(input.publishedAt === undefined ? {} : { publishedAt: input.publishedAt }),
  };
}

export function platformProcessingRecord(input: {
  readonly outboxEntryId: OutboxEntryId;
  readonly state: PlatformProcessingState;
  readonly attempt: PlatformPersistenceAttempt;
  readonly lease?: PlatformPersistenceLease;
  readonly releasedAt?: ISODateTime;
  readonly completion?: PlatformProcessingCompletion;
}): PlatformProcessingRecord {
  return {
    outboxEntryId: input.outboxEntryId,
    state: input.state,
    attempt: input.attempt,
    ...(input.lease === undefined ? {} : { lease: { ...input.lease } }),
    ...(input.releasedAt === undefined ? {} : { releasedAt: input.releasedAt }),
    ...(input.completion === undefined ? {} : { completion: { ...input.completion } }),
  };
}

export function platformLeaseExpired(lease: PlatformPersistenceLease, asOf: ISODateTime): boolean {
  return Date.parse(lease.expiresAt) <= Date.parse(asOf);
}

const leaseOwnerPattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)*$/;
