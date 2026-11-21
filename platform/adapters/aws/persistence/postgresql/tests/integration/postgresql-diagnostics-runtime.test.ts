// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: product.test.postgresql-diagnostics
//   version: 1
//   status: active
//   created_on: "2026-10-26"
//   updated_on: "2026-11-09"
//   layer: 03.product
//   domain: persistence.diagnostics
//   disciplines: [security, sre]
//   kind: test
//   purpose: Exercise bounded diagnostic observations through real pg connections to disposable loopback protocol fixtures.
//   portability: { class: internal, targets: [] }
//   used_by:
//   - id: product.test.postgresql-runtime-runner
//     path: platform/adapters/aws/persistence/postgresql/tests/run-runtime-tests.mjs

import { deepEqual, equal, ok } from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { createServer, type Socket } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createSecureContext, TLSSocket } from "node:tls";
import { Pool } from "pg";
import { nodePoolAdapter } from "../../src/connection";
import { observePostgreSqlOperation, postgreSqlFailureDiagnostic, postgreSqlPersistenceOperationError, postgreSqlSecurityDiagnosticRecords } from "../../src/errors";

const canary = "password=synthetic-diagnostic-canary postgres://user:canary@private.example/query secret-token";
let fixtureStage = "closed-mapping";
let lastSafeFacts: ReturnType<typeof postgreSqlFailureDiagnostic>["facts"] | undefined;
// Protocol/TLS classification needs time to observe the actual peer response;
// only the intentionally silent fixture exercises the short timeout deadline.
const fixtureDeadlines = { protocol: 2_000, intentionalTimeout: 100 } as const;

function errorResponse(code?: string): Buffer {
  const payload = Buffer.from(`SFATAL\0${code === undefined ? "" : `C${code}\0`}M${canary}\0\0`);
  const header = Buffer.alloc(5); header[0] = 69; header.writeInt32BE(payload.length + 4, 1);
  return Buffer.concat([header, payload]);
}

async function withServer(accept: (socket: Socket) => void, run: (port: number) => Promise<void>): Promise<void> {
  const sockets = new Set<Socket>();
  const server = createServer((socket) => {
    sockets.add(socket); socket.on("error", () => undefined); socket.once("close", () => sockets.delete(socket)); accept(socket);
  });
  await new Promise<void>((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  try { const address = server.address(); ok(address !== null && typeof address === "object"); await run(address.port); }
  finally { for (const socket of sockets) socket.destroy(); await new Promise<void>((resolve) => server.close(() => resolve())); }
}

async function failedConnection(port: number, ssl: false | { ca?: string; servername?: string; rejectUnauthorized: boolean } = false, connectionTimeoutMs: number = fixtureDeadlines.protocol) {
  const pool = nodePoolAdapter(new Pool({ host: "127.0.0.1", port, user: "fixture", password: canary, database: "fixture", connectionTimeoutMillis: connectionTimeoutMs, ssl }));
  try {
    let cause: unknown;
    try { const client = await pool.connect(); client.release(); throw new Error("fixture unexpectedly connected"); }
    catch (error) { cause = error; }
    const diagnostic = postgreSqlFailureDiagnostic(cause);
    lastSafeFacts = diagnostic.facts;
    equal(diagnostic.facts.phase, "pool_connect");
    ok(typeof diagnostic.facts.elapsed_ms === "number" && diagnostic.facts.elapsed_ms >= 0 && diagnostic.facts.elapsed_ms < 5_000);
    equal(diagnostic.retryable, false);
    const safe = JSON.stringify({ diagnostic, error: postgreSqlPersistenceOperationError("connect", cause) });
    for (const forbidden of [canary, "private.example", "postgres://", "synthetic-diagnostic-canary", '"stack"', '"cause"']) equal(safe.includes(forbidden), false);
    return diagnostic;
  } finally { await pool.end(); }
}

async function main(): Promise<void> {
  const builders = require("../../../../../../persistence/src/diagnostics") as Record<string, unknown>;
  const descriptor = Object.getOwnPropertyDescriptor(builders, "persistenceObservedDiagnosticRecord")!;
  for (const mode of ["throws", "undefined", "malformed"] as const) {
    Object.defineProperty(builders, "persistenceObservedDiagnosticRecord", { ...descriptor, value: () => {
      if (mode === "throws") throw new Error(canary);
      return mode === "undefined" ? undefined : { code: canary };
    } });
    try {
      const seen: unknown[] = [];
      const result = postgreSqlPersistenceOperationError("readiness", { code: "28P01", message: canary }, { onDiagnostic(record) { seen.push(record); } });
      const processing = { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1,
        detail: { reason: mode === "throws" ? "construction-threw" : mode === "malformed" ? "evidence-rejected" : "construction-rejected" } };
      equal(result.code, "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED");
      equal(result.diagnostic?.facts?.["classification"], "authentication_rejected");
      deepEqual(result.diagnosticRecord, processing); deepEqual(seen, [processing]);
      equal(JSON.stringify(result).includes(canary), false);
    } finally { Object.defineProperty(builders, "persistenceObservedDiagnosticRecord", descriptor); }
  }
  for (const [code, reason] of [["ERR_TLS_CERT_ALTNAME_INVALID", "hostname-mismatch"], ["CERT_HAS_EXPIRED", "expired"], ["CERT_NOT_YET_VALID", "not-yet-valid"],
    ["SELF_SIGNED_CERT_IN_CHAIN", "untrusted-chain"], ["DEPTH_ZERO_SELF_SIGNED_CERT", "untrusted-chain"], ["UNABLE_TO_VERIFY_LEAF_SIGNATURE", "untrusted-chain"], ["UNABLE_TO_GET_ISSUER_CERT_LOCALLY", "untrusted-chain"]] as const) {
    const error = postgreSqlPersistenceOperationError("readiness", { code, message: canary });
    equal(error.diagnostic?.failureSource, "unknown");
    equal(error.diagnosticRecord?.definitionVersion, 2);
    equal(error.relatedDiagnosticRecords?.length, 1);
    equal((error.relatedDiagnosticRecords?.[0]?.detail as { reason: string }).reason, reason);
    equal(JSON.stringify(error).includes(canary), false);
  }
  for (const error of [{ code: "ETIMEDOUT" }, { code: "POSTGRES_TLS_UNAVAILABLE" }, { code: "CERT_REVOKED" }, new Error(canary), Object.defineProperty({}, "code", { get() { throw new Error(canary); } })]) deepEqual(postgreSqlSecurityDiagnosticRecords(error), []);
  deepEqual(postgreSqlSecurityDiagnosticRecords({ cause: { code: "CERT_HAS_EXPIRED" }, errors: [{ code: "CERT_HAS_EXPIRED" }] }).map((record) => record.detail.reason), ["expired"]);
  for (const cause of [{ code: "ECONNRESET", cause: { code: "CERT_HAS_EXPIRED" } }, { errors: [{ code: "28P01" }, { code: "ERR_TLS_CERT_ALTNAME_INVALID" }] }]) {
    const error = postgreSqlPersistenceOperationError("restore_verification", cause);
    equal(error.diagnostic?.facts?.["classification"] === "tls_trust_invalid", false, "existing first recognized primary retains its precedence");
    deepEqual(error.relatedDiagnosticRecords, [], "non-TLS primary must not emit an envelope rejected by strict readers");
  }
  for (const [code, classification, neutral] of [
    ["ECONNRESET", "transport_unavailable", "persistence.transport-unavailable"],
    ["ERR_TLS_CERT_ALTNAME_INVALID", "tls_trust_invalid", "persistence.trust-validation-failed"],
    ["28P01", "authentication_rejected", "persistence.credential-rejected"],
    ["42501", "permission_denied", "persistence.runtime-permission-denied"],
    ["ETIMEDOUT", "timeout", "persistence.operation-timed-out"],
    ["57014", "query_canceled", "persistence.unclassified-failure"],
    ["23505", "conflict", "persistence.unclassified-failure"],
    ["23503", "constraint", "persistence.unclassified-failure"],
    ["40001", "transaction_rolled_back", "persistence.unclassified-failure"],
    ["42P01", "content_unavailable", "persistence.unclassified-failure"],
    ["22001", "validation", "persistence.unclassified-failure"],
    ["synthetic-sensitive-canary", "unknown", "persistence.unclassified-failure"],
  ] as const) {
    const failure = postgreSqlPersistenceOperationError("write_atomic", { code, message: canary });
    equal(failure.diagnostic?.facts?.["classification"], classification);
    equal(failure.diagnosticRecord?.code, neutral);
    equal((failure.diagnosticRecord?.detail as { effect: string }).effect, "unknown", "a machine code does not prove the final write outcome");
    equal(JSON.stringify(failure).includes(canary), false);
  }
  deepEqual(postgreSqlFailureDiagnostic(new Error(canary)).facts, { classification: "unknown", code_status: "absent", phase: "unknown", elapsed_ms: null });
  equal(postgreSqlFailureDiagnostic({ code: canary }).facts.code_status, "unrecognized");
  equal(postgreSqlFailureDiagnostic({ cause: { code: "28P01" } }).facts.classification, "authentication_rejected");
  const materialMessage = "SASL: SCRAM-SERVER-FIRST-MESSAGE: client password must be a string";
  for (const code of [undefined, canary]) {
    const diagnostic = postgreSqlFailureDiagnostic({ cause: { message: materialMessage, code } });
    equal(diagnostic.facts.classification, "authentication_material_invalid");
    equal(diagnostic.facts.code_status, code === undefined ? "absent" : "unrecognized");
    equal(diagnostic.failureKind, "configuration");
    equal(JSON.stringify(diagnostic).includes(materialMessage), false);
  }
  equal(postgreSqlFailureDiagnostic(new Error(materialMessage + canary)).facts.classification, "unknown");
  equal(postgreSqlFailureDiagnostic({ message: materialMessage, code: "28P01" }).facts.classification, "authentication_rejected");
  equal(postgreSqlFailureDiagnostic({ errors: [...Array.from({ length: 32 }, () => ({})), { message: materialMessage }] }).facts.classification, "unknown");
  const messageAccessor = Object.defineProperty({}, "message", { get() { throw new Error(canary); } });
  equal(postgreSqlFailureDiagnostic(messageAccessor).facts.classification, "unknown");
  const cyclic: { cause?: unknown } = {}; cyclic.cause = cyclic;
  equal(postgreSqlFailureDiagnostic(cyclic).facts.code_status, "absent");
  const accessor = Object.defineProperty({}, "code", { get() { throw new Error(canary); } });
  equal(postgreSqlFailureDiagnostic(accessor).facts.classification, "unknown");

  equal(postgreSqlFailureDiagnostic({ errors: [{ cause: { code: "28P01" } }] }).facts.classification, "authentication_rejected");
  let nested: unknown = { code: "28P01" };
  for (let depth = 0; depth < 4; depth += 1) nested = { cause: nested };
  equal(postgreSqlFailureDiagnostic(nested).facts.classification, "unknown", "causal inspection is depth bounded");
  equal(postgreSqlFailureDiagnostic({ errors: [...Array.from({ length: 32 }, () => ({})), { code: "28P01" }] }).facts.classification, "unknown", "aggregate inspection has a node budget");
  try { await observePostgreSqlOperation("query", async () => { throw canary; }); } catch (error) {
    deepEqual(postgreSqlFailureDiagnostic(error).facts, { classification: "unknown", code_status: "absent", phase: "unknown", elapsed_ms: null });
  }
  equal(postgreSqlFailureDiagnostic({ code: "57014" }).facts.classification, "query_canceled", "a driver cancellation code does not prove why it was canceled");

  equal(postgreSqlFailureDiagnostic({ code: "57014" }).failureKind, "unknown", "cancellation does not prove a dependency outage");

  const reused = new Error(canary);
  for (const phase of ["pool_connect", "query"] as const) {
    try { await observePostgreSqlOperation(phase, async () => { throw reused; }); } catch (error) { equal(error, reused); }
    equal(postgreSqlFailureDiagnostic(reused).facts.phase, phase, "each invocation needs a fresh observation");
  }
  try { await observePostgreSqlOperation("pool_connect", () => observePostgreSqlOperation("authentication_value", async () => { throw reused; })); } catch { /* expected */ }
  equal(postgreSqlFailureDiagnostic(reused).facts.phase, "authentication_value", "nested authentication observation belongs to this invocation");
  try { await observePostgreSqlOperation("query", async () => { throw reused; }); } catch { /* expected */ }
  equal(postgreSqlFailureDiagnostic(reused).facts.phase, "query");
  const wrapped = new Error("safe wrapper", { cause: reused });
  equal(postgreSqlFailureDiagnostic(wrapped).facts.phase, "query", "private wrappers retain actual invocation evidence");
  const aggregate = { errors: [wrapped] };
  equal(postgreSqlFailureDiagnostic(aggregate).facts.phase, "query");
  equal(postgreSqlFailureDiagnostic(Object.defineProperty({}, "cause", { get() { throw new Error(canary); } })).facts.phase, "unknown");

  // ErrorResponse packets go through the installed pg parser and actual sockets.
  fixtureStage = "protocol-errors";
  for (const [code, classification, status] of [
    ["28P01", "authentication_rejected", "recognized"], ["42501", "permission_denied", "recognized"],
    ["3D000", "content_unavailable", "recognized"], ["57014", "query_canceled", "recognized"],
    ["ZZ999", "unknown", "unrecognized"], [undefined, "unknown", "absent"],
  ] as const) await withServer((socket) => socket.once("data", () => socket.end(errorResponse(code))), async (port) => {
    const diagnostic = await failedConnection(port);
    equal(diagnostic.facts.classification, classification); equal(diagnostic.facts.code_status, status);
  });
  fixtureStage = "delayed-protocol-response";
  await withServer((socket) => socket.once("data", () => {
    setTimeout(() => socket.end(errorResponse("28P01")), fixtureDeadlines.intentionalTimeout + 50);
  }), async (port) => {
    const diagnostic = await failedConnection(port);
    equal(diagnostic.facts.classification, "authentication_rejected", "normal protocol fixtures must wait beyond the intentional timeout deadline for actual rejection evidence");
    equal(diagnostic.facts.code_status, "recognized");
    ok(diagnostic.facts.elapsed_ms !== null && diagnostic.facts.elapsed_ms >= fixtureDeadlines.intentionalTimeout);
  });
  fixtureStage = "intentional-connection-timeout";
  await withServer(() => undefined, async (port) => {
    const diagnostic = await failedConnection(port, false, fixtureDeadlines.intentionalTimeout);
    equal(diagnostic.facts.classification, "unknown"); equal(diagnostic.facts.code_status, "absent");
    ok(diagnostic.facts.elapsed_ms !== null && diagnostic.facts.elapsed_ms >= 50, "code-less pg timeout is measured without interpreting its message");
  });

  const directory = mkdtempSync(join(tmpdir(), "pg-diagnostic-tls-"));
  try {
    const keyPath = join(directory, "fixture.key"), certPath = join(directory, "fixture.crt");
    const certificate = spawnSync("openssl", ["req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", keyPath, "-out", certPath, "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost", "-days", "1"], { stdio: "pipe", timeout: 10_000 });
    equal(certificate.status, 0, "disposable TLS certificate generation must succeed");
    const ca = readFileSync(certPath, "utf8");
    const context = createSecureContext({ key: readFileSync(keyPath), cert: ca });
    for (const servername of ["wrong.example", "localhost"]) await withServer((socket) => socket.once("data", () => {
      socket.write("S");
      const tls = new TLSSocket(socket, { isServer: true, secureContext: context });
      tls.on("error", () => undefined);
      tls.once("data", () => tls.end(errorResponse("28P01")));
    }), async (port) => {
      fixtureStage = servername === "localhost" ? "tls-verified-authentication" : "tls-hostname-mismatch";
      const diagnostic = await failedConnection(port, { ca, servername, rejectUnauthorized: true });
      equal(diagnostic.facts.classification, servername === "localhost" ? "authentication_rejected" : "tls_trust_invalid");
    });
    await withServer((socket) => socket.once("data", () => {
      socket.write("S"); const tls = new TLSSocket(socket, { isServer: true, secureContext: context }); tls.on("error", () => undefined);
    }), async (port) => {
      fixtureStage = "tls-untrusted-chain";
      const diagnostic = await failedConnection(port, { rejectUnauthorized: true });
      equal(diagnostic.facts.classification, "tls_trust_invalid");
    });
  } finally { rmSync(directory, { recursive: true, force: true }); }
  console.log("PostgreSQL diagnostics real-driver protocol and TLS tests passed.");
}
void main().catch(() => { console.error(JSON.stringify({ code: "POSTGRESQL_DIAGNOSTIC_FIXTURE_FAILED", stage: fixtureStage, ...(lastSafeFacts === undefined ? {} : { execution: lastSafeFacts }) })); process.exitCode = 1; });
