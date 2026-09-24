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
  if (!Number.isInteger(input.durationMs) || input.durationMs <= 0) {
    return err(
      platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_INVALID_LEASE",
        defaultMessage: "Persistence lease duration must be a positive integer number of milliseconds.",
        messageKey: "platform.persistence.lease.duration.invalid",
        params: { durationMs: String(input.durationMs) },
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
      }),
    );
  }

  return platformPersistenceLease({
    owner: input.owner,
    fence: fence.value,
    attempt: attempt.value,
    acquiredAt: input.acquiredAt,
    expiresAt: isoDateTimeFromDate(new Date(Date.parse(input.acquiredAt) + input.durationMs)),
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
