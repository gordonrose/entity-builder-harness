import { deepEqual, equal } from "node:assert/strict";
import { defineDiagnostic } from "@kanbien/core/diagnostics";
import { createPlatformRuntimeRegistry } from "../../src/index";
import { platformAppId, validatePlatformDiagnosticCatalog } from "@kanbien/platform-contracts";
const definition = defineDiagnostic({ code: "fixture.invalid", version: 1,
  classification: { failureKind: "validation", failureSource: "app", severity: "warning", recovery: "user_correctable" },
  detail: { type: "object", properties: { reason: { type: "enum", values: ["invalid"] } } },
} as const);
const catalog = { owner: "fixture", definitions: [definition] };
const registry = createPlatformRuntimeRegistry();
equal(registry.registerDiagnosticCatalog(catalog).ok, true);
equal(registry.registerDiagnosticCatalog(catalog).ok, false);
equal(registry.diagnosticCatalogs().length, 1);
const app = platformAppId("other");
if (!app.ok) throw new Error("fixture-invalid");
equal(createPlatformRuntimeRegistry().forApp(app.value).registerDiagnosticCatalog(catalog).ok, false);
equal(validatePlatformDiagnosticCatalog({ ...catalog, owner: 1 } as never).ok, false);
equal(validatePlatformDiagnosticCatalog({ ...catalog, raw: "synthetic-sensitive-canary" } as never).ok, false);
let accessed = false;
const definitions = Object.defineProperty([definition], "0", { get() { accessed = true; throw new Error("synthetic-sensitive-canary"); } });
equal(validatePlatformDiagnosticCatalog({ owner: "fixture", definitions }).ok, false);
equal(accessed, false, "catalog validation cannot evaluate definition accessors");
const snapshot = registry.diagnosticCatalogs();
(snapshot[0] as { owner: string }).owner = "modified";
equal(registry.diagnosticCatalogs()[0]?.owner, "fixture", "returned catalog snapshots cannot mutate registration");
console.log("Production diagnostic catalog registration passed.");
const classes = ["APP_FIXED"];
let arrayGets = 0;
const suppliedClasses = new Proxy(classes, { get() { arrayGets++; throw new Error("array-get-canary"); } });
equal(registry.registerObservabilityProfile({ name: "fixture.profile" as never, capability: "fixture.action" as never, action: "execute", signals: ["metric"], errorClasses: suppliedClasses }).ok, true);
classes.push("PRIVATE_VALID_TOKEN");
deepEqual(registry.observabilityProfiles()[0]?.errorClasses, ["APP_FIXED"]);
equal(Object.isFrozen(registry.observabilityProfiles()[0]?.errorClasses), true);
equal(arrayGets, 0);
for (const mode of ["invalid", "oversized", "throw"] as const) {
  let snapshots = 0;
  const changingClasses = new Proxy(["APP_FIXED"], { getOwnPropertyDescriptor(target, key) {
    if (key === "length") {
      snapshots++;
      if (snapshots === 2 && mode === "throw") throw new Error("private-snapshot-canary");
      if (snapshots === 2 && mode === "oversized") return { ...Reflect.getOwnPropertyDescriptor(target, key)!, value: 65 };
    }
    if (key === "0" && snapshots === 2 && mode === "invalid") return { ...Reflect.getOwnPropertyDescriptor(target, key)!, value: "private-snapshot-canary@example.invalid" };
    return Reflect.getOwnPropertyDescriptor(target, key);
  } });
  const rejected = registry.registerObservabilityProfile({ name: ("fixture." + mode) as never, capability: "fixture.action" as never, action: "execute", signals: ["metric"], errorClasses: changingClasses });
  equal(rejected.ok, false);
  if (rejected.ok) throw new Error("Changing declaration must be rejected.");
  deepEqual(rejected.error.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "platform-contracts.registration-rejected", definitionVersion: 2,
    detail: { registration: "observability-profile", field: "errorClasses",
      condition: mode === "invalid" ? "member-invalid-format" : mode === "oversized" ? "too-many-members" : "inspection-threw",
      ...(mode === "invalid" ? { index: 0 } : {}), phase: "validation", effect: "rejected" } });
  equal(registry.observabilityProfiles().length, 1);
}
let declarationReads = 0;
const changingProfile = new Proxy({ name: "fixture.changed" as never, capability: "fixture.action" as never, action: "execute" as const, signals: ["metric"] as const, errorClasses: ["APP_FIXED"] }, {
  getOwnPropertyDescriptor(target, key) {
    const descriptor = Reflect.getOwnPropertyDescriptor(target, key);
    if (key === "errorClasses" && ++declarationReads >= 2) return { ...descriptor!, value: undefined };
    return descriptor;
  },
  get(target, key, receiver) { return key === "errorClasses" ? ["PRIVATE_VALID_TOKEN"] : Reflect.get(target, key, receiver); },
});
equal(registry.registerObservabilityProfile(changingProfile).ok, true);
equal(registry.observabilityProfiles()[1]?.errorClasses, undefined, "a failed/empty snapshot cannot retain raw spread data");
equal(registry.registerObservabilityProfile({ name: "fixture.absent" as never, capability: "fixture.action" as never, action: "execute", signals: ["metric"] }).ok, true);
equal(Object.hasOwn(registry.observabilityProfiles()[2]!, "errorClasses"), false);
