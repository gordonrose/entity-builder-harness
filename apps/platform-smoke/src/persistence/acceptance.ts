import {
  outboxDeliveryPolicy,
  outboxEntry,
  outboxEntryId,
  outboxMessageType,
  recordChange,
  recordChangeId,
  recordKind,
  recordReference,
  type PersistenceError,
} from "@kanbien/core/persistence";
import { ok, type Result } from "@kanbien/core/shared";
import type {
  PlatformPersistenceAtomicWriter,
  PlatformPersistenceError,
  PlatformPersistenceMutation,
} from "@kanbien/platform-persistence";
import { platformPersistenceMutation } from "@kanbien/platform-persistence";
import {
  platformSmokeInitialWorkItemRevision,
  type PlatformSmokeAcceptedWorkItemFacts,
  type PlatformSmokeAcceptWorkItemInput,
  type PlatformSmokeWorkItem,
  type PlatformSmokeWorkItemPersistenceError,
  type PlatformSmokeWorkItemRepository,
} from "./types";

export interface PlatformSmokeAcceptWorkItemDependencies {
  readonly repository: PlatformSmokeWorkItemRepository;
  readonly atomicWriter: PlatformPersistenceAtomicWriter;
}

/**
 * Declare the harmless product state and the two platform-owned durable facts.
 * The selected repository and writer must make all three writes one physical
 * transaction; this app never receives a table name or an AWS client.
 */
export async function acceptPlatformSmokeWorkItem(
  input: PlatformSmokeAcceptWorkItemInput,
  dependencies: PlatformSmokeAcceptWorkItemDependencies,
): Promise<Result<PlatformSmokeAcceptedWorkItemFacts, PlatformSmokeWorkItemPersistenceError>> {
  const workItem: PlatformSmokeWorkItem = {
    id: input.id,
    state: "accepted",
    revision: platformSmokeInitialWorkItemRevision(),
    acceptedAt: input.acceptedAt,
  };
  const mutation = platformSmokeWorkItemMutation(input, workItem);
  if (!mutation.ok) return mutation;

  return dependencies.atomicWriter.run<PlatformSmokeAcceptedWorkItemFacts, PlatformSmokeWorkItemPersistenceError>(async (scope) => {
    const created = await dependencies.repository.create({
      workItem,
      transaction: scope.transaction,
    });
    if (!created.ok) return created;
    const staged = await scope.stage(mutation.value);
    if (!staged.ok) return staged;
    return ok({ workItem: created.value, outboxEntryId: mutation.value.outboxEntry.id });
  });
}

function platformSmokeWorkItemMutation(
  input: PlatformSmokeAcceptWorkItemInput,
  workItem: PlatformSmokeWorkItem,
): Result<PlatformPersistenceMutation, PersistenceError | PlatformPersistenceError> {
  const subject = recordReference({
    kind: required(recordKind("platform-smoke.work-item")),
    id: workItem.id,
  });
  const change = recordChange({
    id: recordChangeId("platform-smoke.work-item-change." + workItem.id + ".1"),
    record: subject,
    revision: workItem.revision,
    action: "created",
    occurredAt: workItem.acceptedAt,
    causationId: input.causationId,
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
  });
  if (!change.ok) return change;
  const entry = outboxEntry({
    id: outboxEntryId("platform-smoke.work-item-accepted." + workItem.id),
    subject,
    messageType: required(outboxMessageType("platform-smoke.work-item.accepted")),
    deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")),
    createdAt: workItem.acceptedAt,
    causationId: input.causationId,
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
  });
  return platformPersistenceMutation({ recordChange: change.value, outboxEntry: entry });
}

function required<TValue>(result: { readonly ok: true; readonly value: TValue } | { readonly ok: false }): TValue {
  if (!result.ok) {
    throw new Error("Platform-smoke persistence constants must be valid.");
  }
  return result.value;
}
