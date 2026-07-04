import type { CorrelationId } from "../shared/index";

export type LogLevel = "debug" | "info" | "warn" | "error";

export interface LogRecord {
  readonly level: LogLevel;
  readonly message: string;
  readonly correlationId?: CorrelationId;
  readonly fields?: Readonly<Record<string, unknown>>;
}

export interface Logger {
  write(record: LogRecord): void;
}

export interface Redactor {
  redact(fields: Readonly<Record<string, unknown>>): Readonly<Record<string, unknown>>;
}

export const noopLogger: Logger = {
  write: () => undefined,
};
