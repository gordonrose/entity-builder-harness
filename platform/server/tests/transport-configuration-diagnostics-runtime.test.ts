import { deepEqual, equal } from "node:assert/strict";
import { parseDiagnosticRecord } from "@kanbien/core/diagnostics";
import { resolvePlatformServerTransportOptions, type PlatformServerTransportOptions } from "../src/transport";
import { serverTransportConfigurationDiagnostic, serverTransportRelationshipDiagnostic } from "../src/diagnostics";

const fields = ["maxRequestBodyBytes", "maxHeaderBytes", "maxHeadersCount", "headersTimeoutMs", "requestTimeoutMs",
  "keepAliveTimeoutMs", "handlerTimeoutMs", "shutdownDrainTimeoutMs", "maxConcurrentRequests", "maxRequestsPerSocket"] as const;
const baseline = resolvePlatformServerTransportOptions();
equal(baseline.ok, true);
if (!baseline.ok) throw new Error("Expected existing defaults.");
deepEqual(Object.keys(baseline.value), fields);
deepEqual(Object.values(baseline.value), [1048576, 16384, 100, 10000, 30000, 5000, 30000, 30000, 100, 1000]);
for (const field of fields) {
  for (const [value, reason] of [["synthetic-private-transport-canary", "wrong-type"], [NaN, "not-finite"], [Infinity, "not-finite"], [-Infinity, "not-finite"], [1.5, "not-integer"], [-1.5, "not-integer"], [0, "not-positive"], [-1, "not-positive"]] as const) {
    const result = resolvePlatformServerTransportOptions({ [field]: value } as PlatformServerTransportOptions);
    equal(result.ok, false);
    if (result.ok) throw new Error("Expected rejected transport option.");
    equal(result.reason, `${field} must be a positive integer.`);
    deepEqual(result.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "platform-server.transport-configuration-invalid", definitionVersion: 1,
      detail: { field, reason, phase: "configuration", effect: "rejected" } });
    equal(parseDiagnosticRecord(serverTransportConfigurationDiagnostic, result.diagnosticRecord).ok, true);
    equal(JSON.stringify(result.diagnosticRecord).includes("synthetic-private"), false);
  }
}
const relation = resolvePlatformServerTransportOptions({ headersTimeoutMs: 30_001 });
equal(relation.ok, false);
if (relation.ok) throw new Error("Expected rejected timeout relationship.");
equal(relation.reason, "headersTimeoutMs must not exceed requestTimeoutMs.");
deepEqual(relation.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "platform-server.transport-configuration-inconsistent", definitionVersion: 1,
  detail: { relationship: "headers-within-request-timeout", rule: "less-than-or-equal", phase: "configuration", effect: "rejected" } });
equal(parseDiagnosticRecord(serverTransportRelationshipDiagnostic, relation.diagnosticRecord).ok, true);
equal(resolvePlatformServerTransportOptions({ headersTimeoutMs: 30_000 }).ok, true);
const simultaneous = resolvePlatformServerTransportOptions({ maxHeaderBytes: 0, maxRequestBodyBytes: 0 });
equal(simultaneous.ok, false);
if (!simultaneous.ok) deepEqual(simultaneous.diagnosticRecord.detail, { field: "maxRequestBodyBytes", reason: "not-positive", phase: "configuration", effect: "rejected" });
let reads = 0;
const withGetter = { get maxHeaderBytes() { reads++; return 0; } };
equal(resolvePlatformServerTransportOptions(withGetter).ok, false);
equal(reads, 1);
equal(resolvePlatformServerTransportOptions({ maxHeaderBytes: null } as never).ok, true, "legacy nullish defaults stay accepted");
console.log("Platform transport configuration diagnostics passed.");
