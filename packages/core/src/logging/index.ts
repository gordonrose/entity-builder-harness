import type { CorrelationId } from "../shared/index";

export type LogLevel = "debug" | "info" | "warn" | "error";
export type LogFields = Readonly<Record<string, unknown>>;

export const defaultRedactedValue = "[REDACTED]";
export const defaultSensitiveLogFieldNames = [
  "password",
  "passphrase",
  "passwd",
  "pwd",
  "secret",
  "clientSecret",
  "token",
  "accessToken",
  "refreshToken",
  "idToken",
  "sessionToken",
  "apiKey",
  "authorization",
  "cookie",
  "setCookie",
  "privateKey",
  "credential",
  "credentials",
] as const;

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

export interface LogRedactorOptions {
  readonly additionalKeys?: readonly string[];
  readonly redactedValue?: unknown;
}

export const noopLogger: Logger = {
  write: () => undefined,
};

export const defaultLogRedactor: Redactor = createLogRedactor();

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
  const keys = new Set(redactedKeys.map(normalizeLogFieldName));

  return redactRecord(fields, keys, redactedValue);
}

export function createLogRedactor(options: LogRedactorOptions = {}): Redactor {
  return keyRedactor(
    [...defaultSensitiveLogFieldNames, ...(options.additionalKeys ?? [])],
    options.redactedValue,
  );
}

function redactRecord(fields: LogFields, redactedKeys: ReadonlySet<string>, redactedValue: unknown): LogFields {
  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(fields)) {
    result[key] = redactedKeys.has(normalizeLogFieldName(key))
      ? redactedValue
      : redactNestedValue(value, redactedKeys, redactedValue);
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

function redactNestedValue(value: unknown, redactedKeys: ReadonlySet<string>, redactedValue: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => redactNestedValue(item, redactedKeys, redactedValue));
  }

  if (!isRecord(value)) {
    return value;
  }

  return redactRecord(value, redactedKeys, redactedValue);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && Object.getPrototypeOf(value) === Object.prototype;
}

function normalizeLogFieldName(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}
