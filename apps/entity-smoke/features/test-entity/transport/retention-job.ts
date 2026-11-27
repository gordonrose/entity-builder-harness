import type { QueueMessage, QueueMessageType } from "@kanbien/core/queues";
import { fixedClock, isoDateTimeFromDate } from "@kanbien/core/shared";
import type { PlatformJobName } from "@kanbien/platform-contracts";
import { loadPlatformScheduleDelivery, type PlatformOutboxStore, type PlatformScheduleStore } from "@kanbien/platform-persistence";
import { testEntityRetentionRejected } from "../contract/errors";
import type { TestEntityServiceDependencies } from "../domain/services/dependencies";
import { purgeExpiredTestEntityService } from "../domain/services/purge-expired-test-entities";

export interface TestEntityRetentionDelivery {
  readonly outbox: Pick<PlatformOutboxStore, "get">;
  readonly schedules: Pick<PlatformScheduleStore, "get">;
}

/** Resolve only trusted durable metadata; queue data never chooses an entity directly. */
export async function handleTestEntityRetentionJob(message: QueueMessage, services: TestEntityServiceDependencies,
  delivery: TestEntityRetentionDelivery | undefined, jobName: PlatformJobName, messageType: QueueMessageType): Promise<void> {
  if (delivery === undefined) throw testEntityRetentionRejected("delivery", "missing");
  const asOf = new Date(services.clock.now().getTime());
  const deliveryReference = await loadPlatformScheduleDelivery(message, { ...delivery, jobName, messageType, asOf: isoDateTimeFromDate(asOf) });
  if (!deliveryReference.ok) throw deliveryReference.error;
  const result = await purgeExpiredTestEntityService(deliveryReference.value, { ...services, clock: fixedClock(asOf) });
  if (!result.ok) throw result.error;
}
