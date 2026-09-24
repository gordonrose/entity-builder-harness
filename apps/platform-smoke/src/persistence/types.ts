import type {
  OutboxEntryId,
  PersistenceError,
  RecordId,
  RecordRevision,
  Transaction,
} from "@kanbien/core/persistence";
import { recordId, recordRevision } from "@kanbien/core/persistence";
import type { CausationId, CorrelationId, ISODateTime, Result } from "@kanbien/core/shared";
import type { PlatformPersistenceError } from "@kanbien/platform-persistence";

export type PlatformSmokeWorkItemId = RecordId;
export type PlatformSmokeWorkItemState = "accepted";
export type PlatformSmokeWorkItemPersistenceError = PersistenceError | PlatformPersistenceError;

export interface PlatformSmokeWorkItem {
  readonly id: PlatformSmokeWorkItemId;
  readonly state: PlatformSmokeWorkItemState;
  readonly revision: RecordRevision;
  readonly acceptedAt: ISODateTime;
}

/**
 * Product-owned repository semantics: a work item is created once, not
 * overwritten. The selected persistence adapter must enlist this write in the
 * transaction supplied by the atomic writer.
 */
export interface PlatformSmokeWorkItemRepository {
  create(input: {
    readonly workItem: PlatformSmokeWorkItem;
    readonly transaction: Transaction;
  }): Promise<Result<PlatformSmokeWorkItem, PlatformSmokeWorkItemPersistenceError>>;
}

export interface PlatformSmokeAcceptWorkItemInput {
  readonly id: PlatformSmokeWorkItemId;
  readonly acceptedAt: ISODateTime;
  readonly causationId: CausationId;
  readonly correlationId?: CorrelationId;
}

export interface PlatformSmokeAcceptedWorkItemFacts {
  readonly workItem: PlatformSmokeWorkItem;
  readonly outboxEntryId: OutboxEntryId;
}

export function platformSmokeWorkItemId(
  value: string,
): Result<PlatformSmokeWorkItemId, PersistenceError> {
  return recordId(value);
}

export function platformSmokeInitialWorkItemRevision(): RecordRevision {
  const revision = recordRevision(1);
  if (!revision.ok) {
    throw new Error("Platform-smoke initial work-item revision must be valid.");
  }
  return revision.value;
}
