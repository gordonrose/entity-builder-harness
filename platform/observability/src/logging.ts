import type { Logger, LogFields, LogLevel, LogRecord } from "@kanbien/core/logging";
import type { CorrelationId } from "@kanbien/core/shared";
import { hasValidatedDiagnosticLogOrigin } from "./diagnostic-log";
import { observePlatformSinkCompletion } from "./diagnostics";
import { reportPlatformObservationBoundary, type PlatformObservationDiagnostics } from "./boundary-observation";
import type { PlatformObservationBoundaryDetail } from "./boundary-definitions";
import {
  normalizePlatformError,
  normalizePlatformLogFields,
  type PlatformValueNormalizationOptions,
} from "./normalization";

export interface PlatformLogInput {
  readonly level: LogLevel;
  readonly message: string;
  readonly correlationId?: CorrelationId;
  readonly fields?: Readonly<Record<string, unknown>>;
  readonly error?: unknown;
}

export function createPlatformSafeLogger(
  inner: Logger,
  options: PlatformValueNormalizationOptions = {},
  observations?: PlatformObservationDiagnostics,
): Logger {
  return {
    write: (record) => {
      if (hasValidatedDiagnosticLogOrigin(record)) {
        // The reporter already parsed the selected closed contract and applied
        // stricter whole-record budgets. Preserve its approved depth/item budget,
        // but never bypass a default or target-added sensitive-key policy.
        const fields = record.fields ?? {};
        const policyChecked = normalizePlatformLogFields(fields, { ...options,
          maxDepth: 12, maxArrayItems: 64, maxObjectKeys: 64, maxStringLength: 16_384 });
        if (JSON.stringify(policyChecked) !== JSON.stringify(fields)) throw new TypeError("PLATFORM_DIAGNOSTIC_SINK_POLICY_CONFLICT");
        // Its reporter owns delivery-failure isolation and the truthful status.
        const pending: unknown = inner.write(record);
        if (observePlatformSinkCompletion(pending, () => undefined)) throw new TypeError("PLATFORM_DIAGNOSTIC_SINK_ASYNC_UNCONFIRMED");
        return;
      }
      let input: PlatformLogInput;
      let field: PlatformObservationBoundaryDetail["field"] = "level";
      try { input = {
        level: record.level,
        message: (field = "message", record.message),
        ...(field = "correlation-id", record.correlationId === undefined ? {} : { correlationId: record.correlationId }),
        ...(field = "fields", record.fields === undefined ? {} : { fields: record.fields }),
      }; } catch (error) {
        reportPlatformObservationBoundary(observations, { operation: "log-write", phase: "input-projection", field, reason: "threw", effect: "not-attempted" }, error);
        throw error;
      }
      writePlatformLog(inner, input, options, observations);
    },
  };
}

export function writePlatformLog(
  logger: Logger,
  input: PlatformLogInput,
  options: PlatformValueNormalizationOptions = {},
  observations?: PlatformObservationDiagnostics,
): void {
  let phase: PlatformObservationBoundaryDetail["phase"] = "input-projection";
  let field: PlatformObservationBoundaryDetail["field"] = "fields";
  let errorValue: unknown;
  try { // Isolate every normalisation and provider write failure from the business path that requested telemetry.
    const fields = { // Assemble the bounded structured fields before crossing the injected logger boundary.
      ...(input.fields ?? {}), // Preserve only caller-supplied fields that the caller has already chosen to emit.
      ...((field = "error", input.error) === undefined ? {} : { error: (errorValue = input.error, phase = "error-class", normalizePlatformError(errorValue, options)) }), // Exact selected classification, never provider strings.
    };

    phase = "sink-selection"; field = "logger";
    let prepared: LogRecord;
    const pending: unknown = logger.write((phase = "input-projection", prepared = { // Keep original method-selection-before-argument order.
      level: (field = "level", input.level),
      message: (field = "message", input.message),
      ...(field = "correlation-id", input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
      ...(Object.keys(fields).length === 0 ? {} : { fields: (phase = "field-normalization", field = "fields", normalizePlatformLogFields(fields, options) as LogFields) }),
    }, phase = "sink-invocation", field = "logger", prepared));
    observePlatformSinkCompletion(pending, (error) => reportPlatformObservationBoundary(observations,
      { operation: "log-write", phase: "sink-completion", field: "logger", reason: "rejected", effect: "unknown" }, error));
  } catch (error) { // Treat logging as best-effort operational evidence rather than a dependency of successful work.
    reportPlatformObservationBoundary(observations, { operation: "log-write", phase, field, reason: "threw", effect: phase === "sink-invocation" ? "unknown" : "not-attempted" }, error);
    // Observability must never turn a completed request or job into a failure.
  }
}
