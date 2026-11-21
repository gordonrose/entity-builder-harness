import { deepEqual, equal } from "node:assert/strict";
import { uuid } from "../../../../src/shared/index";

const parsedUuid = uuid("A0B1C2D3-E4F5-4A67-8B90-123456789ABC");
equal(parsedUuid.ok, true);
if (!parsedUuid.ok) throw new Error("Expected UUID parsing to succeed.");
equal(parsedUuid.value, "a0b1c2d3-e4f5-4a67-8b90-123456789abc");
const invalidUuid = uuid("not-a-uuid");
equal(invalidUuid.ok, false);
if (invalidUuid.ok) throw new Error("Expected invalid UUID to fail.");
equal(invalidUuid.error.code, "INVALID_UUID");

const expectedInvalid = {
  ok: false,
  error: {
    code: "INVALID_UUID",
    defaultMessage: "Expected a valid UUID string.",
    diagnosticRecord: {
      schema: "core/diagnostic-record/v1",
      code: "core.shared.uuid-invalid",
      definitionVersion: 1,
      detail: { reason: "invalid-format" },
    },
  },
};
deepEqual(invalidUuid, expectedInvalid, "invalid UUID retains its exact public error and diagnostic");

for (const input of [
  "a0b1c2d3-e4f5-1a67-8b90-123456789abc",
  "a0b1c2d3-e4f5-2a67-8b90-123456789abc",
  "a0b1c2d3-e4f5-3a67-8b90-123456789abc",
  "a0b1c2d3-e4f5-4a67-8b90-123456789abc",
  "a0b1c2d3-e4f5-5a67-8b90-123456789abc",
  "a0b1c2d3-e4f5-4a67-9b90-123456789abc",
  "a0b1c2d3-e4f5-4a67-ab90-123456789abc",
  "a0b1c2d3-e4f5-4a67-bb90-123456789abc",
]) {
  deepEqual(uuid(input), { ok: true, value: input }, `supported version/variant is accepted unchanged: ${input}`);
}

for (const [label, input] of [
  ["empty", ""],
  ["private malformed input", "synthetic-private-uuid"],
  ["leading whitespace", " a0b1c2d3-e4f5-4a67-8b90-123456789abc"],
  ["trailing whitespace", "a0b1c2d3-e4f5-4a67-8b90-123456789abc "],
  ["trailing newline", "a0b1c2d3-e4f5-4a67-8b90-123456789abc\n"],
  ["missing separators", "a0b1c2d3e4f54a678b90123456789abc"],
  ["non-hexadecimal character", "g0b1c2d3-e4f5-4a67-8b90-123456789abc"],
  ["version zero", "a0b1c2d3-e4f5-0a67-8b90-123456789abc"],
  ["version six", "a0b1c2d3-e4f5-6a67-8b90-123456789abc"],
  ["version seven outside the current contract", "a0b1c2d3-e4f5-7a67-8b90-123456789abc"],
  ["variant below the accepted range", "a0b1c2d3-e4f5-4a67-7b90-123456789abc"],
  ["variant above the accepted range", "a0b1c2d3-e4f5-4a67-cb90-123456789abc"],
  ["overlong", "a0b1c2d3-e4f5-4a67-8b90-123456789abc0"],
] as const) {
  deepEqual(uuid(input), expectedInvalid, `${label}: exact rejection with no supplied value in the error`);
}

console.log("packages/core shared UUID parsing unit tests passed.");
