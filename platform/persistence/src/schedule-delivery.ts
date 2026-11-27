import type { OutboxEntry } from "@kanbien/core/persistence";
import { numberConfigValue, type ConfigSource } from "@kanbien/core/config";
import { isoDateTimeFromDate, type Clock, type Result } from "@kanbien/core/shared";
import type { PlatformPersistenceError } from "./errors";
import type { PlatformSchedule, PlatformScheduleStore } from "./scheduling";
import {
  capturePlatformPersistenceDiagnostic, observePlatformPersistenceDiagnostic,
  persistenceScheduleDeliveryBoundaryDiagnosticRecord, persistenceScheduleDeliveryConfigurationDiagnosticRecord,
  type PersistenceScheduleDeliveryBoundaryDetail, type PersistenceScheduleDeliveryConfigurationDetail,
  type PlatformPersistenceDiagnosticOptions,
} from "./diagnostics";

/** Releases due one-off schedules to the durable outbox without deciding when to run. */
export interface PlatformScheduleDelivery {
  runOnce(invocation?: PlatformScheduleDeliveryInvocation): Promise<Result<PlatformScheduleDeliveryRunResult, PlatformPersistenceError>>;
}

export interface PlatformScheduleDeliveryInvocation {
  /** Checked before selection and each handover; cannot interrupt an in-flight write. */
  readonly shouldContinue?: () => boolean;
}

export interface PlatformScheduleDeliveryRunResult {
  readonly inspected: number;
  readonly deliveryCreated: number;
  readonly deliveryAlreadyCreated: number;
  readonly notDue: number;
  /** Present only when unavailable jobs were retained in a blocked state. */
  readonly blocked?: number;
  /** Present only when the caller stopped this pass before all selected work. */
  readonly stopped?: true;
}

/** The caller owns the registered-job-specific shape of the durable outbox entry. */
export type PlatformScheduleOutboxEntryFactory = (schedule: PlatformSchedule) => OutboxEntry | null;

export interface PlatformScheduleDeliveryOptions extends PlatformPersistenceDiagnosticOptions {
  readonly clock: Clock;
  readonly scheduleStore: PlatformScheduleStore;
  readonly createOutboxEntry: PlatformScheduleOutboxEntryFactory;
  /** Finite integer 1..100. Omission preserves the established 100-row pass. */
  readonly maximumSchedules?: number;
}

/**
 * Performs one bounded scan. A deployment trigger will decide when to invoke
 * this; keeping it separate makes the operation deterministic and testable.
 */
export function createPlatformScheduleDelivery(
  options: PlatformScheduleDeliveryOptions,
): PlatformScheduleDelivery {
  const submitted = options.maximumSchedules;
  const checked = numberConfigValue({ get: () => submitted === undefined ? 100 : submitted } as ConfigSource, "maximum-schedules");
  const reason: PersistenceScheduleDeliveryConfigurationDetail["reason"] | undefined = !checked.ok
    ? typeof submitted === "number" ? "not-finite" : "wrong-type"
    : !Number.isInteger(checked.value) ? "not-integer" : checked.value < 1 ? "not-positive" : checked.value > 100 ? "too-large" : undefined;
  if (!checked.ok || reason !== undefined) {
    throw Object.assign(new TypeError("Persistence schedule delivery limit is invalid."), {
      diagnosticRecord: capturePlatformPersistenceDiagnostic(() => persistenceScheduleDeliveryConfigurationDiagnosticRecord(reason ?? "wrong-type")),
    });
  }
  const maximumSchedules = checked.value;
  const { clock, scheduleStore, createOutboxEntry } = options;
  return {
    async runOnce(invocation = {}) {
      let inspected = 0;
      let deliveryCreated = 0;
      let deliveryAlreadyCreated = 0;
      let notDue = 0;
      let blocked = 0;
      let boundary: PersistenceScheduleDeliveryBoundaryDetail["boundary"] = "continuation-check";
      let effect: PersistenceScheduleDeliveryBoundaryDetail["effect"] = "handover-not-started";
      const result = (stopped = false) => ({ ok: true as const, value: {
        inspected, deliveryCreated, deliveryAlreadyCreated, notDue,
        ...(blocked > 0 ? { blocked } : {}), ...(stopped ? { stopped: true as const } : {}),
      } });
      const observe = (reason: "threw" | "returned-failure", cause: unknown) => observePlatformPersistenceDiagnostic(options,
        capturePlatformPersistenceDiagnostic(() => persistenceScheduleDeliveryBoundaryDiagnosticRecord({ boundary, reason, effect })), cause);
      try {
        if (invocation.shouldContinue?.() === false) return result(true);
        boundary = "clock";
        const asOf = isoDateTimeFromDate(clock.now());
        boundary = "selection";
        const due = await scheduleStore.listDue({ asOf, limit: maximumSchedules, blockInvalid: true });
        if (!due.ok) { observe("returned-failure", due.error); return due; }
        for (const schedule of due.value) {
          boundary = "continuation-check";
          if (invocation.shouldContinue?.() === false) return result(true);
          boundary = "entry-construction";
          const entry = createOutboxEntry(schedule);
          if (entry === null) {
            boundary = "block-unavailable-job";
            effect = "handover-outcome-unknown";
            const retained = await scheduleStore.blockDue({ scheduleId: schedule.id, asOf });
            if (!retained.ok) { observe("returned-failure", retained.error); return retained; }
            inspected++;
            effect = "handover-success-returned";
            if (retained.value.state === "blocked-job-unavailable") blocked++;
            else if (retained.value.state === "delivery-created") deliveryAlreadyCreated++;
            else notDue++;
            continue;
          }
          boundary = "handover";
          effect = "handover-outcome-unknown";
          const handover = await scheduleStore.handoverDue({ scheduleId: schedule.id, asOf, outboxEntry: entry });
          if (!handover.ok) { observe("returned-failure", handover.error); return handover; }
          inspected++;
          effect = "handover-success-returned";
          if (handover.value.disposition === "outbox-created") deliveryCreated++;
          if (handover.value.disposition === "outbox-already-created") deliveryAlreadyCreated++;
          if (handover.value.disposition === "not-due") notDue++;
          if (handover.value.disposition === "blocked") blocked++;
        }
        return result();
      } catch (cause) { observe("threw", cause); throw cause; }
    },
  };
}
