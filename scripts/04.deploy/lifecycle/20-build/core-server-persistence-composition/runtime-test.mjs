#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-persistence-composition-runtime
//   version: 2
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-31"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: script
//   purpose: Prove the persistence-capable core-server composition keeps liveness separate from injected dependency readiness and exposes only safe server-mediated acceptance outcomes.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: deploy.test.core-server-persistence-composition
//     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh

import { request as httpRequest } from "node:http";
import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import { join } from "node:path";

import { fixtureRuntime } from "./fixture-runtime.mjs";
const buildOutput = fixtureRuntime(process.argv[2]);
if (typeof buildOutput !== "string" || buildOutput.length === 0) {
  throw new Error("Usage: runtime-test.mjs <compiled-output-directory>");
}

const program = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.js")));
const serverMain = await import(pathToFileUrl(join(buildOutput, "platform/server/src/main.js")));
const verifier = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.js")));
const identityLifecycle = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-runtime-credential.js")));
const releaseIdentity = { sourceCommitSha: "local-persistence-composition-proof-2026.10.23" };
const recordId = "core-persistence-acceptance-0001";
const factDigest = "a".repeat(64);

await proveUnavailableDependency();
await proveAvailableDependency();
await proveHealthVerifierModes();
await proveRuntimeIdentityRevocationAndRestoration();
await proveTaskVerifierDiagnostics();
await proveDetailedReadiness();
await proveHealthDiagnosticDelivery();
await proveHealthObservationSelection();
await proveAcceptanceDiagnosticDelivery();
await proveAcceptanceObserverIsolation();
await proveAcceptanceRequestPredicates();

console.log("Core-server persistence composition local runtime proof passed.");

async function proveAcceptanceRequestPredicates() {
  const routes = [], catalogs = [];
  let persistenceCalls = 0;
  const app = program.createKanbienCoreServerPersistenceApp(releaseIdentity, {
    ...fakePersistence({ readiness: "ready", create: "created", read: "found" }),
    async createAcceptanceRecord() { persistenceCalls++; return "created"; },
    async readAcceptanceRecord() { persistenceCalls++; return { outcome: "not-found" }; },
    async deleteAcceptanceRecord() { persistenceCalls++; return "deleted"; },
  });
  app.mount({ registerDiagnosticCatalog(catalog) { catalogs.push(catalog); },
    registerObservabilityProfile() {}, registerHealthCheck() {}, registerRoute(route) { routes.push(route); } });
  deepEqual(catalogs.map((catalog) => catalog.owner), ["kanbien-core-server.acceptance"]);
  const post = routes.find((route) => route.method === "POST");
  const cases = [
    [undefined, "body", "missing"], [null, "body", "null"], [[], "body", "array"], [7, "body", "wrong-type"],
    [{}, "record_id", "missing"], [{ record_id: null }, "record_id", "wrong-type"],
    [{ record_id: "PRIVATE-invalid-id-canary", fact_digest: "wrong" }, "record_id", "invalid-format"],
    [{ record_id: recordId }, "fact_digest", "missing"],
    [{ record_id: recordId, fact_digest: false }, "fact_digest", "wrong-type"],
    [{ record_id: recordId, fact_digest: "private-digest-canary" }, "fact_digest", "invalid-format"],
  ];
  for (const [body, field, reason] of cases) {
    const seen = [];
    const result = await post.handler.handle({ body }, { onDiagnostic(record) { seen.push(record); } });
    equal(result.status, 400); deepEqual(result.body, { outcome: "invalid-request" });
    deepEqual(seen, [acceptancePredicateRecord("create", "body", field, reason)]);
  }
  const reads = [];
  const getterBody = { get record_id() { reads.push("id"); return "!"; },
    get fact_digest() { reads.push("digest"); return "!"; } };
  await post.handler.handle({ body: getterBody }, {});
  deepEqual(reads, ["id", "digest"], "Both original body getters precede the first ID predicate");
  const raw = Object.freeze(new Error("private-getter-canary"));
  await rejects(() => post.handler.handle({ body: { get record_id() { throw raw; } } }, {}), (error) => error === raw);
  for (const sink of [undefined, () => { throw raw; }, () => Promise.reject(raw), () => {
    const pending = Promise.reject(raw);
    Object.defineProperties(pending, { then: { get() { throw raw; } }, catch: { get() { throw raw; } } });
    return pending;
  }]) {
    equal((await post.handler.handle({ body: {} }, { onDiagnostic: sink })).status, 400);
  }
  for (const operation of ["read", "delete"]) {
    const route = routes.find((item) => item.method === (operation === "read" ? "GET" : "DELETE") && item.path === "/internal/persistence-acceptance");
    for (const [value, reason] of [[undefined, "missing"], [[recordId], "array"], [7, "wrong-type"], ["!private-query-canary", "invalid-format"]]) {
      const seen = [];
      const result = await route.handler.handle({ query: { record_id: value } }, { onDiagnostic(record) { seen.push(record); } });
      equal(result.status, 400); deepEqual(result.body, { outcome: "invalid-request" });
      deepEqual(seen, [acceptancePredicateRecord(operation, "query", "record_id", reason)]);
      equal(JSON.stringify(seen).includes("canary"), false);
    }
  }
  await new Promise((resolve) => setImmediate(resolve));
  equal(persistenceCalls, 0, "Every rejected predicate avoids persistence calls");
  const valid = await post.handler.handle({ body: { record_id: recordId, fact_digest: factDigest, ignored: "private-extra-canary" } }, {});
  equal(valid.status, 201); equal(persistenceCalls, 1, "Ignored extra fields remain accepted");
  const logs = [];
  const started = await start({ ...fakePersistence({ readiness: "ready", create: "created", read: "found" }),
    createAcceptanceRecord: async () => { throw new Error("Invalid body reached persistence"); } }, { write(log) { logs.push(log); } });
  try {
    assertJson(await request(started.handle.port, "POST", "/internal/persistence-acceptance", {}), 400, { outcome: "invalid-request" }, "actual target preserves400");
    const observed = logs.filter((log) => log.fields?.operation === "request-observation");
    deepEqual(observed.map((log) => log.fields.diagnostic), [acceptancePredicateRecord("create", "body", "record_id", "missing")]);
    equal(observed[0].fields.stage, "request"); equal(typeof observed[0].correlationId, "string");
  } finally { await started.close(); }
  const unavailable = await start(fakePersistence({ readiness: "ready", create: "created", read: "found" }), { write(log) {
    if (log.message === "platform.diagnostic.observed") throw raw;
  } });
  try {
    assertJson(await request(unavailable.handle.port, "GET", "/internal/persistence-acceptance?record_id=!"), 400,
      { outcome: "invalid-request" }, "unavailable reporting cannot change rejection");
  } finally { await unavailable.close(); }
}

function acceptancePredicateRecord(operation, source, field, reason) {
  return { schema: "core/diagnostic-record/v1", code: "kanbien-core-server.acceptance.request-invalid", definitionVersion: 1,
    detail: { operation, source, field, reason, effect: "persistence-not-invoked" } };
}

async function proveAcceptanceDiagnosticDelivery() {
  const postgres = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.js")));
  const core = await import(pathToFileUrl(join(buildOutput, "packages/core/src/persistence/index.js")));
  const sources = Array.from({ length: 9 }, (_, ordinal) => core.corePersistenceInMemoryBoundaryRecord({
    operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal,
  }));
  const failure = () => Object.assign(new Error("private-acceptance-failure-canary"), {
    code: "28P01", diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1),
  });
  const noRow = { rows: [], rowCount: 0 };
  const matching = { rows: [{ record_id: recordId, fact_digest: factDigest }] };
  const different = { rows: [{ record_id: recordId, fact_digest: "b".repeat(64) }] };
  const cases = [
    { name: "inserted", method: "POST", results: [{ rows: [{ record_id: recordId }] }], status: 201, body: { outcome: "created" }, operations: [] },
    ...[false, true].flatMap((threw) => [
      { observed: "matching", row: matching, status: 200, outcome: "already-exists" },
      { observed: "different", row: different, status: 409, outcome: "conflict" },
      { observed: "absent", row: noRow, status: 503, outcome: "not-confirmed" },
      { observed: "unavailable", row: failure(), status: 503, outcome: "not-confirmed" },
    ].map(({ observed, row, status, outcome }) => ({
      name: `${threw ? "thrown" : "no-row"}-${observed}`, method: "POST",
      results: [threw ? failure() : noRow, row], status, body: { outcome },
      operations: [...(threw ? [["create", "primary"]] : []), ...(observed === "unavailable" ? [["read", "reconciliation"]] : [])],
      reconciliation: { operation: "create", primaryOutcome: threw ? "call-threw" : "no-row-returned", observed, effect: "read-result-observed" },
    }))),
    { name: "read-found", method: "GET", results: [matching], status: 200, body: { outcome: "found", record: { id: recordId, factDigest }, release: releaseIdentity }, operations: [] },
    { name: "read-absent", method: "GET", results: [noRow], status: 404, body: { outcome: "not-found" }, operations: [] },
    { name: "read-failed", method: "GET", results: [failure()], status: 503, body: { outcome: "not-confirmed" }, operations: [["read", "primary"]] },
    ...[false, true].map((source) => ({ name: `read-tls-source-${source}`, method: "GET",
      results: [Object.assign(new Error("private-acceptance-failure-canary"), { code: "ERR_TLS_CERT_ALTNAME_INVALID",
        ...(source ? { diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) } : {}) })],
      status: 503, body: { outcome: "not-confirmed" }, operations: [["read", "primary"]], source,
      failureCode: "persistence.trust-validation-failed", classification: "tls_trust_invalid",
      security: { schema: "core/diagnostic-record/v1", code: "security.peer-identity-verification-failed", definitionVersion: 1,
        detail: { phase: "peer-identity-verification", reason: "hostname-mismatch", effect: "not-assessed" } },
    })),
    { name: "delete-confirmed", method: "DELETE", results: [{ rows: [], rowCount: 1 }], status: 200, body: { outcome: "deleted" }, operations: [] },
    { name: "delete-absent", method: "DELETE", results: [noRow], status: 404, body: { outcome: "not-found" }, operations: [] },
    { name: "delete-failed", method: "DELETE", results: [failure()], status: 503, body: { outcome: "not-confirmed" }, operations: [["delete", "primary"]] },
  ];
  for (const test of cases) {
    const logs = [], queries = [];
    let closed = 0;
    const persistence = postgres.createKanbienCoreServerPostgreSqlPersistenceRuntime({ schema: "platform", pool: {
      async query(statement) {
        queries.push(statement);
        const result = test.results[queries.length - 1];
        if (result instanceof Error) throw result;
        if (result === undefined) throw new Error("Unexpected speculative query");
        return result;
      },
      async end() { closed++; },
    } });
    const started = await start(persistence, { write(record) { logs.push(record); } });
    try {
      const response = await request(started.handle.port, test.method,
        `/internal/persistence-acceptance${test.method === "POST" ? "" : `?record_id=${recordId}`}`,
        test.method === "POST" ? acceptanceRequest() : undefined);
      assertJson(response, test.status, test.body, test.name);
      equal(queries.length, test.results.length, `${test.name}: original query count`);
      equal(queries[0].text.startsWith(test.method === "POST" ? "INSERT" : test.method === "GET" ? "SELECT" : "DELETE"), true);
      deepEqual(queries[0].values, test.method === "POST" ? [recordId, factDigest] : [recordId]);
      const expected = test.operations.flatMap(([operation, boundary]) => [
        { schema: "core/diagnostic-record/v1", code: test.failureCode ?? "persistence.credential-rejected", definitionVersion: 3,
          detail: { phase: "unknown", classification: test.classification ?? "authentication_rejected", codeStatus: "recognized", operation, boundary,
            effect: operation === "read" ? "not-assessed" : "unknown" } },
        ...(test.source === false ? [] : sources),
      ]);
      if (test.security) expected.push(test.security);
      if (test.reconciliation) expected.push({ schema: "core/diagnostic-record/v1", code: "persistence.reconciliation-observed", definitionVersion: 1, detail: test.reconciliation });
      const observed = logs.filter((entry) => entry.message === "platform.diagnostic.observed"
        && entry.fields.operation === "request-observation").map((entry) => entry.fields.diagnostic);
      deepEqual(observed, expected, `${test.name}: own fact plus source primary/eight, independently of reconciliation result`);
      for (const entry of logs.filter((entry) => entry.fields?.operation === "request-observation")) {
        equal(entry.fields.capability, "kanbien-core-server.persistence");
        equal(entry.fields.stage, "request");
        equal(typeof entry.correlationId, "string");
      }
      equal(response.body.includes("diagnostic"), false);
      equal(JSON.stringify(logs).includes("private-acceptance-failure-canary"), false);
      equal(JSON.stringify(observed).includes(recordId), false);
      equal(JSON.stringify(observed).includes(factDigest), false);
    } finally { await started.close(); }
    equal(closed, 1);
  }
}

async function proveAcceptanceObserverIsolation() {
  const postgres = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.js")));
  const cause = new Error("private-pool-selection-canary");
  let poolReads = 0, queries = 0;
  const pool = { async query() { queries++; return { rows: [] }; }, async end() {} };
  const options = { schema: "platform", get pool() { poolReads++; return pool; } };
  const runtime = postgres.createKanbienCoreServerPostgreSqlPersistenceRuntime(options);
  for (const sink of [undefined, () => { throw cause; }, () => Promise.reject(cause)]) {
    equal(await runtime.createAcceptanceRecord({ id: recordId, factDigest }, sink), "uncertain");
  }
  await new Promise((resolve) => setImmediate(resolve));
  equal(poolReads, 3, "Reconciliation retains the originally selected pool, not a new getter read");
  equal(queries, 6, "Observers never add probes or retries");
  const broken = postgres.createKanbienCoreServerPostgreSqlPersistenceRuntime({ schema: "platform", get pool() { throw cause; } });
  await rejects(() => broken.readAcceptanceRecord(recordId), (error) => error === cause);
  throws(() => postgres.createKanbienCoreServerPostgreSqlPersistenceRuntime({ schema: "bad-schema", pool }), (error) => {
    equal(error.constructor, TypeError); equal(error.message, "CORE_SERVER_PERSISTENCE_SCHEMA_INVALID");
    deepEqual(error.diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "persistence.local-rejected", definitionVersion: 1,
      detail: { operation: "validate-identifier", field: "schema", condition: "pattern", phase: "preflight", effect: "not-started" } });
    return true;
  });
}

async function proveDetailedReadiness() {
  const postgres = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.js")));
  let calls = 0;
  const runtime = postgres.createKanbienCoreServerPostgreSqlPersistenceRuntime({ schema: "platform", pool: {
    query: async () => { calls++; throw { code: "28P01", message: "password=synthetic-readiness-canary" }; },
    end: async () => undefined,
  } });
  const result = await runtime.readinessObservation();
  equal(calls, 1, "detailed readiness must not perform a separate speculative probe");
  equal(result.readiness, "not-ready");
  equal(result.diagnosticCode, "persistence.credential-rejected");
  deepEqual(result.diagnosticRecord.detail, { phase: "unknown", classification: "authentication_rejected", codeStatus: "recognized", operation: "readiness", effect: "not-assessed" });
  equal(JSON.stringify(result).includes("synthetic-readiness-canary"), false);
}

async function proveHealthDiagnosticDelivery() {
  const postgres = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.js")));
  let calls = 0, closed = 0;
  const logs = [];
  const persistence = postgres.createKanbienCoreServerPostgreSqlPersistenceRuntime({ schema: "platform", pool: {
    query: async () => { calls++; throw { code: "ERR_TLS_CERT_ALTNAME_INVALID", message: "private-health-connection-canary" }; },
    end: async () => { closed++; },
  } });
  const started = await start(persistence, { write(record) { logs.push(record); } });
  try {
    assertStatus(await request(started.handle.port, "GET", "/livez"), 200, "liveness never invokes the dependency"); equal(calls, 0);
    const response = await request(started.handle.port, "GET", "/readyz");
    assertStatus(response, 503, "actual dependency observation keeps existing HTTP readiness outcome"); equal(calls, 1);
    const summary = JSON.parse(response.body);
    deepEqual(Object.keys(summary).sort(), ["checkedAt", "checks", "status"]);
    deepEqual(Object.keys(summary.checks[0]).sort(), ["checkedAt", "component", "name", "status", "type"]);
    equal(summary.checks[0].status, "unhealthy");
    const observed = logs.filter((record) => record.message === "platform.diagnostic.observed" && record.fields.capability === "health").map((record) => record.fields.diagnostic);
    deepEqual(observed, [
      { schema: "core/diagnostic-record/v1", code: "persistence.trust-validation-failed", definitionVersion: 2,
        detail: { phase: "unknown", classification: "tls_trust_invalid", codeStatus: "recognized", operation: "readiness", effect: "not-assessed" } },
      { schema: "core/diagnostic-record/v1", code: "security.peer-identity-verification-failed", definitionVersion: 1,
        detail: { phase: "peer-identity-verification", reason: "hostname-mismatch", effect: "not-assessed" } },
      { schema: "core/diagnostic-record/v1", code: "health.check-not-ready", definitionVersion: 1,
        detail: { index: 0, status: "unhealthy", phase: "result", effect: "returned-not-ready" } },
    ]);
    equal(response.body.includes("diagnostic"), false); equal(JSON.stringify(logs).includes("private-health-connection-canary"), false);
  } finally { await started.close(); }
  equal(calls, 1); equal(closed, 1);
}

async function proveHealthObservationSelection() {
  const fake = fakePersistence({ readiness: "not-ready", create: "unavailable", read: "unavailable" });
  let reads = 0, calls = 0;
  Object.defineProperty(fake, "readinessObservation", { get() {
    reads++;
    return function () { equal(this, fake, "Optional observation preserves its original receiver."); calls++; return Promise.resolve({ readiness: "not-ready" }); };
  } });
  const started = await start(fake);
  try {
    assertStatus(await request(started.handle.port, "GET", "/readyz"), 503, "Selected observation keeps readiness state");
    equal(reads, 1); equal(calls, 1); equal(fake.readinessCalls, 0, "Selected observation never adds the legacy call");
  } finally { await started.close(); }
}

async function proveUnavailableDependency() {
  const fake = fakePersistence({ readiness: "not-ready", create: "unavailable", read: "unavailable" });
  const started = await start(fake);
  try {
    assertStatus(await request(started.handle.port, "GET", "/livez"), 200, "liveness must remain live while persistence is unavailable");
    assertStatus(await request(started.handle.port, "GET", "/readyz"), 503, "readiness must report the unavailable persistence dependency");
    equal(fake.readinessCalls, 1, "A runtime without observation retains exactly one legacy readiness call");
    assertJson(await request(started.handle.port, "POST", "/internal/persistence-acceptance", acceptanceRequest()), 503, { outcome: "not-confirmed" }, "unavailable persistence must return only a controlled outcome");
  } finally {
    await started.close();
  }
  if (!fake.closed) throw new Error("Core-server shutdown did not close the injected persistence runtime.");
}

async function proveAvailableDependency() {
  const fake = fakePersistence({ readiness: "ready", create: "created", read: "found" });
  const started = await start(fake);
  try {
    assertStatus(await request(started.handle.port, "GET", "/livez"), 200, "liveness must be live when persistence is ready");
    assertStatus(await request(started.handle.port, "GET", "/readyz"), 200, "readiness must be ready when persistence is ready");
    assertJson(await request(started.handle.port, "GET", "/internal/release-verification"), 200, { release: releaseIdentity }, "candidate must retain bootstrap release verification");
    assertJson(await request(started.handle.port, "POST", "/internal/persistence-acceptance", acceptanceRequest()), 201, { outcome: "created" }, "server-mediated acceptance create must expose a stable result");
    assertJson(await request(started.handle.port, "GET", `/internal/persistence-acceptance?record_id=${recordId}`), 200, { outcome: "found", record: { id: recordId, factDigest }, release: releaseIdentity }, "server-mediated acceptance read must expose only a stable result and release identity");
    assertJson(await request(started.handle.port, "DELETE", `/internal/persistence-acceptance?record_id=${recordId}`), 200, { outcome: "deleted" }, "server-mediated cleanup must be explicit and bounded");
    assertJson(await request(started.handle.port, "POST", "/internal/persistence-acceptance", {}), 400, { outcome: "invalid-request" }, "invalid persistence requests must not reach the runtime");
    assertStatus(await request(started.handle.port, "GET", "/smoke/product"), 404, "composition must not mount product functionality");
  } finally {
    await started.close();
  }
  if (!fake.closed) throw new Error("Core-server shutdown did not close the injected persistence runtime.");
}

async function proveHealthVerifierModes() {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => ({ status: String(url).endsWith("/livez") ? 200 : 503, ok: String(url).endsWith("/livez"), json: async () => undefined });
    const unready = await captureConsole(() => verifier.runKanbienCoreServerPersistenceVerifier({
      PERSISTENCE_VERIFIER_MODE: "health-unready",
      KANBIEN_PRIVATE_PERSISTENCE_URL: "http://core-server-persistence.kanbien-core-platform.internal:3000",
    }));
    if (!unready.output.includes("KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY") || unready.exitCode !== 0) throw new Error("Health verifier did not prove live-but-not-ready safely.");
    globalThis.fetch = async () => ({ status: 200, ok: true, json: async () => undefined });
    const ready = await captureConsole(() => verifier.runKanbienCoreServerPersistenceVerifier({
      PERSISTENCE_VERIFIER_MODE: "health-ready",
      KANBIEN_PRIVATE_PERSISTENCE_URL: "http://core-server-persistence.kanbien-core-platform.internal:3000",
    }));
    if (!ready.output.includes("KANBIEN_CORE_PERSISTENCE_HEALTHY") || ready.exitCode !== 0) throw new Error("Health verifier did not prove recovered readiness safely.");
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function proveRuntimeIdentityRevocationAndRestoration() {
  const queries = [];
  await identityLifecycle.revokeRuntimeAccess({ query: async (statement) => { queries.push(statement); return { rows: statement.text.includes("pg_terminate_backend") ? [{ terminated: true }] : [] }; } }, "core_runtime");
  if (queries.length !== 3 || !queries[0].text.includes('REVOKE rds_iam FROM "core_runtime"') || !queries[1].text.includes('ALTER ROLE "core_runtime" NOLOGIN') || !queries[2].text.includes("pg_terminate_backend(pid) AS terminated") || /password|scram/i.test(JSON.stringify(queries))) throw new Error("Runtime identity revocation did not use the bounded IAM-membership, no-login, and session-termination sequence.");
  await identityLifecycle.revokeRuntimeAccess({ query: async () => ({ rows: [] }) }, "core_runtime");
  for (const [aggregate, visit] of [[true, false], [true, true], [false, true]]) {
    const seen = [], rows = { some(callback) { equal(this, rows); if (visit) callback({ terminated: false }, 999); return aggregate; } };
    const operation = () => identityLifecycle.revokeRuntimeAccess({ query: async () => ({ rows }) }, "_", { onObservation(record) { seen.push(record); } });
    if (aggregate) {
      await rejects(operation, /PERSISTENCE_RUNTIME_SESSION_TERMINATION_NOT_CONFIRMED/);
      deepEqual(seen.map(({ detail }) => detail), [{ task: "administration", operation: "revoke-runtime", field: visit ? "terminated" : "termination-result", condition: visit ? "not-true" : "predicate-rejected", effect: "predicate-rejected", ...(visit ? { ordinal: 0 } : {}) }]);
    } else { await operation(); deepEqual(seen, [], "custom aggregate false overrides rejected callback as before"); }
  }
  await identityLifecycle.revokeRuntimeAccess({ query: async (statement) => ({ rows: statement.text.includes("pg_terminate_backend") ? [{ terminated: false }] : [] }) }, "core_runtime").then(() => { throw new Error("Runtime identity revocation accepted an unconfirmed termination."); }, () => undefined);
  const restored = [];
  let restoredLogin = false;
  await identityLifecycle.restoreRuntimeIamAccess({ query: async (statement) => { restored.push(statement); if (statement.text === 'ALTER ROLE "core_runtime" LOGIN') restoredLogin = true; return { rows: statement.text.startsWith("SELECT pg_has_role") ? [{ member: true }] : [{ exists: true, can_login: restoredLogin, superuser: false, create_role: false, create_database: false, replication: false, bypass_rls: false, inherit: false }] }; } }, "core_runtime");
  if (restored.length !== 5 || !restored[0].text.startsWith("SELECT EXISTS") || restored[0].values?.[0] !== "core_runtime" || restored[1].text !== 'ALTER ROLE "core_runtime" LOGIN' || !restored[2].text.startsWith("SELECT EXISTS") || !restored[3].text.includes('GRANT rds_iam TO "core_runtime"') || !restored[4].text.startsWith("SELECT pg_has_role") || /password|scram/i.test(JSON.stringify(restored))) throw new Error("Runtime identity restoration did not verify the bounded role before enabling login and restoring IAM membership.");
  const widened = [];
  await identityLifecycle.restoreRuntimeIamAccess({ query: async (statement) => { widened.push(statement); return { rows: [{ exists: true, can_login: false, superuser: false, create_role: false, create_database: true, replication: false, bypass_rls: false, inherit: false }] }; } }, "core_runtime").then(() => { throw new Error("Runtime identity restoration enabled a widened role."); }, () => undefined);
  if (widened.length !== 1 || !widened[0].text.startsWith("SELECT EXISTS")) throw new Error("Runtime identity restoration did not stop before enabling a widened role.");
}

async function proveTaskVerifierDiagnostics() {
  const { createRequire } = await import("node:module");
  const require = createRequire(import.meta.url), crypto = require("node:crypto");
  const originalFetch = globalThis.fetch, originalLog = console.log, originalError = console.error, originalExit = process.exitCode, originalHash = crypto.createHash;
  const output = [], calls = [], env = { PERSISTENCE_VERIFIER_MODE: "create", KANBIEN_PRIVATE_PERSISTENCE_URL: "http://core-server-persistence.kanbien-core-platform.internal:3000", PERSISTENCE_ACCEPTANCE_RECORD_ID: "core-persistence-verifier-fixture", PERSISTENCE_ACCEPTANCE_FACT: "PRIVATE-verifier-fact-canary" };
  const source = (base) => Array.from({ length: 9 }, (_, index) => ({ schema: "core/diagnostic-record/v1", code: "core.persistence.in-memory-boundary-failed", definitionVersion: 1,
    detail: { operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal: base + index } }));
  const first = source(0), second = source(20), failure = (records) => Object.freeze(Object.assign(new Error("PRIVATE-verifier-error-canary"), { diagnosticRecord: records[0], relatedDiagnosticRecords: records.slice(1) }));
  const bodyFailure = failure(first), lateFailure = failure(second);
  console.log = console.error = (value) => output.push(JSON.parse(value));
  const run = async (overrides = {}) => { output.length = calls.length = 0; process.exitCode = 73; await verifier.runKanbienCoreServerPersistenceVerifier({ ...env, ...overrides }); return output[0]; };
  const successful = () => ({ status: 201, ok: true, async json() { return { outcome: "created" }; } });
  try {
    globalThis.fetch = async (...args) => { calls.push(args); return successful(); };
    for (const [overrides, field, condition] of [
      [{ PERSISTENCE_VERIFIER_MODE: undefined }, "mode", "missing"], [{ PERSISTENCE_VERIFIER_MODE: 3 }, "mode", "wrong-type"], [{ PERSISTENCE_VERIFIER_MODE: "PRIVATE-mode-canary" }, "mode", "unsupported"],
      [{ KANBIEN_PRIVATE_PERSISTENCE_URL: undefined }, "base-url", "missing"], [{ KANBIEN_PRIVATE_PERSISTENCE_URL: 3 }, "base-url", "wrong-type"], [{ KANBIEN_PRIVATE_PERSISTENCE_URL: "PRIVATE-url-canary" }, "base-url", "pattern"],
      [{ PERSISTENCE_ACCEPTANCE_RECORD_ID: undefined }, "record-id", "missing"], [{ PERSISTENCE_ACCEPTANCE_RECORD_ID: 3 }, "record-id", "wrong-type"], [{ PERSISTENCE_ACCEPTANCE_RECORD_ID: "PRIVATE-id-canary" }, "record-id", "pattern"],
      [{ PERSISTENCE_ACCEPTANCE_FACT: undefined }, "fact", "wrong-type"], [{ PERSISTENCE_ACCEPTANCE_FACT: "" }, "fact", "empty"], [{ PERSISTENCE_ACCEPTANCE_FACT: "x".repeat(257) }, "fact", "too-long"],
    ]) {
      const result = await run(overrides);
      equal(result.code, "VERIFIER_CONFIGURATION_INVALID"); equal(calls.length, 0); equal(process.exitCode, 1);
      deepEqual(result.observations.map(({ detail }) => detail), [{ task: "verification", operation: "verification", field, condition, effect: "predicate-rejected" }]);
      equal(JSON.stringify(result).includes("PRIVATE-"), false);
    }
    const getterOrder = [];
    const supplied = Object.fromEntries(Object.entries(env).map(([field, value]) => [field, value]));
    for (const [field, value] of Object.entries(env)) Object.defineProperty(supplied, field, { get() { getterOrder.push(field); return field === "PERSISTENCE_VERIFIER_MODE" ? undefined : value; } });
    output.length = 0; await verifier.runKanbienCoreServerPersistenceVerifier(supplied);
    deepEqual(getterOrder, Object.keys(env), "all four original environment reads precede the first predicate");
    for (const mode of ["sync", "async", "json-rejected", "json-threw", "outcome-getter"]) {
      globalThis.fetch = (...args) => {
        calls.push(args);
        if (mode === "sync") throw bodyFailure;
        if (mode === "async") return Promise.reject(bodyFailure);
        const result = successful();
        result.json = function () { equal(this, result); if (mode === "json-threw") throw bodyFailure; return mode === "json-rejected" ? Promise.reject(bodyFailure) : Promise.resolve({ get outcome() { throw bodyFailure; } }); };
        return Promise.resolve(result);
      };
      const result = await run();
      equal(calls.length, 1); equal(result.code, mode === "json-rejected" ? "KANBIEN_CORE_PERSISTENCE_VERIFICATION_REJECTED" : "KANBIEN_CORE_PERSISTENCE_VERIFICATION_UNAVAILABLE");
      const phase = mode === "sync" || mode === "async" ? "fetch" : mode === "outcome-getter" ? "response-predicate" : "response-json";
      const record = result.observations.find(({ code }) => code.endsWith("boundary-failed"));
      equal(record.detail.phase, phase); equal(record.detail.condition, mode === "async" || mode === "json-rejected" ? "rejected" : "threw"); equal(record.detail.effect, "unknown");
      deepEqual([result.diagnostic, ...result.related_diagnostics], first);
      equal(JSON.stringify(result).includes("PRIVATE-"), false);
    }
    const fetchDescriptor = Object.getOwnPropertyDescriptor(globalThis, "fetch"), originalTimeout = AbortSignal.timeout, originalStringify = JSON.stringify;
    try {
      for (const [scenario, phase, effect, expectedOrder, expectedCalls] of [
        ["main-fetch", "fetch", "unknown", ["fetch-selection", "timeout", "body", "fetch-invocation"], 1],
        ["main-timeout", "request-timeout", "not-started", ["fetch-selection", "timeout"], 0],
        ["main-body", "request-projection", "not-started", ["fetch-selection", "timeout", "body"], 0],
        ["live-fetch", "live-fetch", "unknown", ["fetch-selection", "timeout", "fetch-invocation"], 1],
        ["live-timeout", "live-timeout", "not-started", ["fetch-selection", "timeout"], 0],
        ["ready-fetch", "ready-fetch", "unknown", ["fetch-selection", "timeout", "fetch-invocation", "fetch-selection", "timeout", "fetch-invocation"], 2],
        ["ready-timeout", "ready-timeout", "not-started", ["fetch-selection", "timeout", "fetch-invocation", "fetch-selection", "timeout"], 1],
      ]) {
        const order = [];
        let timeouts = 0;
        Object.defineProperty(globalThis, "fetch", { configurable: true, get() {
          order.push("fetch-selection");
          return function (...args) {
            equal(this, undefined, "the original unqualified fetch receiver is preserved");
            order.push("fetch-invocation"); calls.push(args);
            if (scenario === "main-fetch" || scenario === "live-fetch" || scenario === "ready-fetch" && calls.length === 2) throw bodyFailure;
            return Promise.resolve(scenario.startsWith("main") ? successful() : { status: 200, ok: true });
          };
        } });
        AbortSignal.timeout = function (duration) {
          equal(this, AbortSignal); equal(duration, 30_000); order.push("timeout"); timeouts++;
          if (scenario === "main-timeout" || scenario === "live-timeout" || scenario === "ready-timeout" && timeouts === 2) throw bodyFailure;
          return Reflect.apply(originalTimeout, this, [duration]);
        };
        JSON.stringify = function (value, ...args) {
          if (value !== null && typeof value === "object" && Object.hasOwn(value, "record_id") && Object.hasOwn(value, "fact_digest")) {
            order.push("body"); if (scenario === "main-body") throw bodyFailure;
          }
          return Reflect.apply(originalStringify, this, [value, ...args]);
        };
        const result = await run(scenario.startsWith("main") ? {} : { PERSISTENCE_VERIFIER_MODE: "health-ready" });
        deepEqual(order, expectedOrder); equal(calls.length, expectedCalls); equal(output.length, 1); equal(process.exitCode, 1);
        const record = result.observations[0];
        equal(record.detail.phase, phase); equal(record.detail.condition, "threw"); equal(record.detail.effect, effect);
        deepEqual([result.diagnostic, ...result.related_diagnostics], first, "the same raw thrown source survives each independent location");
        equal(originalStringify(result).includes("PRIVATE-"), false);
      }
    } finally {
      Object.defineProperty(globalThis, "fetch", fetchDescriptor); AbortSignal.timeout = originalTimeout; JSON.stringify = originalStringify;
    }
    const digest = originalHash("sha256").update(env.PERSISTENCE_ACCEPTANCE_FACT).digest("hex");
    for (const [mode, status, body, field, condition] of [
      ["create", 503, { outcome: "created" }, "status", "status-mismatch"],
      ["create", 201, null, "body", "wrong-type"], ["create", 201, {}, "outcome", "missing"], ["create", 201, { outcome: "PRIVATE-outcome-canary" }, "outcome", "wrong-outcome"],
      ["read", 200, { outcome: "found" }, "record", "missing-record"], ["read", 200, { outcome: "found", record: null }, "record", "wrong-type"],
      ["read", 200, { outcome: "found", record: { id: "PRIVATE-id-canary", factDigest: digest } }, "record-id-result", "id-mismatch"],
      ["read", 200, { outcome: "found", record: { id: env.PERSISTENCE_ACCEPTANCE_RECORD_ID, factDigest: "PRIVATE-digest-canary" } }, "fact-digest-result", "digest-mismatch"],
    ]) {
      globalThis.fetch = async (...args) => { calls.push(args); return { status, json: async () => body }; };
      const result = await run({ PERSISTENCE_VERIFIER_MODE: mode });
      deepEqual(result.observations.map(({ detail }) => detail), [{ task: "verification", operation: "verification", field, condition, effect: "predicate-rejected" }]);
      equal(JSON.stringify(result).includes("PRIVATE-"), false);
    }
    let statusReads = 0;
    globalThis.fetch = async (...args) => { calls.push(args); return { get status() { return ++statusReads === 1 ? 503 : 200; }, json: async () => ({ outcome: "created" }) }; };
    deepEqual(await run(), { verdict: "accepted", code: "KANBIEN_CORE_PERSISTENCE_RECORD_ACCEPTED" }); equal(statusReads, 2); equal(process.exitCode, 73, "success keeps the caller's original exitCode");
    let rejectReady;
    globalThis.fetch = (url) => { calls.push(url); return String(url).endsWith("/livez") ? Promise.reject(bodyFailure) : new Promise((_resolve, reject) => { rejectReady = reject; }); };
    const firstResult = await run({ PERSISTENCE_VERIFIER_MODE: "health-ready" });
    equal(calls.length, 2); equal(output.length, 1); equal(firstResult.code, "KANBIEN_CORE_PERSISTENCE_HEALTH_VERIFICATION_UNAVAILABLE");
    deepEqual(firstResult.observations.map(({ detail }) => detail.phase), ["live-fetch", "health-settlement"]);
    deepEqual([firstResult.diagnostic, ...firstResult.related_diagnostics], first);
    process.exitCode = 73; rejectReady(lateFailure);
    await new Promise((resolve) => setImmediate(resolve));
    equal(output.length, 2); equal(process.exitCode, 73, "late concurrent evidence cannot change exitCode");
    deepEqual(output[1].observations.map(({ detail }) => detail.phase), ["ready-fetch"]);
    deepEqual([output[1].diagnostic, ...output[1].related_diagnostics], second);
    globalThis.fetch = () => { calls.push("fetch"); throw bodyFailure; };
    await run({ PERSISTENCE_VERIFIER_MODE: "health-ready" }); equal(calls.length, 1, "synchronous first fetch still prevents the second invocation");
    output.length = 0; process.exitCode = 73;
    crypto.createHash = () => { throw bodyFailure; };
    await rejects(() => verifier.runKanbienCoreServerPersistenceVerifier(env), (error) => error === bodyFailure);
    equal(process.exitCode, 73); equal(output[0].observations[0].detail.phase, "fact-digest");
    crypto.createHash = originalHash;
    for (const failure of [bodyFailure, Object.freeze(new Error("PRIVATE-raw-canary")), "PRIVATE-primitive-canary", null]) {
      output.length = 0; process.exitCode = 73;
      await rejects(() => verifier.runKanbienCoreServerPersistenceVerifier(Object.defineProperty({ ...env }, "PERSISTENCE_VERIFIER_MODE", { get() { throw failure; } })), (error) => error === failure);
      equal(process.exitCode, 73); equal(output[0].observations[0].detail.phase, "input-projection"); equal(JSON.stringify(output).includes("PRIVATE-"), false);
    }
  } finally { globalThis.fetch = originalFetch; console.log = originalLog; console.error = originalError; process.exitCode = originalExit; crypto.createHash = originalHash; }
}

async function captureConsole(run) {
  const originalLog = console.log, originalError = console.error, originalExitCode = process.exitCode;
  const records = [];
  console.log = (...values) => records.push(values.join(" "));
  console.error = (...values) => records.push(values.join(" "));
  process.exitCode = undefined;
  try { await run(); return { output: records.join("\n"), exitCode: process.exitCode ?? 0 }; }
  finally { console.log = originalLog; console.error = originalError; process.exitCode = originalExitCode; }
}

async function start(persistence, logger = { write: () => undefined }) {
  const { platformPersistenceDiagnosticCatalog } = await import(pathToFileUrl(join(buildOutput, "platform/persistence/src/diagnostics.js")));
  const started = await serverMain.startPlatformServerProcess({
    diagnosticCatalogs: [platformPersistenceDiagnosticCatalog],
    apps: [program.createKanbienCoreServerPersistenceApp(releaseIdentity, persistence)],
    env: { HOST: "127.0.0.1", PORT: "3000", PLATFORM_SOURCE_COMMIT_SHA: releaseIdentity.sourceCommitSha },
    host: "127.0.0.1",
    port: 0,
    installSignalHandlers: false,
    logger,
  });
  if (!started.ok) throw new Error(`Persistence composition did not start: ${started.error.code}`);
  return started.value;
}

function acceptanceRequest() {
  return { record_id: recordId, fact_digest: factDigest };
}

function fakePersistence({ readiness, create, read }) {
  return {
    closed: false,
    readinessCalls: 0,
    readiness: async function () { this.readinessCalls++; return readiness; },
    createAcceptanceRecord: async () => create,
    readAcceptanceRecord: async () => read === "found" ? { outcome: "found", record: { id: recordId, factDigest } } : { outcome: read },
    deleteAcceptanceRecord: async () => "deleted",
    close: async function close() { this.closed = true; },
  };
}

function request(port, method, path, jsonBody) {
  return new Promise((resolve, reject) => {
    const body = jsonBody === undefined ? undefined : JSON.stringify(jsonBody);
    const requestHandle = httpRequest({
      host: "127.0.0.1",
      port,
      path,
      method,
      headers: body === undefined ? undefined : { "content-type": "application/json", "content-length": Buffer.byteLength(body) },
    }, (response) => {
      let body = "";
      response.setEncoding("utf8");
      response.on("data", (chunk) => { body += chunk; });
      response.on("end", () => resolve({ status: response.statusCode, body }));
    });
    requestHandle.on("error", reject);
    requestHandle.end(body);
  });
}

function assertStatus(response, expectedStatus, explanation) {
  if (response.status !== expectedStatus) {
    throw new Error(`${explanation}: expected ${expectedStatus}, received ${response.status}.`);
  }
}

function assertJson(response, expectedStatus, expectedBody, explanation) {
  assertStatus(response, expectedStatus, explanation);
  if (response.body !== JSON.stringify(expectedBody)) {
    throw new Error(`${explanation}: response body did not match the safe contract.`);
  }
}

function pathToFileUrl(path) {
  return new URL(`file://${path}`).href;
}
