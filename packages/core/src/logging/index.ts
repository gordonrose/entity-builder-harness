import type { CorrelationId } from "../shared/index";
import type { CoreLoggingDiagnosticOptions } from "./diagnostics";
import { LoggingObservation } from "./observations";
export * from "./diagnostics";
export { observeCoreLoggingDiagnostic, selectCoreLoggingDiagnosticEvidence } from "./observations";

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
}, diagnostics?: CoreLoggingDiagnosticOptions): LogRecord {
  const observation = new LoggingObservation("log-record", diagnostics);
  return observation.run(() => ({
    level: observation.at("input-projection", "level", () => input.level),
    message: observation.at("input-projection", "message", () => input.message),
    ...(observation.at("input-projection", "correlation-id", () => input.correlationId) === undefined ? {} : { correlationId: observation.at("input-projection", "correlation-id", () => input.correlationId) }),
    ...(observation.at("input-projection", "fields", () => input.fields) === undefined ? {} : { fields: observation.at("field-enumeration", "fields", () => ({ ...input.fields })) }),
  }));
}

export function redactLogFields(
  fields: LogFields,
  redactedKeys: readonly string[],
  redactedValue: unknown = defaultRedactedValue,
  diagnostics?: CoreLoggingDiagnosticOptions,
): LogFields {
  const observation = new LoggingObservation("redact-fields", diagnostics);
  return observation.run(() => redactFields(fields, redactedKeys, redactedValue, observation));
}

export function createLogRedactor(options: LogRedactorOptions = {}, diagnostics?: CoreLoggingDiagnosticOptions): Redactor {
  const observation = new LoggingObservation("create-redactor", diagnostics);
  return observation.run(() => keyRedactor(
    observation.at("key-iteration", "redaction-keys", () => [...defaultSensitiveLogFieldNames, ...(() => {
      const keys = observation.at("key-projection", "redaction-keys", () => options.additionalKeys ?? []);
      return observation.at("key-iteration", "redaction-keys", () => keys);
    })()]),
    observation.at("key-projection", "replacement", () => options.redactedValue),
    diagnostics,
  ));
}

function redactFields(fields: LogFields, redactedKeys: readonly string[], redactedValue: unknown = defaultRedactedValue, observation: LoggingObservation): LogFields {
  const keys = observation.at("key-iteration", "redaction-keys", () => new Set(redactedKeys.map((key) => {
    const normalized = observation.at("key-normalization", "redaction-keys", () => normalizeLogFieldName(key));
    return observation.at("key-iteration", "redaction-keys", () => normalized);
  })));
  return redactRecord(fields, keys, redactedValue, observation);
}
function redactRecord(fields: LogFields, redactedKeys: ReadonlySet<string>, redactedValue: unknown, observation: LoggingObservation): LogFields {
  const result: Record<string, unknown> = {};

  for (const [key, value] of observation.at("field-enumeration", "fields", () => Object.entries(fields))) {
    const replacement = observation.at("key-normalization", "fields", () => redactedKeys.has(normalizeLogFieldName(key)))
      ? redactedValue
      : redactNestedValue(value, redactedKeys, redactedValue, observation);
    observation.at("field-assignment", "fields", () => { result[key] = replacement; });
    observation.at("field-enumeration", "fields", () => undefined);
  }

  return result;
}

export function keyRedactor(redactedKeys: readonly string[], redactedValue?: unknown, diagnostics?: CoreLoggingDiagnosticOptions): Redactor {
  return {
    redact: (fields) => {
      const observation = new LoggingObservation("redact", diagnostics);
      return observation.run(() => redactFields(fields, redactedKeys, redactedValue, observation));
    },
  };
}

export function redactingLogger(inner: Logger, redactor: Redactor, diagnostics?: CoreLoggingDiagnosticOptions): Logger {
  return {
    write: (record) => {
      const observation = new LoggingObservation("write", diagnostics);
      observation.effectIs("inner-not-invoked");
      observation.run(() => {
      const returned = observation.at("inner-selection", "logger", () => inner.write((() => {
      const projected = observation.at("record-projection", undefined, () => ({
        ...record,
        ...(observation.at("record-projection", "fields", () => record.fields) === undefined ? {} : { fields: (() => {
          return observation.at("redactor-selection", "redactor", () => redactor.redact((() => {
            const fields = observation.at("record-projection", "fields", () => record.fields);
            return observation.at("redactor-invocation", "redactor", () => fields!);
          })()));
        })() }),
      }));
      observation.effectIs("inner-outcome-unknown");
      return observation.at("inner-invocation", "logger", () => projected);
      })()));
      observation.returned(returned);
      });
    },
  };
}

function redactNestedValue(value: unknown, redactedKeys: ReadonlySet<string>, redactedValue: unknown, observation: LoggingObservation): unknown {
  if (observation.at("value-inspection", "fields", () => Array.isArray(value))) {
    return observation.at("value-traversal", "fields", () => (value as unknown[]).map((item) => {
      const copied = redactNestedValue(item, redactedKeys, redactedValue, observation);
      return observation.at("value-traversal", "fields", () => copied);
    }));
  }

  if (!observation.at("value-inspection", "fields", () => isRecord(value))) {
    return value;
  }

  return redactRecord(value as LogFields, redactedKeys, redactedValue, observation);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && Object.getPrototypeOf(value) === Object.prototype;
}

function normalizeLogFieldName(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}
