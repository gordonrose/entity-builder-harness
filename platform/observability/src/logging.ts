import type { Logger, LogFields, LogLevel } from "@kanbien/core/logging";
import type { CorrelationId } from "@kanbien/core/shared";
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
): Logger {
  return {
    write: (record) => {
      writePlatformLog(inner, {
        level: record.level,
        message: record.message,
        ...(record.correlationId === undefined ? {} : { correlationId: record.correlationId }),
        ...(record.fields === undefined ? {} : { fields: record.fields }),
      }, options);
    },
  };
}

export function writePlatformLog(
  logger: Logger,
  input: PlatformLogInput,
  options: PlatformValueNormalizationOptions = {},
): void {
  try { // Isolate every normalisation and provider write failure from the business path that requested telemetry.
    const fields = { // Assemble the bounded structured fields before crossing the injected logger boundary.
      ...(input.fields ?? {}), // Preserve only caller-supplied fields that the caller has already chosen to emit.
      ...(input.error === undefined ? {} : { error: normalizePlatformError(input.error) }), // Reduce an error to its bounded shape when the caller explicitly supplied one.
    };

    logger.write({ // Delegate one safe structured record to the target-selected Core logger port.
      level: input.level, // Keep the caller's bounded Core log level.
      message: input.message, // Keep the caller's stable message identifier.
      ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }), // Preserve an explicitly supplied correlation identifier at the port boundary.
      ...(Object.keys(fields).length === 0 ? {} : { fields: normalizePlatformLogFields(fields, options) as LogFields }), // Normalise all optional fields before delivery.
    });
  } catch { // Treat logging as best-effort operational evidence rather than a dependency of successful work.
    // Observability must never turn a completed request or job into a failure.
  }
}
