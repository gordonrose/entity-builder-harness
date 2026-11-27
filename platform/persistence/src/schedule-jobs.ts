import {
  outboxEntry, outboxEntryId, outboxMessageType, recordId, recordKind, recordReference,
  type OutboxDeliveryPolicy, type OutboxMessageType,
} from "@kanbien/core/persistence";
import { isoDateTimeFromDate, type Clock, type Result } from "@kanbien/core/shared";
import { platformJobName, type PlatformJobRegistration } from "@kanbien/platform-contracts";
import type { PlatformScheduleOutboxEntryFactory } from "./schedule-delivery";
import {
  capturePlatformPersistenceDiagnostic, observePlatformPersistenceDiagnostic,
  persistenceScheduleJobMappingDiagnosticRecord, type PersistenceScheduleJobMappingDetail,
  type PlatformPersistenceDiagnosticOptions,
} from "./diagnostics";

export interface PlatformScheduleJobOutboxOptions extends PlatformPersistenceDiagnosticOptions {
  /** Supply only the registrations selected by this runtime's public app mounts. */
  readonly jobs: readonly Pick<PlatformJobRegistration, "name" | "messageType">[];
  readonly deliveryPolicy: OutboxDeliveryPolicy;
  readonly clock: Clock;
}

/** A reminder owns one stable outbox identity; message type comes from its registered job. */
export function createPlatformScheduleJobOutboxFactory(options: PlatformScheduleJobOutboxOptions): PlatformScheduleOutboxEntryFactory {
  const types = new Map<string, OutboxMessageType>();
  for (const job of options.jobs) {
    const name = platformJobName(job.name);
    if (!name.ok) throw rejected("invalid-job-name");
    const type = outboxMessageType(job.messageType);
    if (!type.ok) throw rejected("invalid-message-type");
    if (types.has(name.value)) throw rejected("duplicate-job");
    types.set(name.value, type.value);
  }
  const { clock, deliveryPolicy } = options;
  const kind = required(recordKind("platform.schedule"));
  return schedule => {
    const messageType = types.get(schedule.jobName);
    if (messageType === undefined) {
      observePlatformPersistenceDiagnostic(options, capturePlatformPersistenceDiagnostic(() => persistenceScheduleJobMappingDiagnosticRecord("job-unavailable")));
      return null;
    }
    return outboxEntry({
      id: outboxEntryId(String(schedule.id)),
      subject: recordReference({ kind, id: required(recordId(String(schedule.id))) }),
      messageType, deliveryPolicy, createdAt: isoDateTimeFromDate(clock.now()),
    });
  };
}

function rejected(reason: PersistenceScheduleJobMappingDetail["reason"]) {
  return Object.assign(new TypeError("Selected schedule job registrations are invalid."), {
    diagnosticRecord: capturePlatformPersistenceDiagnostic(() => persistenceScheduleJobMappingDiagnosticRecord(reason)),
  });
}
function required<T>(result: Result<T, unknown>): T {
  if (!result.ok) throw result.error;
  return result.value;
}
