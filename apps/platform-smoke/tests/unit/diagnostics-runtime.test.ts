import { deepEqual, equal } from "node:assert/strict";
import { platformSmokeAcceptanceFailure } from "../../src/diagnostics";
import { platformSmokeRebuildValidator, platformSmokeWorkItemAcceptanceValidator } from "../../src/app.mount";

deepEqual(platformSmokeRebuildValidator.diagnose?.({})?.detail, { field: "payload.rebuild", reason: "missing" });
deepEqual(platformSmokeRebuildValidator.diagnose?.({ rebuild: "synthetic-sensitive-canary" })?.detail, { field: "payload.rebuild", reason: "wrong-type" });
equal(platformSmokeRebuildValidator.diagnose?.({ rebuild: true }), undefined);
deepEqual(platformSmokeWorkItemAcceptanceValidator.diagnose?.({ password: "synthetic-sensitive-canary" })?.detail, { field: "payload", reason: "unexpected-body" });
deepEqual(platformSmokeAcceptanceFailure("PERSISTENCE_DUPLICATE").detail, { operation: "accept-work-item", reason: "duplicate", effect: "rejected" });
const unknown = platformSmokeAcceptanceFailure("synthetic-sensitive-canary");
deepEqual(unknown.detail, { operation: "accept-work-item", reason: "operation-failed", effect: "unknown" });
equal(JSON.stringify(unknown).includes("synthetic-sensitive-canary"), false);
console.log("App-owned attribute and uncertain-operation diagnostics passed.");
