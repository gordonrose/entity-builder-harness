import { numberConfigValue, type ConfigSource } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import type { PlatformPersistenceError } from "./errors";
import type { PlatformOutboxRelay, PlatformOutboxRelayRunResult } from "./relay";
import type { PlatformScheduleDelivery, PlatformScheduleDeliveryRunResult } from "./schedule-delivery";
import {
  capturePlatformPersistenceDiagnostic,
  observePlatformPersistenceDiagnostic,
  persistenceScheduleDispatchBoundaryDiagnosticRecord,
  persistenceScheduleDispatchConfigurationDiagnosticRecord,
  type PersistenceScheduleDispatchBoundaryDetail,
  type PersistenceScheduleDispatchConfigurationDetail,
  type PlatformPersistenceDiagnosticOptions,
} from "./diagnostics";

export interface PlatformScheduleDispatchOptions extends PlatformPersistenceDiagnosticOptions {
  readonly delivery: PlatformScheduleDelivery;
  readonly relay: PlatformOutboxRelay;
  /** Finite integer from 1 through 100; captured once during construction. */
  readonly maximumRelayAttempts: number;
}

export interface PlatformScheduleDispatchInvocation {
  /** Cooperative stop between calls, not interruption of in-flight work. */
  readonly shouldContinue?: () => boolean;
  /** Optional earlier due-phase stop, reserving time to relay existing backlog. */
  readonly shouldContinueDelivery?: () => boolean;
}

export interface PlatformScheduleDispatchRunResult {
  /** Null means stopping was requested before due delivery started. */
  readonly delivery: PlatformScheduleDeliveryRunResult | null;
  readonly relayAttempts: number;
  readonly published: number;
  readonly stopReason: Exclude<PlatformOutboxRelayRunResult["status"], "published"> | "requested-stop" | "attempt-limit";
}

export interface PlatformScheduleDispatcher {
  runOnce(invocation?: PlatformScheduleDispatchInvocation): Promise<Result<PlatformScheduleDispatchRunResult, PlatformPersistenceError>>;
}

/**
 * One existing due pass, then a bounded relay pass, including old pending work.
 * Fail-fast on dependency errors; already committed handovers/sends are not undone.
 * This does not install a timer, execute jobs, or enforce dependency timeouts.
 */
export function createPlatformScheduleDispatcher(options: PlatformScheduleDispatchOptions): PlatformScheduleDispatcher {
  const submitted = options.maximumRelayAttempts;
  const number = numberConfigValue({ get: () => submitted } as ConfigSource, "maximum-relay-attempts");
  if (!number.ok) {
    throw invalidConfiguration(submitted === undefined ? "missing" : typeof submitted === "number" ? "not-finite" : "wrong-type");
  }
  const reason: PersistenceScheduleDispatchConfigurationDetail["reason"] | undefined = !Number.isInteger(number.value) ? "not-integer"
    : number.value < 1 ? "not-positive"
    : number.value > 100 ? "too-large"
    : undefined;
  if (reason !== undefined) {
    throw invalidConfiguration(reason);
  }
  // The checked result, not a second read of the caller's setting, owns the bound.
  const maximumRelayAttempts = number.value;
  const { delivery, relay } = options;
  return {
    async runOnce(invocation = {}) {
      let boundary: PersistenceScheduleDispatchBoundaryDetail["boundary"] = "continuation-check";
      let effect: PersistenceScheduleDispatchBoundaryDetail["effect"] = "dispatch-not-started";
      let deliveryResult: PlatformScheduleDeliveryRunResult | null = null;
      let relayAttempts = 0;
      let published = 0;
      const stopped = (stopReason: PlatformScheduleDispatchRunResult["stopReason"]): Result<PlatformScheduleDispatchRunResult, PlatformPersistenceError> =>
        ({ ok: true, value: { delivery: deliveryResult, relayAttempts, published, stopReason } });
      const observeFailure = (reason: PersistenceScheduleDispatchBoundaryDetail["reason"], cause: unknown) =>
        observePlatformPersistenceDiagnostic(options,
          capturePlatformPersistenceDiagnostic(() => persistenceScheduleDispatchBoundaryDiagnosticRecord({ boundary, reason, effect })), cause);
      try {
        if (invocation.shouldContinue?.() === false) return stopped("requested-stop");
        boundary = "due-delivery";
        effect = "due-outcome-unknown";
        const due = await delivery.runOnce({ shouldContinue: () =>
          invocation.shouldContinue?.() !== false && invocation.shouldContinueDelivery?.() !== false });
        if (!due.ok) {
          observeFailure("returned-failure", due.error);
          return due;
        }
        deliveryResult = due.value;
        effect = "due-success-returned";
        while (relayAttempts < maximumRelayAttempts) {
          boundary = "continuation-check";
          if (invocation.shouldContinue?.() === false) return stopped("requested-stop");
          boundary = "outbox-relay";
          effect = "relay-outcome-unknown";
          relayAttempts += 1;
          const sent = await relay.runOnce();
          if (!sent.ok) {
            observeFailure("returned-failure", sent.error);
            return sent;
          }
          if (sent.value.status !== "published") return stopped(sent.value.status);
          published += 1;
          effect = "relay-success-returned";
        }
        return stopped("attempt-limit");
      } catch (cause) {
        observeFailure("threw", cause);
        throw cause;
      }
    },
  };
}

function invalidConfiguration(reason: PersistenceScheduleDispatchConfigurationDetail["reason"]) {
  return Object.assign(new TypeError("Persistence schedule dispatcher relay-attempt limit is invalid."), {
    diagnosticRecord: capturePlatformPersistenceDiagnostic(() => persistenceScheduleDispatchConfigurationDiagnosticRecord(reason)),
  });
}
