import { deepEqual, equal, ok, rejects } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { definePlatformApp, platformAppId } from "@kanbien/platform-contracts";
import { mountPlatformAppForTest, type PlatformTestMountOptions } from "../src/index";

const canary = "synthetic-private-mount-evidence-canary";
const slots = ["primary", "related-0", "related-1", "related-2", "related-3", "related-4", "related-5", "related-6", "related-7"] as const;
const definition = defineDiagnostic({ code: "mount-fixture.failure", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { slot: { type: "enum", values: slots } } },
} as const);
const catalog = { owner: "mount-fixture", definitions: [definition] };
const appId = platformAppId("mount-fixture");
ok(appId.ok);
const id = appId.value;
const records: readonly DiagnosticRecord[] = slots.map((slot) => {
  const checked = createDiagnosticRecord(definition, { slot }); ok(checked.ok); return checked.value;
});
const primary = records[0]!, companions = records.slice(1);

async function failure(cause: unknown, registered: boolean, options: PlatformTestMountOptions = {}) {
  let mounts = 0;
  const result = await mountPlatformAppForTest(definePlatformApp({ id, name: "Mount evidence fixture", mount(registry) {
    mounts++;
    if (registered) equal(registry.registerDiagnosticCatalog(catalog).ok, true);
    throw cause;
  } }), options);
  equal(mounts, 1); equal(result.ok, false); ok(!result.ok);
  equal(result.error.code, "PLATFORM_TEST_MOUNT_FAILED");
  equal(result.error.defaultMessage, "Platform app failed to mount in the test registry.");
  deepEqual(result.error.contractErrors, []);
  equal(Object.hasOwn(result.error, "cause"), false);
  return result.error;
}

async function main(): Promise<void> {
  for (const mode of ["registered", "explicit"] as const) {
    const registered = mode === "registered", options = registered ? {} : { diagnosticDefinitions: [definition] };
    let causeReads = 0;
    const native = Object.assign(new Error("Historical mount reason."), { diagnosticRecord: primary, relatedDiagnosticRecords: companions, token: canary });
    Object.defineProperty(native, "cause", { get() { causeReads++; throw new Error(canary); } });
    const retained = await failure(native, registered, options);
    deepEqual(retained.diagnosticRecord, primary); deepEqual(retained.relatedDiagnosticRecords, companions);
    deepEqual(retained.details, { reason: "Historical mount reason." }); equal(causeReads, 0);
    equal(JSON.stringify(retained).includes(canary), false, "native extras and causes are not serialized into the test result");

    const malformed = { ...primary, detail: { slot: canary } };
    const rejectedPrimary = await failure(Object.assign(new Error("Legacy malformed-primary reason."), { diagnosticRecord: malformed, relatedDiagnosticRecords: companions }), registered, options);
    equal(rejectedPrimary.diagnosticRecord, undefined); deepEqual(rejectedPrimary.relatedDiagnosticRecords, companions);
    equal(JSON.stringify(rejectedPrimary).includes(canary), false, "a rejected primary does not erase selected companions or expose unchecked detail");

    let primaryReads = 0;
    const accessor = Object.defineProperty(Object.assign(new Error("Legacy accessor reason."), { relatedDiagnosticRecords: companions }), "diagnosticRecord", { get() { primaryReads++; throw new Error(canary); } });
    const ignoredAccessor = await failure(accessor, registered, options);
    equal(primaryReads, 0); equal(ignoredAccessor.diagnosticRecord, undefined); deepEqual(ignoredAccessor.relatedDiagnosticRecords, companions);

    let relatedReads = 0;
    const relatedAccessor = Object.defineProperty(Object.assign(new Error("Legacy companion accessor reason."), { diagnosticRecord: primary }), "relatedDiagnosticRecords", { get() { relatedReads++; throw new Error(canary); } });
    const ignoredRelated = await failure(relatedAccessor, registered, options);
    equal(relatedReads, 0); deepEqual(ignoredRelated.diagnosticRecord, primary); equal(ignoredRelated.relatedDiagnosticRecords, undefined);

    const mixed = await failure({ diagnosticRecord: primary, relatedDiagnosticRecords: [malformed, companions[0], { ...primary, code: "unselected.failure" }, companions[1]], message: canary, cause: native }, registered, options);
    deepEqual(mixed.diagnosticRecord, primary); deepEqual(mixed.relatedDiagnosticRecords, companions.slice(0, 2));
    deepEqual(mixed.details, { reason: "Unknown app mount failure." }); equal(JSON.stringify(mixed).includes(canary), false);
  }

  const unselected = await failure({ diagnosticRecord: primary, relatedDiagnosticRecords: companions, message: canary }, false);
  equal(unselected.diagnosticRecord, undefined); deepEqual(unselected.relatedDiagnosticRecords, []);
  deepEqual(unselected.details, { reason: "Unknown app mount failure." });

  let messageReads = 0;
  const legacyMessage = Object.defineProperty(new Error(), "message", { get() { messageReads++; return canary; } });
  const historical = await failure(legacyMessage, false);
  equal(messageReads, 1); deepEqual(historical.details, { reason: canary }, "the helper's historical Error.message result remains compatible, separate from safe diagnostic detail");
  equal(historical.diagnosticRecord, undefined);
  const messageFailure = new Error("Synthetic message getter failure.");
  const throwingMessage = Object.defineProperty(new Error(), "message", { get() { throw messageFailure; } });
  await rejects(failure(throwingMessage, false), (error) => error === messageFailure, "the original Error.message getter rejection is not replaced by optional evidence");
  console.log("Testing mount boundary diagnostics: registered/explicit primary plus eight companions, selected closure, privacy and legacy message behavior passed.");
}
void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
