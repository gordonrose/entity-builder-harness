import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { captureDiagnosticRecord, deliverDiagnosticRecord, diagnosticProcessingRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, type DiagnosticDefinition, type DiagnosticEvidence, type DiagnosticRecord } from "../diagnostics/index";
import { attachCoreDiagnosticRecord, err, ok } from "../shared/index";
import type { ConcurrencyToken } from "./concurrency";
import { corePersistenceInMemoryBoundaryRecord, corePersistenceValidationRecord,
  type CorePersistenceInMemoryBoundaryDetail, type InMemoryPersistenceDiagnosticOptions } from "./diagnostics";
import { persistenceError } from "./errors";
import type { Repository } from "./repository";
import type { Transaction, UnitOfWork } from "./transactions";

export interface InMemoryRepositoryOptions<TEntity, TId> extends InMemoryPersistenceDiagnosticOptions {
  readonly getId: (entity: TEntity) => TId;
  readonly getConcurrencyToken?: (entity: TEntity) => ConcurrencyToken | undefined;
  readonly clone?: (entity: TEntity) => TEntity;
  readonly initialEntities?: readonly TEntity[];
}

export function inMemoryRepository<TEntity, TId>(
  options: InMemoryRepositoryOptions<TEntity, TId>,
): Repository<TEntity, TId> {
  const records = new Map<TId, TEntity>();
  const cloneEntity = (entity: TEntity): TEntity => clone(entity, options.clone);

  let ordinal = 0;
  for (const entity of options.initialEntities ?? []) {
    let id: TId;
    try { id = options.getId(entity); }
    catch (error) {
      boundaryEvidence(options, { operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal }, error);
      throw error;
    }
    let stored: TEntity;
    try { stored = cloneEntity(entity); }
    catch (error) {
      boundaryEvidence(options, { operation: "initialize", phase: "clone-initial", reason: "boundary-threw", effect: "write-not-reached", ordinal }, error);
      throw error;
    }
    records.set(id, stored);
    ordinal++;
  }

  return {
    async get(id) {
      const entity = records.get(id);
      if (entity === undefined) return null;
      try { return cloneEntity(entity); }
      catch (error) {
        boundaryEvidence(options, { operation: "get", phase: "clone-read", reason: "boundary-threw", effect: "read-only" }, error);
        throw error;
      }
    },

    async save(entity, saveOptions = {}) {
      if (saveOptions.transaction !== undefined) {
        return err(
          persistenceError({
            code: "PERSISTENCE_TRANSACTION_UNSUPPORTED",
            defaultMessage: "The in-memory repository cannot participate in a durable transaction.",
            messageKey: "persistence.transaction.unsupported",
            diagnosticRecord: corePersistenceValidationRecord({ operation: "save", field: "transaction", reason: "unsupported" }),
          }),
        );
      }

      let id: TId;
      try { id = options.getId(entity); }
      catch (error) {
        boundaryEvidence(options, { operation: "save", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached" }, error);
        throw error;
      }

      if (saveOptions.expectedConcurrencyToken !== undefined) {
        const current = records.get(id);
        let currentToken: ConcurrencyToken | undefined;
        try { currentToken = current === undefined ? undefined : options.getConcurrencyToken?.(current); }
        catch (error) {
          boundaryEvidence(options, { operation: "save", phase: "get-concurrency-token", reason: "boundary-threw", effect: "write-not-reached" }, error);
          throw error;
        }

        if (currentToken !== saveOptions.expectedConcurrencyToken) {
          return err(
            persistenceError({
              code: "PERSISTENCE_CONFLICT",
              defaultMessage: "The stored entity changed before it could be saved.",
              messageKey: "persistence.conflict",
              params: { id: String(id) },
              diagnosticRecord: corePersistenceValidationRecord({ operation: "save", field: "concurrency-token",
                reason: current === undefined ? "record-absent" : currentToken === undefined ? "token-unavailable" : "token-mismatch" }),
            }),
          );
        }
      }

      let stored: TEntity;
      try { stored = cloneEntity(entity); }
      catch (error) {
        boundaryEvidence(options, { operation: "save", phase: "clone-before-write", reason: "boundary-threw", effect: "write-not-reached" }, error);
        throw error;
      }
      records.set(id, stored);
      try { return ok(cloneEntity(stored)); }
      catch (error) {
        boundaryEvidence(options, { operation: "save", phase: "clone-after-write", reason: "boundary-threw", effect: "write-completed" }, error);
        throw error;
      }
    },
  };
}

export function inMemoryUnitOfWork(options: InMemoryPersistenceDiagnosticOptions = {}): UnitOfWork {
  return {
    async run(operation) {
      const afterCommitActions: Array<() => Promise<void> | void> = [];
      let open = true;
      const transaction: Transaction = {
        afterCommit(action) {
          if (!open) {
            const error = new TypeError("Cannot register after-commit actions after the transaction is closed.");
            boundaryEvidence(options, { operation: "after-commit-registration", phase: "closed-registration", reason: "transaction-closed", effect: "registration-rejected" }, error);
            throw error;
          }
          afterCommitActions.push(action);
        },
      };

      let phase: "operation" | "after-commit" = "operation";
      let ordinal = 0;
      try {
        const value = await operation(transaction);
        open = false;

        phase = "after-commit";
        for (const action of afterCommitActions) {
          await action();
          ordinal++;
        }

        return value;
      } catch (error) {
        open = false;
        const definitions = selectedDefinitions(options);
        const evidence = boundaryEvidence(options, { operation: "unit-of-work", phase, reason: "boundary-threw",
          effect: phase === "operation" ? "operation-not-returned" : "operation-returned",
          ...(phase === "operation" ? {} : { ordinal }) }, error, definitions);
        throw persistenceError({
          code: "PERSISTENCE_TRANSACTION_FAILED",
          defaultMessage: "Transaction failed before it could complete.",
          messageKey: "persistence.transaction.failed",
          cause: error,
          ...evidence,
          relatedDiagnosticDefinitions: definitions,
        });
      }
    },
  };
}

function selectedDefinitions(options: InMemoryPersistenceDiagnosticOptions) {
  try { return [...coreDiagnosticCatalog.definitions, ...(options.diagnosticDefinitions ?? [])]; }
  catch { observe(options, diagnosticProcessingRecord("definition-selection-failed")); return coreDiagnosticCatalog.definitions; }
}
function observe(options: InMemoryPersistenceDiagnosticOptions, record: DiagnosticRecord): void {
  deliverDiagnosticRecord(record, value => options.onDiagnostic?.(value));
}
function boundaryEvidence(options: InMemoryPersistenceDiagnosticOptions, detail: CorePersistenceInMemoryBoundaryDetail, error: unknown,
  definitions: readonly DiagnosticDefinition[] = selectedDefinitions(options)): DiagnosticEvidence {
  const notices: DiagnosticRecord[] = [];
  const source = selectDiagnosticEvidenceWithReport(definitions, error, record => notices.push(record));
  const own = requireDiagnosticRecord(coreDiagnosticCatalog.definitions, captureDiagnosticRecord(() => corePersistenceInMemoryBoundaryRecord(detail)));
  observe(options, own);
  if (source.diagnosticRecord !== undefined) observe(options, source.diagnosticRecord);
  for (const companion of source.relatedDiagnosticRecords ?? []) observe(options, companion);
  for (const notice of notices) observe(options, notice);
  attachCoreDiagnosticRecord(error, own);
  return { diagnosticRecord: source.diagnosticRecord ?? own,
    ...(source.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: source.relatedDiagnosticRecords }) };
}

function clone<TEntity>(entity: TEntity, cloneEntity?: (entity: TEntity) => TEntity): TEntity {
  if (cloneEntity !== undefined) {
    return cloneEntity(entity);
  }

  if (Array.isArray(entity)) {
    return [...entity] as TEntity;
  }

  if (entity !== null && typeof entity === "object") {
    return { ...entity };
  }

  return entity;
}
