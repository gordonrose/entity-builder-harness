import {
  keyRedactor,
  logRecord,
  redactingLogger,
  type LogFields,
  type LogRecord,
  type Logger,
  type LogLevel,
  type Redactor,
} from "../src/logging/index";
import { correlationId } from "../src/shared/index";

const level: LogLevel = "info";
const fields: LogFields = {
  service: "api",
  attempt: 2,
  nestedDiagnostic: { provider: "test" },
};

const record: LogRecord = logRecord({
  level,
  message: "Runtime event.",
  correlationId: correlationId("request-123"),
  fields,
});
void record;

const redactor: Redactor = keyRedactor(["password", "token"]);
const logger: Logger = {
  write: (_record) => undefined,
};

const wrapped: Logger = redactingLogger(logger, redactor);
wrapped.write(record);

// @ts-expect-error log levels are intentionally constrained.
logRecord({ level: "fatal", message: "Unsupported level." });

// @ts-expect-error correlationId must be branded, not any string.
logRecord({ level: "info", message: "Bad correlation.", correlationId: "request-123" });

// @ts-expect-error log records need an operational message.
logRecord({ level: "info" });
