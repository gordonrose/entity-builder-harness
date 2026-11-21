import { deepEqual, equal, rejects } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformAppId, type PlatformApp, type PlatformDiagnosticCatalog } from "@kanbien/platform-contracts";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { mountPlatformRuntimeApps } from "../../src/index";
const secret = "private-mount-canary@example.invalid";
const cause = new Error(secret);
const checkedId = platformAppId("fixture"); if (!checkedId.ok) throw new Error("Fixture invalid");
const id = checkedId.value;
function detail(record: DiagnosticRecord | undefined, phase: string, boundary: string, effect: string, ordinal?: number): void {
  equal(record?.code, "platform-runtime.boundary-failed"); equal(record?.definitionVersion, 1);
  deepEqual(record?.detail, { operation: "mount", phase, subject: phase === "registry-construction" || phase === "registry-validation" || phase === "mount-projection" ? "runtime" : "app", boundary, effect, ...(ordinal === undefined ? {} : { ordinal }) });
  equal(JSON.stringify(record).includes(secret), false);
}
async function main(): Promise<void> {
  const emitted: DiagnosticRecord[] = [];
  let receiver: unknown, idReads = 0, depsReads = 0;
  const app: PlatformApp = { get id() { idReads++; return id; }, name: secret, mount() { receiver = this; throw cause; } };
  let result = await mountPlatformRuntimeApps({ apps: [app], get deps() { depsReads++; return createPlatformTestMountDeps(); }, onDiagnostic(r) { emitted.push(r); } });
  equal(result.ok, false); if (result.ok) throw new Error("Expected failure");
  equal(result.error.code, "PLATFORM_RUNTIME_APP_MOUNT_FAILED"); equal(result.error.defaultMessage, "Platform app failed during runtime mount.");
  equal(result.error.cause, cause); deepEqual(result.error.details, { appId: id }); equal(receiver, app); equal(idReads, 4); equal(depsReads, 1);
  detail(result.error.diagnosticRecord, "app-mount", "invocation", "step-completion-unobserved", 0); equal(emitted.length, 1);
  emitted.length = 0;
  result = await mountPlatformRuntimeApps({ apps: [{ id, name: secret, mount: () => Promise.reject(cause) }], deps: createPlatformTestMountDeps(), onDiagnostic(r) { emitted.push(r); } });
  equal(result.ok, false); detail(emitted[0], "app-mount", "completion", "step-completion-unobserved", 0);
  emitted.length = 0;
  let mountReads = 0;
  result = await mountPlatformRuntimeApps({ apps: [{ id, name: secret, get mount(): never { mountReads++; throw cause; } }], get deps(): never { throw new Error("Should not read deps"); }, onDiagnostic(r) { emitted.push(r); } });
  equal(result.ok, false); equal(mountReads, 1); detail(emitted[0], "app-mount", "selection", "step-not-invoked", 0);
  emitted.length = 0;
  await rejects(mountPlatformRuntimeApps({ apps: [{ get id(): never { throw cause; }, name: secret, mount() {} }], deps: createPlatformTestMountDeps(), onDiagnostic(r) { emitted.push(r); } }), (error) => error === cause);
  detail(emitted[0], "app-identity", "selection", "step-not-invoked", 0);

  // A catch-projection getter supersedes the mount failure exactly as before; both locations remain observable.
  emitted.length = 0; idReads = 0; const projectionError = new Error("projection");
  await rejects(mountPlatformRuntimeApps({ apps: [{ get id() { if (++idReads === 4) throw projectionError; return id; }, name: secret, mount() { throw cause; } }], deps: createPlatformTestMountDeps(), onDiagnostic(r) { emitted.push(r); } }), (error) => error === projectionError);
  equal(idReads, 4); equal(emitted.length, 2);
  detail(emitted[0], "app-mount", "invocation", "step-completion-unobserved", 0);
  detail(emitted[1], "mount-error-projection", "projection", "boundary-outcome-unknown", 0);

  emitted.length = 0;
  const iterable = { *[Symbol.iterator]() { yield { id, name: secret, mount() {} }; throw cause; } };
  await rejects(mountPlatformRuntimeApps({ apps: iterable as never, deps: createPlatformTestMountDeps(), onDiagnostic(r) { emitted.push(r); } }), (error) => error === cause);
  detail(emitted[0], "app-iteration", "iteration", "boundary-outcome-unknown");
  emitted.length = 0;
  await rejects(mountPlatformRuntimeApps({ get registryOptions(): never { throw cause; }, apps: [], deps: createPlatformTestMountDeps(), onDiagnostic(r) { emitted.push(r); } }), (error) => error === cause);
  detail(emitted[0], "registry-construction", "selection", "boundary-outcome-unknown");

  const definition = defineDiagnostic({ code: "fixture.mount-failure", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" }, detail: { type: "object", properties: {} } });
  const checked = createDiagnosticRecord(definition, {}); if (!checked.ok) throw new Error("Fixture invalid");
  const catalog = { owner: "fixture", definitions: [definition] };
  const source = { diagnosticRecord: checked.value, relatedDiagnosticRecords: Array.from({ length: 8 }, () => checked.value) };
  emitted.length = 0; let snapshots: readonly PlatformDiagnosticCatalog[] | undefined, selectedReads = 0;
  result = await mountPlatformRuntimeApps({ apps: [{ id, name: secret, mount(registry) { equal(registry.registerDiagnosticCatalog(catalog).ok, true); throw source; } }], deps: createPlatformTestMountDeps(),
    get diagnosticDefinitions() { selectedReads++; return []; }, onDiagnostic(r, context, catalogs) { equal(context.stage, "startup"); snapshots = catalogs; emitted.push(r); } });
  equal(result.ok, false); if (result.ok) throw new Error("Expected failure");
  equal(result.error.diagnosticRecord?.code, definition.code); equal(result.error.relatedDiagnosticRecords?.length, 8); equal(emitted.length, 10); equal(selectedReads, 1);
  equal(snapshots?.length, 1); equal(snapshots?.[0]?.owner, "fixture");
  detail(emitted[0], "app-mount", "invocation", "step-completion-unobserved", 0);
  equal((await mountPlatformRuntimeApps({ apps: [], deps: createPlatformTestMountDeps(), get diagnosticDefinitions(): never { throw cause; }, onDiagnostic(): never { throw cause; } })).ok, true);
  // Invalid/unselected/accessor evidence never gains admission merely because mounting failed.
  for (const [upstream, inaccessible] of [[{ diagnosticRecord: { ...checked.value, definitionVersion: 2 } }, false], [{ diagnosticRecord: checked.value }, false], [{ get diagnosticRecord(): never { throw new Error("No getter"); } }, true]] as const) {
    emitted.length = 0;
    result = await mountPlatformRuntimeApps({ apps: [{ id, name: secret, mount() { throw upstream; } }], deps: createPlatformTestMountDeps(), onDiagnostic(r) { emitted.push(r); return Promise.reject(cause); } });
    equal(result.ok, false); if (result.ok) throw new Error("Expected failure"); equal(result.error.cause, upstream);
    equal(result.error.diagnosticRecord?.code, "platform-runtime.boundary-failed"); equal(emitted.length, inaccessible ? 2 : 1);
    if (inaccessible) deepEqual(emitted[1], { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason: "evidence-inaccessible" } });
  }
}
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
