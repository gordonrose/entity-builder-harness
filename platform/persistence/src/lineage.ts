import type {
  RecordChange,
  RecordChangeId,
  RecordReference,
} from "@kanbien/core/persistence";
import type { CausationId, Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError } from "./errors";

export interface PlatformRecordChangeStore {
  append(change: RecordChange): Promise<Result<RecordChange, PlatformPersistenceError>>;
  findByRecord(record: RecordReference): Promise<readonly RecordChange[]>;
  findByCause(causationId: CausationId): Promise<readonly RecordChange[]>;
}

export function createInMemoryPlatformRecordChangeStore(): PlatformRecordChangeStore {
  const changes = new Map<RecordChangeId, RecordChange>();

  return {
    async append(change) {
      if (changes.has(change.id)) {
        return {
          ok: false,
          error: platformPersistenceError({
            code: "PLATFORM_PERSISTENCE_DUPLICATE_RECORD_CHANGE",
            defaultMessage: "Record change already exists.",
            messageKey: "platform.persistence.lineage.duplicate",
          }),
        };
      }

      const stored = copyRecordChange(change);
      changes.set(change.id, stored);
      return { ok: true, value: copyRecordChange(stored) };
    },

    async findByRecord(record) {
      return [...changes.values()]
        .filter((change) => change.record.kind === record.kind && change.record.id === record.id)
        .sort((left, right) => Number(left.revision) - Number(right.revision))
        .map(copyRecordChange);
    },

    async findByCause(causationId) {
      return [...changes.values()]
        .filter((change) => change.causationId === causationId)
        .sort((left, right) => Date.parse(left.occurredAt) - Date.parse(right.occurredAt))
        .map(copyRecordChange);
    },
  };
}

function copyRecordChange(change: RecordChange): RecordChange {
  return {
    ...change,
    record: { ...change.record },
    ...(change.actor === undefined ? {} : { actor: { ...change.actor } }),
    ...(change.changedFields === undefined ? {} : { changedFields: [...change.changedFields] }),
  };
}
