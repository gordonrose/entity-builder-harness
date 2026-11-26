import type { OutboxEntry } from "@kanbien/core/persistence";
import { isoDateTimeFromDate, type Clock, type Result } from "@kanbien/core/shared";
import type { PlatformPersistenceError } from "./errors";
import type { PlatformSchedule, PlatformScheduleStore } from "./scheduling";

/** Releases due one-off schedules to the durable outbox without deciding when to run. */
export interface PlatformScheduleDelivery {
  runOnce(): Promise<Result<PlatformScheduleDeliveryRunResult, PlatformPersistenceError>>;
}

export interface PlatformScheduleDeliveryRunResult {
  readonly inspected: number;
  readonly deliveryCreated: number;
  readonly deliveryAlreadyCreated: number;
  readonly notDue: number;
}

/** The caller owns the registered-job-specific shape of the durable outbox entry. */
export type PlatformScheduleOutboxEntryFactory = (schedule: PlatformSchedule) => OutboxEntry;

export interface PlatformScheduleDeliveryOptions {
  readonly clock: Clock;
  readonly scheduleStore: PlatformScheduleStore;
  readonly createOutboxEntry: PlatformScheduleOutboxEntryFactory;
}

/**
 * Performs one bounded scan. A deployment trigger will decide when to invoke
 * this; keeping it separate makes the operation deterministic and testable.
 */
export function createPlatformScheduleDelivery(
  options: PlatformScheduleDeliveryOptions,
): PlatformScheduleDelivery {
  return {
    async runOnce() {
      const asOf = isoDateTimeFromDate(options.clock.now());
      const due = await options.scheduleStore.listDue({ asOf, limit: 100 });
      if (!due.ok) return due;

      let deliveryCreated = 0;
      let deliveryAlreadyCreated = 0;
      let notDue = 0;

      for (const schedule of due.value) {
        const handover = await options.scheduleStore.handoverDue({
          scheduleId: schedule.id,
          asOf,
          outboxEntry: options.createOutboxEntry(schedule),
        });
        if (!handover.ok) return handover;

        if (handover.value.disposition === "outbox-created") deliveryCreated++;
        if (handover.value.disposition === "outbox-already-created") deliveryAlreadyCreated++;
        if (handover.value.disposition === "not-due") notDue++;
      }

      return {
        ok: true,
        value: { inspected: due.value.length, deliveryCreated, deliveryAlreadyCreated, notDue },
      };
    },
  };
}
