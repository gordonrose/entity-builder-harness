import type { RecordLifecyclePolicy } from "@kanbien/core/persistence";
import type { Clock, Result, UuidGenerator } from "@kanbien/core/shared";
import type { PlatformJobName } from "@kanbien/platform-contracts";
import type { PlatformScheduleStore } from "@kanbien/platform-persistence";
import type { TestEntityRepository } from "../../persistence/repository";
import type { TestEntityError } from "../../contract/errors";

/** The durable app supplies this; local feature tests can stay storage-only. */
export interface TestEntityExpiredPurgeReminder {
  readonly jobName: PlatformJobName;
  readonly store: Pick<PlatformScheduleStore, "create">;
}

/** Both participants belong to the same transaction; repository reads lock the selected row. */
export interface TestEntityDeletionScope {
  readonly repository: TestEntityRepository;
  readonly schedules: Pick<PlatformScheduleStore, "create">;
}

export interface TestEntityDeletionTransaction {
  run<T>(operation: (scope: TestEntityDeletionScope) => Promise<Result<T, TestEntityError>>): Promise<Result<T, TestEntityError>>;
}

export interface TestEntityServiceDependencies {
  readonly repository: TestEntityRepository;
  readonly clock: Clock;
  readonly uuidGenerator: UuidGenerator;
  readonly lifecyclePolicy: RecordLifecyclePolicy;
  readonly expiredPurgeReminder?: TestEntityExpiredPurgeReminder;
  readonly deletionTransaction?: TestEntityDeletionTransaction;
}
