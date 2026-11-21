import { deepEqual, equal, throws } from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { recordConfigSource, destinationPortConstraint, type ConfigSettingRequirement } from "@kanbien/core/config";
import * as core from "@kanbien/core/config";
import { loadPlatformConfiguration } from "../../src/index";

const requirements = [{ setting: "database.port", rule: destinationPortConstraint }] as const satisfies readonly ConfigSettingRequirement[];
const bindings = { "database.port": "DATABASE_PORT" };
let assembled = 0;
const load = (value: string | undefined) => loadPlatformConfiguration({
  requirements, bindings, source: recordConfigSource({ DATABASE_PORT: value, PRIVATE: "synthetic-private-canary" }),
  assemble(values) { assembled++; return { ok: true as const, value: { port: values["database.port"] } }; },
});
deepEqual(load("443"), { ok: true, value: { port: 443 } });
for (const [value, reason] of [[undefined, "missing"], ["-20", "out-of-range"], [" ", "blank"], [" 443", "surrounding-whitespace"], ["1e3", "invalid-integer"]] as const) {
  deepEqual(load(value), { ok: false, error: { code: "CONFIGURATION_INVALID", issues: [{ setting: "database.port", reason }] } });
}
equal(assembled, 1, "invalid values must not reach assembly");
const readOrder: string[] = [];
const multi = loadPlatformConfiguration({
  requirements: [...requirements, { setting: "service.name", rule: { kind: "text" } }],
  bindings: { ...bindings, "service.name": "SERVICE_NAME" },
  source: { get(key) { readOrder.push(key); return key === "DATABASE_PORT" ? "-20" : " "; } },
  assemble() { throw new Error("must-not-assemble"); },
});
deepEqual(readOrder, ["DATABASE_PORT", "SERVICE_NAME"]);
deepEqual(multi, { ok: false, error: { code: "CONFIGURATION_INVALID", issues: [
  { setting: "database.port", reason: "out-of-range" }, { setting: "service.name", reason: "blank" },
] } });
const relation = loadPlatformConfiguration({
  requirements: [{ setting: "first", rule: { kind: "text" } }, { setting: "second", rule: { kind: "text" } }],
  bindings: { first: "FIRST", second: "SECOND" }, source: recordConfigSource({ FIRST: "same", SECOND: "same" }),
  relationships: [{ relationship: "separation", rule: "must-differ", left: "first", right: "second" }],
  assemble() { throw new Error("must-not-assemble-relationship-failure"); },
});
equal(relation.ok, false);
if (!relation.ok && relation.error.code === "CONFIGURATION_INVALID" && "relationshipIssues" in relation.error)
  deepEqual(relation.error.relationshipIssues, [{ relationship: "separation", rule: "must-differ", left: "first", right: "second" }]);

let reads = 0, getters = 0;
const source = { get() { reads++; return "443"; } };
for (const [badBindings, reason] of [
  [{}, "identity-count-mismatch"], [{ ...bindings, extra: "PRIVATE" }, "identity-count-mismatch"],
  [{ "database.port": " PRIVATE " }, "invalid-format"], [{ "database.port": "constructor" }, "reserved"],
  [Object.defineProperty({}, "database.port", { enumerable: true, get() { getters++; return "PRIVATE"; } }), "missing"],
] as const) {
  throws(() => loadPlatformConfiguration({ requirements, bindings: badBindings as Record<string, string>, source, assemble: values => ({ ok: true, value: values }) }),
    (error: unknown) => {
      const failure = error as TypeError & { diagnosticRecord: { code: string; detail: unknown } };
      equal(failure.message, "PLATFORM_CONFIGURATION_LOADING_DECLARATION_INVALID");
      equal(failure.diagnosticRecord.code, "platform-config.loading-declaration-invalid");
      deepEqual(failure.diagnosticRecord.detail, { field: "bindings", reason, effect: "not-started" });
      equal(JSON.stringify(failure).includes("PRIVATE"), false);
      return true;
    });
}
equal(reads, 0); equal(getters, 0);

const thrown = new Error("synthetic-source-canary");
throws(() => loadPlatformConfiguration({ requirements, bindings, source: { get() { throw thrown; } }, assemble: values => ({ ok: true, value: values }) }),
  error => error === thrown);
const assemblyThrown = new Error("synthetic-assembly-canary");
throws(() => loadPlatformConfiguration({ requirements, bindings, source: recordConfigSource({ DATABASE_PORT: "443" }), assemble() { throw assemblyThrown; } }),
  error => error === assemblyThrown);
const assemblyFailure = { code: "FIXTURE_ASSEMBLY_REJECTED" };
deepEqual(loadPlatformConfiguration({ requirements, bindings, source: recordConfigSource({ DATABASE_PORT: "443" }), assemble: () => ({ ok: false, error: assemblyFailure }) }),
  { ok: false, error: assemblyFailure });

// Exercise the actual coordinator with an injected Core result, not a copied implementation.
const filename = require.resolve("../../src/domain/loading"), local = createRequire(filename);
const fixture = { exports: {} as typeof import("../../src/domain/loading") };
let checks = 0;
new Function("require", "module", "exports", readFileSync(filename, "utf8"))(
  (name: string) => name === "@kanbien/core/config" ? { ...core, validateConfigRequirements() { checks++; return { ok: true, value: { "database.port": 444 } }; } } : local(name),
  fixture, fixture.exports,
);
deepEqual(fixture.exports.loadPlatformConfiguration({ requirements, bindings, source: recordConfigSource({ DATABASE_PORT: "443", PRIVATE: "synthetic-private-canary" }),
  assemble: values => ({ ok: true, value: values }) }), { ok: true, value: { "database.port": 444 } });
equal(checks, 1, "the coordinator must call the shared checker and use its returned values");
console.log("platform/config loading runtime test passed.");
