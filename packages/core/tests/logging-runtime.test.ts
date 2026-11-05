import { deepEqual, equal, throws } from "node:assert/strict";
import { correlationId } from "../src/shared/index";
import {
  createLogRedactor,
  defaultLogRedactor,
  defaultRedactedValue,
  defaultSensitiveLogFieldNames,
  keyRedactor,
  logRecord,
  noopLogger,
  redactLogFields,
  redactingLogger,
  type LogRecord,
  type Logger,
  coreLoggingBoundaryDiagnosticRecord,
  coreLoggingBoundaryDiagnostic,
  observeCoreLoggingDiagnostic,
  type CoreLoggingDiagnosticOptions,
} from "../src/logging/index";
import { coreMonitoringValidationDiagnosticRecord } from "../src/monitoring/index";
import type { DiagnosticRecord } from "../src/diagnostics/index";

const requestId = correlationId("request-123");
const record = logRecord({
  level: "info",
  message: "Config loaded.",
  correlationId: requestId,
  fields: {
    service: "api",
    password: "secret",
  },
});

deepEqual(record, {
  level: "info",
  message: "Config loaded.",
  correlationId: "request-123",
  fields: {
    service: "api",
    password: "secret",
  },
});

const fields = { token: "abc", service: "api" };
const copiedRecord = logRecord({ level: "debug", message: "copy test", fields });
fields.token = "changed";
equal(copiedRecord.fields?.token, "abc");

deepEqual(redactLogFields(record.fields ?? {}, ["password"]), {
  service: "api",
  password: defaultRedactedValue,
});

deepEqual(
  redactLogFields(
    {
      access_token: "access-secret",
      AccessToken: "second-secret",
      "set-cookie": "session=secret",
      service: "api",
    },
    defaultSensitiveLogFieldNames,
  ),
  {
    access_token: defaultRedactedValue,
    AccessToken: defaultRedactedValue,
    "set-cookie": defaultRedactedValue,
    service: "api",
  },
);

deepEqual(
  defaultLogRedactor.redact({
    auth: {
      token: "nested-secret",
      detail: { client_secret: "client-secret" },
    },
    attempts: [{ apiKey: "api-secret", status: "failed" }],
    service: "api",
  }),
  {
    auth: {
      token: defaultRedactedValue,
      detail: { client_secret: defaultRedactedValue },
    },
    attempts: [{ apiKey: defaultRedactedValue, status: "failed" }],
    service: "api",
  },
);

deepEqual(
  createLogRedactor({ additionalKeys: ["dateOfBirth"], redactedValue: null }).redact({
    date_of_birth: "2000-01-01",
    tenant: "tenant-1",
  }),
  {
    date_of_birth: null,
    tenant: "tenant-1",
  },
);

const customRedactor = keyRedactor(["token"], null);
deepEqual(customRedactor.redact({ token: "abc", tenant: "tenant-1" }), {
  token: null,
  tenant: "tenant-1",
});

const written: LogRecord[] = [];
const captureLogger: Logger = {
  write: (entry) => {
    written.push(entry);
  },
};

redactingLogger(captureLogger, keyRedactor(["password"])).write(record);
equal(written.length, 1);
const writtenRecord = written[0];
if (writtenRecord === undefined) {
  throw new Error("Expected a redacted log record to be written.");
}
deepEqual(writtenRecord.fields, {
  service: "api",
  password: defaultRedactedValue,
});

noopLogger.write(record);

async function loggingDiagnostics(): Promise<void> {
  const events: DiagnosticRecord[] = [];
  const contexts: unknown[] = [];
  const diagnostics: CoreLoggingDiagnosticOptions = { onDiagnostic(record, context) { equal(this, diagnostics); events.push(record); contexts.push(context); } };
  const raw = Object.freeze(new Error("PRIVATE_LOG_CANARY"));
  const failures: readonly [() => unknown, string, string, string | undefined, string][] = [
    [() => logRecord({ get level(): never { throw raw; }, message: "safe" }, diagnostics), "log-record", "input-projection", "level", "result-not-returned"],
    [() => logRecord({ level: "info", get message(): never { throw raw; } }, diagnostics), "log-record", "input-projection", "message", "result-not-returned"],
    [() => logRecord({ level: "info", message: "safe", get correlationId(): never { throw raw; } }, diagnostics), "log-record", "input-projection", "correlation-id", "result-not-returned"],
    [() => logRecord({ level: "info", message: "safe", fields: Object.defineProperty({}, "secret", { enumerable: true, get() { throw raw; } }) }, diagnostics), "log-record", "field-enumeration", "fields", "result-not-returned"],
    [() => createLogRedactor({ get additionalKeys(): never { throw raw; } }, diagnostics), "create-redactor", "key-projection", "redaction-keys", "result-not-returned"],
    [() => createLogRedactor({ get redactedValue(): never { throw raw; } }, diagnostics), "create-redactor", "key-projection", "replacement", "result-not-returned"],
    [() => redactLogFields({}, [null as never], undefined, diagnostics), "redact-fields", "key-normalization", "redaction-keys", "result-not-returned"],
    [() => redactLogFields(Object.defineProperty({}, "secret", { enumerable: true, get() { throw raw; } }), [], undefined, diagnostics), "redact-fields", "field-enumeration", "fields", "result-not-returned"],
    [() => keyRedactor([], undefined, diagnostics).redact({ nested: new Proxy({}, { getPrototypeOf() { throw raw; } }) }), "redact", "value-inspection", "fields", "result-not-returned"],
    [() => redactingLogger({ get write(): never { throw raw; } }, defaultLogRedactor, diagnostics).write(record), "write", "inner-selection", "logger", "inner-not-invoked"],
    [() => redactingLogger(captureLogger, { get redact(): never { throw raw; } }, diagnostics).write(record), "write", "redactor-selection", "redactor", "inner-not-invoked"],
    [() => redactingLogger(captureLogger, { redact() { throw raw; } }, diagnostics).write(record), "write", "redactor-invocation", "redactor", "inner-not-invoked"],
    [() => redactingLogger({ write() { throw raw; } }, defaultLogRedactor, diagnostics).write(record), "write", "inner-invocation", "logger", "inner-outcome-unknown"],
  ];
  for (const [invoke, operation, phase, field, effect] of failures) {
    events.length = 0;
    throws(invoke);
    equal(events.length, 1);
    equal(events[0]?.code, "core.logging.boundary-failed");
    equal(events[0]?.definitionVersion, 1);
    deepEqual(coreLoggingBoundaryDiagnostic.classification, { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false });
    deepEqual(events[0]?.detail, { operation, phase, ...(field === undefined ? {} : { field }), reason: "threw", effect });
    equal(JSON.stringify(events).includes("PRIVATE_LOG_CANARY"), false);
  }
  events.length = 0;
  throws(() => logRecord({ level: "info", get message(): never { throw raw; } }, diagnostics), (error) => error === raw);
  equal(Object.hasOwn(raw, "diagnosticRecord"), false);
  const laterKeys = ["first", "second"];
  let keyReads = 0;
  Object.defineProperty(laterKeys, "1", { get() { keyReads++; throw raw; } });
  events.length = 0;
  throws(() => redactLogFields({}, laterKeys, undefined, diagnostics), (error) => error === raw);
  equal(keyReads, 1);
  deepEqual(events[0]?.detail, { operation: "redact-fields", phase: "key-iteration", field: "redaction-keys", reason: "threw", effect: "result-not-returned" });
  const laterValues = [1, 2];
  let valueReads = 0;
  Object.defineProperty(laterValues, "1", { get() { valueReads++; throw raw; } });
  events.length = 0;
  throws(() => redactLogFields({ nested: laterValues }, [], undefined, diagnostics), (error) => error === raw);
  equal(valueReads, 1);
  deepEqual(events[0]?.detail, { operation: "redact-fields", phase: "value-traversal", field: "fields", reason: "threw", effect: "result-not-returned" });
  const sequence: string[] = [];
  let fieldReads = 0;
  const input: LogRecord = { level: "info", message: "safe", get fields() { sequence.push(`fields-${++fieldReads}`); return { secret: "private" }; } };
  const inner: Logger = { get write() { sequence.push("select-inner"); return function (this: Logger, _record: LogRecord) { equal(this, inner); sequence.push("call-inner"); }; } };
  const redactor = { get redact() { sequence.push("select-redactor"); return function (this: unknown, fields: Readonly<Record<string, unknown>>) { equal(this, redactor); sequence.push("call-redactor"); return fields; }; } };
  equal(redactingLogger(inner, redactor, diagnostics).write(input), undefined);
  deepEqual(sequence, ["select-inner", "fields-1", "fields-2", "select-redactor", "fields-3", "call-redactor", "call-inner"]);
  let reads = 0;
  logRecord({ level: "info", message: "safe", get fields() { reads++; return {}; } }, diagnostics);
  equal(reads, 2);
  let diagnosticInputReads = 0;
  createLogRedactor({ get onDiagnostic() { diagnosticInputReads++; throw raw; } } as never);
  equal(diagnosticInputReads, 0);

  const sources = Array.from({ length: 9 }, (_, ordinal) => coreMonitoringValidationDiagnosticRecord({ operation: "signal-definition", field: "signal-intent", reason: "closed-value-rejected", ordinal, effect: "rejected" }));
  const cause = Object.freeze({ diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1), secret: "PRIVATE_LOG_CANARY" });
  events.length = 0; contexts.length = 0;
  const own = coreLoggingBoundaryDiagnosticRecord({ operation: "write", phase: "inner-invocation", field: "logger", reason: "threw", effect: "inner-outcome-unknown" });
  const selected = observeCoreLoggingDiagnostic(diagnostics, own, cause);
  equal(events.length, 10); deepEqual(events.slice(1), sources); equal(selected.relatedDiagnosticRecords?.length, 8);
  deepEqual(contexts, Array.from({ length: 10 }, () => ({ operation: "write", phase: "inner-invocation", field: "logger" })));
  events.length = 0;
  throws(() => redactingLogger({ write() { throw cause; } }, defaultLogRedactor, diagnostics).write(record), (error) => error === cause);
  equal(events.length, 10); deepEqual(events.slice(1), sources);
  events.length = 0;
  let calls = 0, shadowReads = 0;
  const rejected = Promise.reject(cause);
  Object.defineProperty(rejected, "then", { get() { shadowReads++; throw raw; } });
  const asyncLogger: Logger = { write() { calls++; return rejected; } };
  equal(redactingLogger(asyncLogger, defaultLogRedactor, diagnostics).write(record), undefined);
  await new Promise((resolve) => setTimeout(resolve, 0));
  equal(calls, 1); equal(shadowReads, 0); equal(events.length, 10);
  deepEqual(events[0]?.detail, { operation: "write", phase: "inner-invocation", field: "logger", reason: "rejected", effect: "inner-outcome-unknown" });
  events.length = 0;
  redactingLogger({ write() { return { then(_resolve: unknown, reject: (error: unknown) => void) { reject(raw); } }; } }, defaultLogRedactor, diagnostics).write(record);
  await new Promise((resolve) => setTimeout(resolve, 0));
  equal(events.length, 1); equal((events[0]?.detail as { reason?: unknown }).reason, "rejected");
  const sinkOptions: CoreLoggingDiagnosticOptions[] = [
    { get onDiagnostic(): never { throw raw; } },
    { onDiagnostic() { throw raw; } },
    { onDiagnostic() { return Promise.reject(raw); } },
    { onDiagnostic() { return { then(_resolve: unknown, reject: (error: unknown) => void) { reject(raw); } }; } },
    { onDiagnostic() { const value = Promise.reject(raw); Object.defineProperty(value, "then", { get() { throw raw; } }); return value; } },
    { get diagnosticDefinitions(): never { throw raw; } },
  ];
  for (const options of sinkOptions) throws(() => logRecord({ level: "info", get message(): never { throw raw; } }, options), (error) => error === raw);
  await new Promise((resolve) => setTimeout(resolve, 0));
}
loggingDiagnostics().then(() => console.log("packages/core logging runtime test passed.")).catch((error: unknown) => { console.error(error); process.exitCode = 1; });
