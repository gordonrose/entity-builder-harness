import { deepEqual, equal, throws } from "node:assert/strict";
import { validateConfigRequirements } from "@kanbien/core/config";
import { validatePersistenceMigrationInstructions, validatePersistenceVerificationInstructions,
  persistenceConnectionDiagnosticMode, persistenceMigrationRequirements, persistenceExpectedRecordRequirements,
  persistenceMaintenanceDiagnosticCatalog, type PersistenceInstructionCheck } from "../src/index";

const id = "core-persistence-acceptance-v1", digest = "a".repeat(64), canary = "synthetic-private-N03-canary";
const expected = { "verification.expected-record-id": id, "verification.expected-fingerprint": digest };
const migration = "persistence.migration-instructions-invalid", verification = "persistence.verification-instructions-invalid";
function failure(code: string, issues: readonly { setting: string; reason: string }[]) {
  return { ok: false, error: { code: "CONFIGURATION_INVALID", diagnostic: { schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail: { issues } } } };
}
equal(persistenceMaintenanceDiagnosticCatalog.definitions.length, 2);
for (const operation of [undefined, "apply"]) deepEqual(validatePersistenceMigrationInstructions(operation), { ok: true, value: { operation: "apply" } });
for (const [value, reason] of [[false, "wrong-type"], ["", "blank"], [" \t", "blank"], [" apply ", "surrounding-whitespace"], [canary, "unsupported-value"]] as const) {
  const result = validatePersistenceMigrationInstructions(value);
  deepEqual(result, failure(migration, [{ setting: "migration.operation", reason }]));
  equal(JSON.stringify(result).includes(canary), false);
}
deepEqual(validatePersistenceVerificationInstructions(canary, expected), failure(verification, [{ setting: "verification.mode", reason: "unsupported-value" }]));
deepEqual(validatePersistenceVerificationInstructions(canary, { "verification.expected-record-id": undefined, "verification.expected-fingerprint": undefined }),
  failure(verification, [{ setting: "verification.mode", reason: "unsupported-value" }]), "unsupported mode does not invent requirements for that mode");
for (const mode of [undefined, null, false, 1, "", " \t", " connection "]) {
  deepEqual(validatePersistenceVerificationInstructions(mode, expected), { ok: true, value: { mode: "verify-record", expected: { recordId: id, factDigest: digest } } });
  equal(persistenceConnectionDiagnosticMode(mode), false);
}
deepEqual(validatePersistenceVerificationInstructions("connection", { "verification.expected-record-id": false, "verification.expected-fingerprint": canary }), { ok: true, value: { mode: "connection" } });
equal(persistenceConnectionDiagnosticMode("connection"), true);
for (const key of ["verification.expected-record-id", "verification.expected-fingerprint"] as const) {
  for (const [value, reason] of [[undefined, "missing"], [false, "wrong-type"], [" \n", "blank"], [" value ", "surrounding-whitespace"], [canary, "invalid-format"]] as const) {
    const result = validatePersistenceVerificationInstructions(undefined, { ...expected, [key]: value });
    deepEqual(result, failure(verification, [{ setting: key, reason }]));
    equal(JSON.stringify(result).includes(canary), false);
  }
}
deepEqual(validatePersistenceVerificationInstructions(undefined, { "verification.expected-record-id": undefined, "verification.expected-fingerprint": "x" }), failure(verification, [
  { setting: "verification.expected-record-id", reason: "missing" }, { setting: "verification.expected-fingerprint", reason: "invalid-format" },
]));
for (const suffix of ["a".repeat(8), "z-9".repeat(26) + "ab"]) equal(validatePersistenceVerificationInstructions(undefined, { ...expected, "verification.expected-record-id": "core-persistence-" + suffix }).ok, true);
for (const suffix of ["a".repeat(7), "a".repeat(81), "UPPERCASE", "bad_name"]) equal(validatePersistenceVerificationInstructions(undefined, { ...expected, "verification.expected-record-id": "core-persistence-" + suffix }).ok, false);
for (const value of ["a".repeat(63), "a".repeat(65), "A".repeat(64), "g".repeat(64)]) equal(validatePersistenceVerificationInstructions(undefined, { ...expected, "verification.expected-fingerprint": value }).ok, false);

let calls = 0;
const checkedUse: PersistenceInstructionCheck = (source, requirements) => {
  calls++;
  const checked = validateConfigRequirements(source, requirements);
  return checked.ok && requirements === persistenceExpectedRecordRequirements ? { ok: true, value: { ...checked.value,
    "verification.expected-record-id": "core-persistence-checked-v1", "verification.expected-fingerprint": "b".repeat(64) } } : checked;
};
deepEqual(validatePersistenceVerificationInstructions(undefined, expected, checkedUse), { ok: true, value: { mode: "verify-record", expected: { recordId: "core-persistence-checked-v1", factDigest: "b".repeat(64) } } });
equal(calls, 1, "use the shared checker's returned values");
const rejected: PersistenceInstructionCheck = () => ({ ok: false, error: { code: "CONFIGURATION_INVALID", issues: [{ setting: "migration.operation", reason: "unsupported-value" }] } });
deepEqual(validatePersistenceMigrationInstructions("apply", rejected), failure(migration, [{ setting: "migration.operation", reason: "unsupported-value" }]), "do not ignore a returned shared rejection");
let sourceReads = 0;
const thrown = Object.freeze(new Error(canary));
const throwing = Object.defineProperty({ ...expected }, "verification.expected-record-id", { get() { sourceReads++; throw thrown; } });
throws(() => validatePersistenceVerificationInstructions(undefined, throwing), error => error === thrown);
equal(sourceReads, 1);
const varied: PersistenceInstructionCheck = (source, requirements) => validateConfigRequirements(source,
  requirements === persistenceMigrationRequirements ? [{ setting: "migration.operation", rule: { kind: "choice", values: ["apply", "fixture"] } }] : requirements);
equal(validatePersistenceMigrationInstructions("fixture", varied).ok, true, "finite choices are supplied to the shared checker, not recoded as an independent membership guard");
console.log("Persistence maintenance configuration runtime tests passed: fifteen failures, compatibility, aggregation, checked values and source identity.");
