import {
  observePlatformPersistenceDiagnostic,
  persistenceCommandDiagnosticRecord,
  selectPlatformPersistenceDiagnosticEvidence,
  type PlatformPersistenceDiagnosticOptions,
  type PlatformPersistenceObserver,
} from "@kanbien/platform-persistence";
import { postgreSqlPersistenceProviderFailureClass, type PostgreSqlPersistenceOperation } from "./errors";

export type PostgreSqlPersistenceTelemetryOutcome = "succeeded" | "failed" | "rolled_back";

export interface PostgreSqlPersistenceTelemetry {
  readonly operation: PostgreSqlPersistenceOperation;
  readonly outcome: PostgreSqlPersistenceTelemetryOutcome;
  readonly durationBucket: "under-10ms" | "under-100ms" | "under-1000ms" | "one-second-or-more";
  readonly errorClass?: ReturnType<typeof postgreSqlPersistenceProviderFailureClass>;
  readonly poolInUseBucket?: "zero" | "one" | "two-to-four" | "five-or-more";
}

export type PostgreSqlPersistenceTelemetrySink = (observation: PostgreSqlPersistenceTelemetry) => void;

export function recordPostgreSqlPersistenceTelemetry(
  sink: PostgreSqlPersistenceTelemetrySink | undefined,
  input: {
    readonly operation: PostgreSqlPersistenceOperation;
    readonly outcome: PostgreSqlPersistenceTelemetryOutcome;
    readonly durationMs: number;
    readonly error?: unknown;
    readonly poolInUse?: number;
  },
  diagnostics?: PlatformPersistenceDiagnosticOptions,
): void {
  if (sink === undefined) return;
  let operation: PostgreSqlPersistenceOperation | undefined;
  let boundary: "encoding" | "callback" = "encoding";
  try {
    const observation = {
      operation: operation = input.operation,
      outcome: input.outcome,
      durationBucket: durationBucket(input.durationMs),
      ...(input.error === undefined ? {} : { errorClass: postgreSqlPersistenceProviderFailureClass(input.error) }),
      ...(input.poolInUse === undefined ? {} : { poolInUseBucket: poolBucket(input.poolInUse) }),
    };
    boundary = "callback";
    const pending: unknown = sink(observation);
    consumeRejection(pending, (cause) => observeTelemetryFailure(diagnostics, operation, "callback", cause));
  } catch (cause) {
    observeTelemetryFailure(diagnostics, operation, boundary, cause);
    // Telemetry never changes database transaction semantics.
  }
}

export function postgreSqlPlatformPersistenceObserver(
  sink: PostgreSqlPersistenceTelemetrySink | undefined,
  diagnostics?: PlatformPersistenceDiagnosticOptions,
): PlatformPersistenceObserver {
  return {
    record: (observation) => {
      try {
        recordPostgreSqlPersistenceTelemetry(sink, {
          operation: "transaction",
          outcome: observation.outcome === "succeeded" ? "succeeded" : "failed",
          durationMs: 0,
          ...(observation.error === undefined ? {} : { error: observation.error }),
        }, diagnostics);
      } catch (cause) {
        observeTelemetryFailure(diagnostics, "transaction", "encoding", cause);
        throw cause;
      }
    },
  };
}

const intrinsicPromiseThen = Promise.prototype.then;
function consumeRejection(pending: unknown, rejected: (cause: unknown) => void): void {
  if (pending === undefined) return;
  try { Reflect.apply(intrinsicPromiseThen, pending, [undefined, rejected]); }
  catch {
    try { Reflect.apply(intrinsicPromiseThen, Promise.resolve(pending), [undefined, rejected]); }
    catch (cause) { rejected(cause); }
  }
}

function observeTelemetryFailure(diagnostics: PlatformPersistenceDiagnosticOptions | undefined,
  operation: PostgreSqlPersistenceOperation | undefined, boundary: "encoding" | "callback", cause: unknown): void {
  try {
    if (operation !== undefined) {
      // Encoding here means the local observation projection, never SQL encoding.
      observePlatformPersistenceDiagnostic(diagnostics, persistenceCommandDiagnosticRecord({
        operation, boundary, role: "primary", condition: "unclassified", codeStatus: "not-inspected", effect: "not-assessed",
      }), cause);
      return;
    }
    // A failed operation getter establishes no operation to put in an own record.
    const source = selectPlatformPersistenceDiagnosticEvidence(diagnostics ?? {}, cause);
    for (const record of [source.diagnosticRecord, ...(source.relatedDiagnosticRecords ?? [])]) {
      if (record === undefined) continue;
      try { consumeRejection(diagnostics?.onDiagnostic?.(record), () => undefined); }
      catch { /* Optional observer failures cannot change telemetry or database work. */ }
    }
  } catch { /* Diagnostic selection/construction cannot change the legacy outcome. */ }
}

function durationBucket(durationMs: number): PostgreSqlPersistenceTelemetry["durationBucket"] {
  if (!Number.isFinite(durationMs) || durationMs < 0) return "one-second-or-more";
  if (durationMs < 10) return "under-10ms";
  if (durationMs < 100) return "under-100ms";
  if (durationMs < 1_000) return "under-1000ms";
  return "one-second-or-more";
}

function poolBucket(poolInUse: number): NonNullable<PostgreSqlPersistenceTelemetry["poolInUseBucket"]> {
  if (!Number.isFinite(poolInUse) || poolInUse <= 0) return "zero";
  if (poolInUse === 1) return "one";
  if (poolInUse <= 4) return "two-to-four";
  return "five-or-more";
}
