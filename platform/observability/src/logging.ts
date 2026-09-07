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
  const fields = {
    ...(input.fields ?? {}),
    ...(input.error === undefined ? {} : { error: normalizePlatformError(input.error) }),
  };

  logger.write({
    level: input.level,
    message: input.message,
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    ...(Object.keys(fields).length === 0 ? {} : { fields: normalizePlatformLogFields(fields, options) as LogFields }),
  });
}
