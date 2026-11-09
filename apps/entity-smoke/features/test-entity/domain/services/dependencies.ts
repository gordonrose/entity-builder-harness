import type { RecordLifecyclePolicy } from "@kanbien/core/persistence";
import type { Clock, UuidGenerator } from "@kanbien/core/shared";
import type { TestEntityRepository } from "../../persistence/repository";
export interface TestEntityServiceDependencies { readonly repository: TestEntityRepository; readonly clock: Clock; readonly uuidGenerator: UuidGenerator; readonly lifecyclePolicy: RecordLifecyclePolicy; }
