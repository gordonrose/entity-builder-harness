import type { RecordLifecyclePolicy } from "@kanbien/core/persistence";
import type { Clock, UuidGenerator } from "@kanbien/core/shared";
import type { PlatformJobName } from "@kanbien/platform-contracts";
import type { PlatformScheduleStore } from "@kanbien/platform-persistence";
import type { TestEntityRepository } from "../../persistence/repository";

/** The durable app supplies this; local feature tests can stay storage-only. */
export interface TestEntityExpiredPurgeReminder {
  readonly jobName: PlatformJobName;
  readonly store: PlatformScheduleStore;
}

export interface TestEntityServiceDependencies {
  readonly repository: TestEntityRepository;
  readonly clock: Clock;
  readonly uuidGenerator: UuidGenerator;
  readonly lifecyclePolicy: RecordLifecyclePolicy;
  readonly expiredPurgeReminder?: TestEntityExpiredPurgeReminder;
}
