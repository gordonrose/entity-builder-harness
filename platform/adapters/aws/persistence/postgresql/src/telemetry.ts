import type { PlatformPersistenceObserver } from "@kanbien/platform-persistence";
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
): void {
  if (sink === undefined) return;
  try {
    sink({
      operation: input.operation,
      outcome: input.outcome,
      durationBucket: durationBucket(input.durationMs),
      ...(input.error === undefined ? {} : { errorClass: postgreSqlPersistenceProviderFailureClass(input.error) }),
      ...(input.poolInUse === undefined ? {} : { poolInUseBucket: poolBucket(input.poolInUse) }),
    });
  } catch {
    // Telemetry never changes database transaction semantics.
  }
}

export function postgreSqlPlatformPersistenceObserver(
  sink: PostgreSqlPersistenceTelemetrySink | undefined,
): PlatformPersistenceObserver {
  return {
    record: (observation) => {
      recordPostgreSqlPersistenceTelemetry(sink, {
        operation: "transaction",
        outcome: observation.outcome === "succeeded" ? "succeeded" : "failed",
        durationMs: 0,
        ...(observation.error === undefined ? {} : { error: observation.error }),
      });
    },
  };
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
