import { deepEqual, equal, throws } from "node:assert/strict";
import { systemUuidGenerator } from "../../../../src/shared/index";

// Keep the original supported-runtime smoke, without asserting a random value.
equal(systemUuidGenerator.generate().ok, true);

function withCrypto(crypto: unknown, check: () => void): void {
  const original = Object.getOwnPropertyDescriptor(globalThis, "crypto");
  try {
    Object.defineProperty(globalThis, "crypto", { configurable: true, value: crypto });
    check();
  } finally {
    if (original === undefined) {
      equal(Reflect.deleteProperty(globalThis, "crypto"), true, "remove a test-only Crypto property");
    } else {
      Object.defineProperty(globalThis, "crypto", original);
    }
    deepEqual(Object.getOwnPropertyDescriptor(globalThis, "crypto"), original,
      "each fixture restores the exact original Crypto descriptor");
  }
}

const invalidFormatRecord = {
  schema: "core/diagnostic-record/v1",
  code: "core.shared.uuid-invalid",
  definitionVersion: 1,
  detail: { reason: "invalid-format" },
};
const generatedInvalidRecord = {
  schema: "core/diagnostic-record/v1",
  code: "core.shared.uuid-generation-failed",
  definitionVersion: 1,
  detail: { reason: "generated-value-invalid" },
};
const generationThrewRecord = {
  schema: "core/diagnostic-record/v1",
  code: "core.shared.uuid-generation-failed",
  definitionVersion: 1,
  detail: { reason: "generation-threw" },
};

{
  let calls = 0;
  withCrypto({ randomUUID: () => { calls++; return "A0B1C2D3-E4F5-4A67-8B90-123456789ABC"; } }, () => {
    deepEqual(systemUuidGenerator.generate(), { ok: true, value: "a0b1c2d3-e4f5-4a67-8b90-123456789abc" },
      "generation validates and normalizes the dependency's value");
    equal(calls, 1, "successful generation invokes Crypto once");
  });
}

for (const rejected of ["synthetic-private-generated-uuid", ""]) {
  let calls = 0;
  withCrypto({ randomUUID: () => { calls++; return rejected; } }, () => {
    const actual = systemUuidGenerator.generate();

    deepEqual(actual, {
      ok: false,
      error: {
        code: "UUID_GENERATION_FAILED",
        defaultMessage: "The system could not generate a UUID.",
        diagnosticRecord: generatedInvalidRecord,
        relatedDiagnosticRecords: [invalidFormatRecord],
      },
    }, "invalid generated output preserves its exact primary and validation companion, without raw output");
    equal(calls, 1, "invalid output does not trigger another generation attempt");
  });
}

for (const cause of [new Error("synthetic-private-generation-failure"), "synthetic-private-thrown-value"]) {
  let calls = 0;
  withCrypto({ randomUUID: () => { calls++; throw cause; } }, () => {
    const actual = systemUuidGenerator.generate();

    equal(actual.ok, false, "dependency throws become a returned failure");
    if (actual.ok) throw new Error("Expected UUID generation failure.");
    equal(actual.error.cause, cause, "generation preserves the original thrown value");
    deepEqual(actual.error.diagnosticRecord, generationThrewRecord,
      "the diagnostic describes an invocation failure without copying the cause");
    equal(actual.error.code, "UUID_GENERATION_FAILED");
    equal(actual.error.defaultMessage, "The system could not generate a UUID.");
    equal(actual.error.relatedDiagnosticRecords, undefined, "throws do not invent an invalid-format observation");
    equal(calls, 1, "a thrown dependency is not replayed");
  });
}

for (const crypto of [undefined, {}]) {
  withCrypto(crypto, () => {
    const actual = systemUuidGenerator.generate();

    equal(actual.ok, false, "an unavailable Crypto capability returns failure");
    if (actual.ok) throw new Error("Expected unavailable Crypto failure.");
    equal(actual.error.code, "UUID_GENERATION_FAILED");
    equal(actual.error.defaultMessage, "The system could not generate a UUID.");
    equal(actual.error.cause instanceof TypeError, true, "preserve the observed native access/invocation failure");
    deepEqual(actual.error.diagnosticRecord, generationThrewRecord, "unavailable capability does not prove invalid generated output");
    equal(actual.error.relatedDiagnosticRecords, undefined);
  });
}

const originalCrypto = Object.getOwnPropertyDescriptor(globalThis, "crypto");
const assertionFailure = new Error("synthetic fixture assertion failure");
throws(() => withCrypto({}, () => { throw assertionFailure; }), (error) => error === assertionFailure,
  "fixture restores Crypto even when a case throws");
deepEqual(Object.getOwnPropertyDescriptor(globalThis, "crypto"), originalCrypto, "fixture preserves the exact original Crypto descriptor");

console.log("packages/core shared UUID generation unit tests passed.");
