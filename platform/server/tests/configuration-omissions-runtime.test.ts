import { deepEqual, equal, throws } from "node:assert/strict";
import { resolvePlatformReleaseIdentity, resolvePlatformServerRuntimeConfigurationWithDiagnostics } from "../src/index";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";

const canary = "synthetic-private-omission-canary";
for (const [value, reason] of [[undefined, "missing"], ["", "empty"], [" ", "normalization-empty"], [", ,", "normalization-empty"]] as const) {
  const observation = resolvePlatformServerRuntimeConfigurationWithDiagnostics({ env: { PLATFORM_CORS_ALLOWLIST: value } });
  const omissions = observation.diagnosticRecords.filter((record) => record.code === "platform-server.configuration-omitted");
  deepEqual(omissions.map((record) => record.detail), [
    { phase: "configuration", setting: "http.cors-origin", reason: "missing", effect: "omitted" },
    { phase: "configuration", setting: "http.cors-allowlist", reason, effect: "omitted" },
    { phase: "configuration", setting: "release.source-commit", reason: "missing", effect: "omitted" },
  ]);
}
for (const origin of [" ", canary, "*", "https://one.test,https://two.test"]) {
  const observation = resolvePlatformServerRuntimeConfigurationWithDiagnostics({ env: {
    PLATFORM_CORS_ORIGIN: origin, PLATFORM_CORS_ALLOWLIST: " https://one.test, https://one.test ",
    PLATFORM_SOURCE_COMMIT_SHA: "release_1",
  } });
  equal(observation.configuration.corsOrigin, origin, "origin grammar and whitespace are not tightened");
  deepEqual(observation.configuration.corsAllowlist, ["https://one.test", "https://one.test"], "existing duplicates survive");
  equal(observation.diagnosticRecords.length, 4);
  equal(JSON.stringify(observation.diagnosticRecords).includes(canary), false);
}
for (const [value, reason] of [[undefined, "missing"], ["", "empty"], [" ", "format-rejected"], ["private/token", "format-rejected"]] as const) {
  const records: DiagnosticRecord[] = [];
  deepEqual(resolvePlatformReleaseIdentity(value, (record) => { records.push(record); }), {});
  deepEqual(records, [{ schema: "core/diagnostic-record/v1", code: "platform-server.configuration-omitted", definitionVersion: 1,
    detail: { phase: "configuration", setting: "release.source-commit", reason, effect: "omitted" } }]);
  deepEqual(resolvePlatformReleaseIdentity(value, () => { throw new Error(canary); }), {});
  deepEqual(resolvePlatformReleaseIdentity(value, () => Promise.reject(new Error(canary))), {});
  equal(JSON.stringify(records).includes("private/token"), false);
}
let coercions = 0;
const object = { toString() { coercions++; return "accepted"; } };
deepEqual(resolvePlatformReleaseIdentity(object as unknown as string), { sourceCommitSha: object });
equal(coercions, 1, "original regular-expression coercion occurs once");
const thrown = new Error(canary);
let attempts = 0;
throws(() => resolvePlatformReleaseIdentity({ toString() { attempts++; throw thrown; } } as unknown as string), (error: unknown) => error === thrown);
equal(attempts, 1);
console.log("Server existing CORS/release omissions retain grammar, coercion, privacy and observer isolation.");
