import { deepEqual, equal, throws } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { type CorrelationId, type ISODateTime } from "@kanbien/core/shared";
import type { QueueMessageType } from "@kanbien/core/queues";
import { platformJobName } from "@kanbien/platform-contracts";
import { createPlatformTestQueueMessage } from "@kanbien/platform-testing";
import { createPlatformRuntimeContextDeps, createPlatformRuntimeJobContext, createPlatformRuntimeRequestContext } from "../src/index";

const secret = "private-context-canary@example.invalid";
const cause = new Error(secret);
const request = { requestId: secret as CorrelationId, method: "GET" as const, path: secret };
const now = "2026-01-01T00:00:00.000Z" as ISODateTime;
const jobName = platformJobName("fixture.job"); if (!jobName.ok) throw new Error("Invalid fixture");
const job = { jobName: jobName.value, message: createPlatformTestQueueMessage({ type: "fixture.message" as QueueMessageType }), correlationId: secret as CorrelationId };
function expected(record: DiagnosticRecord | undefined, operation: string, phase: string, boundary: string): void {
  equal(record?.schema, "core/diagnostic-record/v1"); equal(record?.code, "platform-runtime.boundary-failed"); equal(record?.definitionVersion, 1);
  deepEqual(record?.detail, { operation, phase, subject: "context", boundary, effect: "context-not-returned" });
  equal(JSON.stringify(record).includes(secret), false);
}
for (const [operation, create] of [
  ["request-context", (input: object) => createPlatformRuntimeRequestContext(Object.defineProperties({ ...request }, Object.getOwnPropertyDescriptors(input)))],
  ["job-context", (input: object) => createPlatformRuntimeJobContext(Object.defineProperties({ ...job }, Object.getOwnPropertyDescriptors(input)))],
] as const) {
  const emitted: DiagnosticRecord[] = [];
  let clocks = 0, defs = 0;
  const options = { clock: { now() { clocks++; throw cause; } }, get diagnosticDefinitions(): never { defs++; throw cause; }, onDiagnostic(r: DiagnosticRecord) { emitted.push(r); } };
  throws(() => create(options), (error) => error === cause); equal(clocks, 1); equal(defs, 0); equal(emitted.length, 1);
  expected(emitted[0], operation, "clock-read", "invocation");
  const success = create({ clock: options.clock, onDiagnostic: options.onDiagnostic, now }); equal(success.now, now); equal(clocks, 1); equal(emitted.length, 1);
  emitted.length = 0;
  throws(() => create({ clock: { now: () => new Date(NaN) }, onDiagnostic(r: DiagnosticRecord) { emitted.push(r); } }), RangeError);
  equal(emitted.length, 1); expected(emitted[0], operation, "timestamp-normalization", "invocation");
}

// Accessors are supplied directly, not spread, so their original short circuit is measured.
let reads = ""; const emitted: DiagnosticRecord[] = [];
const input = {
  ...request,
  get logger(): never { reads += "l"; throw cause; },
  get metrics(): never { reads += "m"; throw cause; },
  get clock(): never { reads += "c"; throw cause; },
  onDiagnostic(r: DiagnosticRecord) { emitted.push(r); },
};
throws(() => createPlatformRuntimeRequestContext(input), (error) => error === cause); equal(reads, "l");
expected(emitted[0], "request-context", "dependency-selection", "selection");
emitted.length = 0; reads = "";
throws(() => createPlatformRuntimeContextDeps(input), (error) => error === cause); equal(reads, "l");
expected(emitted[0], "context-deps", "dependency-selection", "selection");
emitted.length = 0;
throws(() => createPlatformRuntimeRequestContext({ ...request, get now(): never { throw cause; }, onDiagnostic(r) { emitted.push(r); } }), (error) => error === cause);
expected(emitted[0], "request-context", "timestamp-selection", "selection");
emitted.length = 0;
throws(() => createPlatformRuntimeRequestContext({ ...request, now, get path(): never { throw cause; }, onDiagnostic(r) { emitted.push(r); } }), (error) => error === cause);
expected(emitted[0], "request-context", "context-projection", "projection");
let tenantReads = 0;
createPlatformRuntimeRequestContext({ ...request, now, get tenant() { tenantReads++; return {} as never; } }); equal(tenantReads, 2);
let flagCalls = 0;
const flags = { isEnabled() { flagCalls++; return true; } };
const context = createPlatformRuntimeRequestContext({ ...request, now, flags: flags as never }); equal(context.flags, flags); equal(flagCalls, 0);
const upstream = defineDiagnostic({ code: "fixture.context-failure", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" }, detail: { type: "object", properties: {} } });
const checked = createDiagnosticRecord(upstream, {}); if (!checked.ok) throw new Error("Invalid fixture");
const source = Object.assign(new Error(secret), { diagnosticRecord: checked.value, relatedDiagnosticRecords: [checked.value] });
emitted.length = 0;
throws(() => createPlatformRuntimeRequestContext({ ...request, clock: { now() { throw source; } }, diagnosticDefinitions: [upstream], onDiagnostic(r) { emitted.push(r); throw cause; } }), (error) => error === source);
equal(emitted.length, 1); expected(emitted[0], "request-context", "clock-read", "invocation");
equal(source.diagnosticRecord, checked.value); equal(source.relatedDiagnosticRecords.length, 1);
const defaults = createPlatformRuntimeContextDeps();
equal(defaults.clock.now().toISOString(), "2026-07-10T00:00:00.000Z");
throws(() => createPlatformRuntimeContextDeps({ get logger(): never { throw cause; }, get onDiagnostic(): never { throw new Error("Observer getter"); } }), (error) => error === cause);
