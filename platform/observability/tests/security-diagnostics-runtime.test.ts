import { deepEqual, equal } from "node:assert/strict";
import { diagnosticRelatedRecordLimit } from "@kanbien/core/diagnostics";
import { platformPersistenceDiagnosticCatalog, persistenceObservedDiagnosticRecord } from "../../persistence/src/diagnostics";
import type { LogRecord } from "@kanbien/core/logging";
import { platformSecurityDiagnosticCatalog, validateCertificateAuthorityContent, securityPeerIdentityDiagnosticRecord, securityPeerTrustDiagnosticRecord } from "@kanbien/platform-security";
import { createPlatformDiagnosticReporter, createPlatformSafeLogger, reportPlatformErrorDiagnostic, createPlatformReadinessObserver } from "../src/index";

const records: LogRecord[] = [];
const reporter = createPlatformDiagnosticReporter({ catalogs: [platformSecurityDiagnosticCatalog],
  logger: createPlatformSafeLogger({ write: (record) => records.push(record) }), clock: { now: () => new Date("2026-10-27T00:00:00.000Z") } });
const result = validateCertificateAuthorityContent("-----BEGIN CERTIFICATE-----\nsynthetic-private-certificate-canary\n-----END CERTIFICATE-----");
if (result.ok) throw new Error("fixture-accepted");
const context = { capability: "security", operation: "validate-trust-material", stage: "startup" } as const;
for (const record of [result.error.diagnosticRecord, securityPeerIdentityDiagnosticRecord("hostname-mismatch"), securityPeerTrustDiagnosticRecord("untrusted-chain")]) {
  deepEqual(reporter.report(record, context), { status: "written" });
  deepEqual(records.at(-1)?.fields?.["diagnostic"], record);
  deepEqual(reporter.report({ ...record, detail: { ...record.detail, certificate: "synthetic-private-certificate-canary" } }, context), { status: "rejected" });
}
equal(records.length, 3);
equal(JSON.stringify(records).includes("canary"), false);
equal(JSON.stringify(records).includes("BEGIN CERTIFICATE"), false);
const unavailable = createPlatformDiagnosticReporter({ catalogs: [platformSecurityDiagnosticCatalog],
  logger: createPlatformSafeLogger({ write: () => { throw new Error("synthetic-sink-secret-canary"); } }), clock: { now: () => new Date() } });
deepEqual(unavailable.report(result.error.diagnosticRecord, context), { status: "unavailable" });
const primary = persistenceObservedDiagnosticRecord({ classification: "tls_trust_invalid", phase: "pool_query", code_status: "recognized" }, "readiness");
const related = securityPeerIdentityDiagnosticRecord("hostname-mismatch");
let attempts = 0;
reportPlatformErrorDiagnostic({ report() { attempts++; if (attempts === 1) throw new Error("synthetic-sink-secret-canary"); return { status: "written" }; } }, { diagnosticRecord: primary, relatedDiagnosticRecords: [related] }, context);
equal(attempts, 2, "a primary sink failure must not suppress independent related delivery");
for (const hostile of [Array(1), Array(diagnosticRelatedRecordLimit + 1).fill(related), Object.defineProperty([], "0", { get() { throw new Error("synthetic-secret-canary"); } }), new Proxy([], { get() { throw new Error("synthetic-secret-canary"); } })]) {
  attempts = 0;
  reportPlatformErrorDiagnostic({ report() { attempts++; return { status: "written" }; } }, { diagnosticRecord: primary, relatedDiagnosticRecords: hostile }, context);
  equal(attempts, 1);
}
const onlyPersistence = createPlatformDiagnosticReporter({ catalogs: [platformPersistenceDiagnosticCatalog], logger: { write: () => undefined }, clock: { now: () => new Date() } });
deepEqual(onlyPersistence.report(related, context), { status: "rejected" });
const readinessRecords: LogRecord[] = [];
const logger = createPlatformSafeLogger({ write: (record) => readinessRecords.push(record) });
const clock = { now: () => new Date("2026-10-27T00:00:00.000Z") };
const readiness = createPlatformReadinessObserver({ identity: { target: "fixture", scope: "fixture", workload: "fixture", dependency: "persistence" },
  probe: async () => ({ readiness: "not-ready", diagnosticCode: primary.code, diagnosticRecord: primary, relatedDiagnosticRecords: [related] }),
  diagnostics: createPlatformDiagnosticReporter({ catalogs: [platformPersistenceDiagnosticCatalog, platformSecurityDiagnosticCatalog], logger, clock }),
  logger, clock, metrics: { record() {} }, timeoutMs: 100, allowedDiagnosticCodes: [primary.code], defaultDiagnosticCode: primary.code });
void readiness.observe().then((event) => {
  equal(event.diagnosticCode, primary.code, "readiness event remains persistence-owned");
  deepEqual(readinessRecords.filter((record) => record.message === "platform.diagnostic.observed").map((record) => record.fields?.["diagnostic"]), [primary, related], "a reporter without the observability catalog rejects the generic observation while preserving selected upstream evidence");
});
console.log("Shared security records pass explicit catalog registration, safe reporting and sink-failure isolation without forcing production logging.");
