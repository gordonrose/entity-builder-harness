import type { CorrelationId } from "../shared/index";

export type LogLevel = "debug" | "info" | "warn" | "error";
export type LogFields = Readonly<Record<string, unknown>>;

export const defaultRedactedValue = "[REDACTED]";

export interface LogRecord {
  readonly level: LogLevel;
  readonly message: string;
  readonly correlationId?: CorrelationId;
  readonly fields?: LogFields;
}

export interface Logger {
  write(record: LogRecord): void;
}

export interface Redactor {
  redact(fields: LogFields): LogFields;
}

export const noopLogger: Logger = {
  write: () => undefined,
};

export function logRecord(input: {
  readonly level: LogLevel;
  readonly message: string;
  readonly correlationId?: CorrelationId;
  readonly fields?: LogFields;
}): LogRecord {
  return {
    level: input.level,
    message: input.message,
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    ...(input.fields === undefined ? {} : { fields: { ...input.fields } }),
  };
}

export function redactLogFields(
  fields: LogFields,
  redactedKeys: readonly string[],
  redactedValue: unknown = defaultRedactedValue,
): LogFields {
  const keys = new Set(redactedKeys);
  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(fields)) {
    result[key] = keys.has(key) ? redactedValue : value;
  }

  return result;
}

export function keyRedactor(redactedKeys: readonly string[], redactedValue?: unknown): Redactor {
  return {
    redact: (fields) => redactLogFields(fields, redactedKeys, redactedValue),
  };
}

export function redactingLogger(inner: Logger, redactor: Redactor): Logger {
  return {
    write: (record) => {
      inner.write({
        ...record,
        ...(record.fields === undefined ? {} : { fields: redactor.redact(record.fields) }),
      });
    },
  };
}
