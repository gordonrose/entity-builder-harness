import { deepEqual, equal } from "node:assert/strict";
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
} from "../src/logging/index";

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

console.log("packages/core logging runtime test passed.");
