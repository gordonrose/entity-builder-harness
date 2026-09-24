import type { OutboxEntry, OutboxEntryId } from "@kanbien/core/persistence";
import {
  queueIdempotencyKey,
  queueMessage,
  queueMessageId,
  queueMessageType,
  queueMessageVersion,
  type Queue,
  type QueueMessage,
} from "@kanbien/core/queues";
import {
  isoDateTimeFromDate,
  type Clock,
  type ISODateTime,
  type Result,
} from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError } from "./errors";
import {
  recordPlatformPersistenceObservation,
  type PlatformPersistenceObserver,
  type PlatformPersistenceTransition,
  type PlatformPersistenceTransitionOutcome,
} from "./observability";
import type { PlatformOutboxStore } from "./outbox";
import type {
  PlatformOutboxRecord,
  PlatformPersistenceLeaseOwner,
} from "./types";

/** The only queue payload required for the first durable-outbox relay. */
export type PlatformOutboxQueuePayload = {
  readonly outboxEntryId: string;
};

export type PlatformOutboxRelayRunResult =
  | { readonly status: "idle" }
  | { readonly status: "contended"; readonly outboxEntryId: OutboxEntryId }
  | {
      readonly status: "published";
      readonly outboxEntryId: OutboxEntryId;
      readonly attempt: number;
      readonly fence: number;
    }
  | {
      readonly status: "queue-send-failed";
      readonly outboxEntryId: OutboxEntryId;
      readonly attempt: number;
      readonly fence: number;
    }
  | {
      readonly status: "publish-marker-failed";
      readonly outboxEntryId: OutboxEntryId;
      readonly attempt: number;
      readonly fence: number;
    };

export interface PlatformOutboxRelay {
  runOnce(): Promise<Result<PlatformOutboxRelayRunResult, PlatformPersistenceError>>;
}

export interface PlatformOutboxRelayOptions {
  readonly outbox: PlatformOutboxStore;
  readonly queue: Queue<PlatformOutboxQueuePayload>;
  readonly owner: PlatformPersistenceLeaseOwner;
  readonly leaseDurationMs: number;
  readonly clock: Clock;
  readonly observer?: PlatformPersistenceObserver;
}

/**
 * Claims at most one due entry, sends its minimal queue envelope, and marks it
 * published only after the queue accepts that envelope. A failed send leaves
 * the durable entry leased until expiry, when a later relay may retry it.
 */
export function createPlatformOutboxRelay(
  options: PlatformOutboxRelayOptions,
): PlatformOutboxRelay {
  return {
    async runOnce() {
      const claimedAt = isoDateTimeFromDate(options.clock.now());
      const due = await options.outbox.listDeliverable({ asOf: claimedAt, limit: 1 });
      if (!due.ok) {
        recordRelayObservation(options, "outbox.delivery.lookup_failed", "failed", due.error);
        return due;
      }

      const candidate = due.value[0];
      if (candidate === undefined) {
        return { ok: true, value: { status: "idle" } };
      }

      const claim = await options.outbox.claim({
        id: candidate.entry.id,
        owner: options.owner,
        acquiredAt: claimedAt,
        leaseDurationMs: options.leaseDurationMs,
      });
      if (!claim.ok) {
        recordRelayObservation(options, "outbox.claim_failed", "failed", claim.error, candidate);
        return claim;
      }

      if (claim.value.disposition === "already-published") {
        return { ok: true, value: { status: "idle" } };
      }

      if (claim.value.disposition === "lease-active") {
        recordRelayObservation(options, "outbox.lease_active", "rejected", undefined, claim.value.record);
        return {
          ok: true,
          value: { status: "contended", outboxEntryId: claim.value.record.entry.id },
        };
      }

      const record = claim.value.record;
      const lease = record.lease;
      if (lease === undefined) {
        recordRelayObservation(options, "outbox.claim_failed", "failed", undefined, record);
        return invalidRelayState("A claimed outbox record must have a lease.");
      }

      recordRelayObservation(options, "outbox.claimed", "succeeded", undefined, record);

      const envelope = platformOutboxQueueMessage(record.entry, claimedAt);
      if (!envelope.ok) {
        recordRelayObservation(options, "outbox.envelope_rejected", "rejected", envelope.error, record);
        return envelope;
      }

      const sent = await options.queue.send(envelope.value);
      if (!sent.ok) {
        recordRelayObservation(options, "outbox.queue_send_failed", "failed", sent.error, record);
        return {
          ok: true,
          value: relayResult("queue-send-failed", record),
        };
      }

      const publishedAt = isoDateTimeFromDate(options.clock.now());
      const markedPublished = await options.outbox.markPublished({
        id: record.entry.id,
        fence: lease.fence,
        publishedAt,
      });
      if (!markedPublished.ok) {
        recordRelayObservation(options, "outbox.publish_marker_failed", "failed", markedPublished.error, record);
        return {
          ok: true,
          value: relayResult("publish-marker-failed", record),
        };
      }

      recordRelayObservation(options, "outbox.published", "succeeded", undefined, record);

      return {
        ok: true,
        value: relayResult("published", record),
      };
    },
  };
}

function recordRelayObservation( // Project relay-local state into the no-payload persistence observability port.
  options: PlatformOutboxRelayOptions, // Receive the selected relay composition and its optional observer.
  transition: PlatformPersistenceTransition, // Name the exact stable relay transition that occurred.
  outcome: PlatformPersistenceTransitionOutcome, // Preserve the bounded transition outcome.
  error?: unknown, // Let the observer reduce any store or queue failure to a safe error class.
  record?: PlatformOutboxRecord, // Use only a present Core correlation reference; never pass the outbox ID, subject, tenant, or message data.
): void { // Keep the relay's decision path independent of telemetry delivery.
  recordPlatformPersistenceObservation(options.observer, { // Delegate through the persistence-owned best-effort boundary.
    transition, // Preserve the fixed transition identity.
    outcome, // Preserve the reviewed logical transition outcome.
    ...(record?.entry.correlationId === undefined ? {} : { correlationId: record.entry.correlationId }), // Carry a safe cross-system link only when the immutable entry already contains one.
    ...(error === undefined ? {} : { error }), // Let the selected implementation emit only its bounded error classification.
  }); // Finish the no-throw observation request.
}

export function platformOutboxQueueMessage(
  entry: OutboxEntry,
  enqueuedAt: ISODateTime,
): Result<QueueMessage<PlatformOutboxQueuePayload>, PlatformPersistenceError> {
  const messageType = queueMessageType(String(entry.messageType));
  const messageVersion = queueMessageVersion(Number(entry.messageVersion));
  if (!messageType.ok || !messageVersion.ok) {
    return invalidQueueMapping("The outbox message type or version is not a valid queue envelope.");
  }

  return {
    ok: true,
    value: queueMessage({
      id: queueMessageId(String(entry.id)),
      type: messageType.value,
      version: messageVersion.value,
      enqueuedAt,
      ...(entry.tenantId === undefined ? {} : { tenantId: entry.tenantId }),
      ...(entry.correlationId === undefined ? {} : { correlationId: entry.correlationId }),
      ...(entry.causationId === undefined ? {} : { causationId: entry.causationId }),
      idempotencyKey: queueIdempotencyKey(String(entry.id)),
      payload: { outboxEntryId: String(entry.id) },
    }),
  };
}

function relayResult(
  status: Exclude<PlatformOutboxRelayRunResult["status"], "idle" | "contended">,
  record: PlatformOutboxRecord,
): Exclude<PlatformOutboxRelayRunResult, { readonly status: "idle" } | { readonly status: "contended" }> {
  if (record.lease === undefined) {
    throw new TypeError("A relay result requires a claimed outbox record.");
  }

  return {
    status,
    outboxEntryId: record.entry.id,
    attempt: Number(record.attempt),
    fence: Number(record.lease.fence),
  };
}

function invalidRelayState(
  defaultMessage: string,
): Result<never, PlatformPersistenceError> {
  return {
    ok: false,
    error: platformPersistenceError({
      code: "PLATFORM_PERSISTENCE_OUTBOX_NOT_LEASED",
      defaultMessage,
      messageKey: "platform.persistence.relay.outbox.not_leased",
    }),
  };
}

function invalidQueueMapping(
  defaultMessage: string,
): Result<never, PlatformPersistenceError> {
  return {
    ok: false,
    error: platformPersistenceError({
      code: "PLATFORM_PERSISTENCE_QUEUE_MAPPING_INVALID",
      defaultMessage,
      messageKey: "platform.persistence.relay.queue_mapping.invalid",
    }),
  };
}
