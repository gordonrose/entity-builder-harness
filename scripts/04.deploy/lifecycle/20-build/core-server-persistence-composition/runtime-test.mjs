#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-persistence-composition-runtime
//   version: 2
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-11-27"
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
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readProgramBuildInputs } from "../runnable-program-contract/build-inputs.mjs";
import { planRuntimePackages, writeRuntimePackages } from "../../../../repo/workspace-build/runtime-packages.mjs";

import { fixtureRuntime } from "./fixture-runtime.mjs";
const buildOutput = fixtureRuntime(process.argv[2]);
if (typeof buildOutput !== "string" || buildOutput.length === 0) {
  throw new Error("Usage: runtime-test.mjs <compiled-output-directory>");
}

if (process.argv[3] === "--scheduling") {
  await proveSchedulingComposition();
  console.log("Scheduler target controlled composition proof passed; no database or AWS state was contacted.");
  process.exit(0);
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
await proveSchedulingSyntheticOperations();

console.log("Core-server persistence composition local runtime proof passed.");

async function proveSchedulingSyntheticOperations() {
  const require = createRequire(join(buildOutput, "scheduling-proof-fixture.cjs"));
  const source = name => require(join(buildOutput, "infra/04.deploy/03.product/entrypoints", name + ".js"));
  const helper = source("shared/persistence/scheduling-administration"), config = source("shared/persistence/configuration");
  const policy = source("kanbien-core-server-persistence-administration.main").kanbienCoreSchedulingDatabasePolicy("kanbienpersistence", "core_schema_migration", "core_runtime");
  const { kanbienCoreScheduledProofJobName: jobName, kanbienCoreScheduledProofMessageType: messageType } = source("kanbien-core-server-persistence-scheduling.app");
  const configuration = config.persistenceConfiguration({ PERSISTENCE_POSTGRES_HOST: "postgres", PERSISTENCE_POSTGRES_PORT: "5432", PERSISTENCE_POSTGRES_DATABASE: "kanbienpersistence",
    PERSISTENCE_POSTGRES_SCHEMA: "platform", PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic" }, "administration");
  const id = "a0b1c2d3-e4f5-4a67-8b90-123456789abc", other = "b0b1c2d3-e4f5-4a67-8b90-123456789abc", dueAt = "2026-11-27T12:00:00.000Z";
  const native = Object.freeze(new Error("PRIVATE-PROOF-QUERY-CANARY"));
  const lease = { lease_owner: null, lease_fence: null, lease_acquired_at: null, lease_expires_at: null };
  function fixture() {
    const state = { schedule: null, outbox: null, processing: null, inserted: 0, releases: 0, connected: 0, events: [], selection: null,
      fail: undefined, releaseFailure: undefined, rollbackFailure: undefined };
    const client = { async query(statement) {
      state.events.push(statement);
      const { text, values } = statement;
      if (state.fail && state.fail(text)) throw native;
      if (text === "ROLLBACK" && state.rollbackFailure) throw state.rollbackFailure;
      if (/^(BEGIN|SET LOCAL|COMMIT|ROLLBACK)/.test(text)) return { rows: [] };
      if (text === "SELECT clock_timestamp() AS observed_at") return { rows: [{ observed_at: new Date(dueAt) }] };
      if (text.startsWith("SELECT id FROM")) {
        deepEqual(values, ["entity-smoke.test-entity", other, ...(text.includes("due_at=$3") ? [dueAt] : [])]); equal(text.endsWith("LIMIT 2"), true);
        return { rows: state.selection ?? [] };
      }
      if (text.startsWith("INSERT INTO")) {
        state.inserted++; deepEqual(values, [id, jobName, dueAt, "waiting", null, null]);
        state.schedule = { id, job_name: jobName, due_at: new Date(dueAt), state: "waiting", outbox_entry_id: null, subject_kind: null, subject_id: null };
        return { rows: [state.schedule] };
      }
      deepEqual(values, [id], "every durable lookup must bind only the reserved ID");
      if (text.includes('"platform_schedule"')) return { rows: state.schedule === null ? [] : [state.schedule] };
      if (text.includes('"platform_outbox"')) return { rows: state.outbox === null ? [] : [state.outbox] };
      if (text.includes('"platform_processing"')) return { rows: state.processing === null ? [] : [state.processing] };
      throw new Error("unexpected synthetic proof SQL");
    }, release() { state.releases++; if (state.releaseFailure) throw state.releaseFailure; } };
    const pool = { query() { throw new Error("proof must use one transaction connection"); }, async connect() { state.connected++; return client; }, async end() {} };
    return { state, client, options: { pool, configuration, policy, jobName, messageType } };
  }
  const f = fixture();
  const seed = await helper.seedSchedulingProof({ ...f.options, id, dueAt });
  deepEqual(seed, { schema: "kanbien/scheduling-proof-seed/v1", schedule_id: id, job_name: jobName, due_at: dueAt, disposition: "created" });
  equal((await helper.seedSchedulingProof({ ...f.options, id, dueAt })).disposition, "already-exists"); equal(f.state.inserted, 1);
  await rejects(() => helper.seedSchedulingProof({ ...f.options, id, dueAt: "2026-11-27T12:01:00.000Z" })); equal(f.state.inserted, 1, "different request cannot reuse an existing ID");
  let application = { kind: "acceptance", present: false };
  const observe = (overrides = {}) => helper.observeSchedulingProof({ ...f.options, selection: { kind: "schedule", id },
    readApplication: async (client, selected) => { equal(client, f.client); equal(selected, id); return application; }, ...overrides });
  let before = f.state.events.length;
  const waiting = await observe(); equal(waiting.schedule.state, "waiting"); equal(waiting.outbox, null); equal(waiting.processing, null); equal(waiting.application.present, false);
  equal(f.state.events[before].text, "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY");
  equal(f.state.events.slice(before).some(({ text }) => /^(INSERT|UPDATE|DELETE|CREATE|ALTER|GRANT)/.test(text)), false);
  f.state.schedule = { ...f.state.schedule, state: "delivery-created", outbox_entry_id: id };
  f.state.outbox = { id, subject_kind: "platform.schedule", subject_id: id, message_type: messageType, message_version: 1, delivery_policy: "scheduling.standard",
    created_at: new Date(dueAt), tenant_id: null, correlation_id: null, causation_id: null, state: "published", attempt: 1, ...lease, published_at: new Date(dueAt) };
  f.state.processing = { outbox_entry_id: id, state: "completed", attempt: 1, ...lease, released_at: null, retry_at: null, completion_outcome: "succeeded", completed_at: new Date(dueAt) };
  application = { kind: "acceptance", present: true, fact_digest: createHash("sha256").update(JSON.stringify([id, jobName, dueAt])).digest("hex") };
  const completed = await observe(); equal(completed.outbox.state, "published"); equal(completed.processing.completion.outcome, "succeeded"); deepEqual(completed.application, application);
  deepEqual(completed.delivery_message, { id, type: messageType, version: 1, enqueuedAt: dueAt, idempotencyKey: id, payload: { outboxEntryId: id } });
  equal(waiting.delivery_message, null, "a missing outbox has no repeatable message");
  f.state.outbox.subject_id = other;
  await rejects(observe, error => error.message === "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED");
  f.state.outbox.subject_id = id;
  f.state.processing.completion_outcome = "terminal-failure";
  equal((await observe()).processing.completion.outcome, "terminal-failure", "terminal failure is an observation, never relabelled successful");
  f.state.outbox.attempt = -1;
  await rejects(observe, error => error.diagnosticRecord?.code === "persistence.stored-record-observed", "invalid nullable reads must not be reported as physical absence");
  f.state.outbox.attempt = 1;
  const readFailure = Object.freeze({ code: "CONTROLLED_APPLICATION_READ_FAILURE" });
  f.state.rollbackFailure = Object.freeze(new Error("PRIVATE-ROLLBACK-CANARY")); f.state.releaseFailure = Object.freeze(new Error("PRIVATE-RELEASE-CANARY"));
  const observed = [];
  await rejects(() => helper.observeSchedulingProof({ ...f.options, selection: { kind: "schedule", id }, readApplication: async () => { throw readFailure; } },
    { onObservation: record => { observed.push(record); throw native; } }), error => error === readFailure);
  equal(observed.some(record => record.detail.phase === "rollback"), true); equal(observed.some(record => record.detail.phase === "client-release"), true);
  equal(JSON.stringify(observed).includes("PRIVATE-"), false); equal(f.state.inserted, 1);
  for (const input of [undefined, 7, "PRIVATE-NOT-A-UUID"]) {
    const invalid = fixture();
    await rejects(() => helper.seedSchedulingProof({ ...invalid.options, id: input, dueAt })); equal(invalid.state.connected, 0);
  }
  for (const input of [undefined, {}, "PRIVATE-NOT-A-TIME"]) {
    const invalid = fixture();
    await rejects(() => helper.seedSchedulingProof({ ...invalid.options, id, dueAt: input })); equal(invalid.state.connected, 0);
  }
  const subject = fixture(); subject.state.selection = [{ id }, { id: other }];
  const subjectObserve = () => helper.observeSchedulingProof({ ...subject.options, selection: { kind: "subject", id: other, dueAt, subjectKind: "entity-smoke.test-entity" },
    readApplication: async () => ({ kind: "entity", present: false }) });
  await rejects(subjectObserve, error => error.message === "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED");
  subject.state.selection = [];
  const absent = await subjectObserve(); deepEqual(absent.selection, { kind: "subject", id: other, due_at: dueAt }); equal(absent.schedule, null); equal(absent.application.present, false);
  const untouched = () => helper.observeSchedulingProof({ ...subject.options, selection: { kind: "subject", id: other, subjectKind: "entity-smoke.test-entity" },
    readApplication: async () => ({ kind: "entity", present: true, visibility: "active", lifecycle_state: "active" }) });
  const control = await untouched(); deepEqual(control.selection, { kind: "subject", id: other }); equal(control.schedule, null); equal(control.application.present, true);
  const selectionQuery = subject.state.events.filter(({ text }) => text.startsWith("SELECT id FROM")).at(-1);
  deepEqual(selectionQuery.values, ["entity-smoke.test-entity", other]); equal(selectionQuery.text.includes("due_at"), false);
  subject.state.selection = [{ id }];
  await rejects(untouched, error => error.message === "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED", "an unexpected reminder is not ignored");
  equal(subject.state.events.some(({ text }) => /^(INSERT|UPDATE|DELETE)/.test(text)), false);
}

async function proveSchedulingComposition() {
  const selected = readProgramBuildInputs(process.cwd(), { programId: "kanbien-core-server-persistence-scheduling-worker" });
  writeRuntimePackages(planRuntimePackages({ compiledRoot: buildOutput, assetRoot: process.cwd(), packages: selected.inputs.packages }));
  const require = createRequire(join(buildOutput, "scheduler-fixture.cjs"));
  const source = name => require(join(buildOutput, "infra/04.deploy/03.product/entrypoints", name + ".js"));
  const { schedulingConfiguration } = source("shared/scheduling/configuration");
  const { createSchedulingTargetHandler } = source("shared/scheduling/invocation");
  const { createSchedulingComposition, schedulingRuntimeBudgets } = source("shared/scheduling/composition");
  const proof = source("kanbien-core-server-persistence-scheduling.app");
  const { kanbienCoreAcceptanceDiagnosticCatalog } = source("kanbien-core-server-persistence-diagnostics");
  equal(typeof source("kanbien-core-server-persistence-scheduling-worker.handler").handler, "function");
  const shared = require("@kanbien/core/shared"), persistence = require("@kanbien/platform-persistence");
  const canary = "PRIVATE-SCHEDULER-TARGET-DO-NOT-REPORT";
  const raw = Object.freeze(new Error(canary));
  const certificate = readFileSync("platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt", "utf8");
  const scope = { schema: "platform", dispatchUsername: "core_scheduling_dispatch", workerUsername: "core_scheduling_worker" };
  const env = { PERSISTENCE_POSTGRES_HOST: "postgres", PERSISTENCE_POSTGRES_PORT: "5432", PERSISTENCE_POSTGRES_DATABASE: "kanbienpersistence",
    PERSISTENCE_POSTGRES_SCHEMA: "platform", PERSISTENCE_POSTGRES_IAM_REGION: "eu-west-1", AWS_REGION: "eu-west-1",
    PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-ABCDEFGHIJKLMNOP/core_scheduling_worker",
    PERSISTENCE_SCHEDULING_DATABASE_USERNAME: "core_scheduling_worker", PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/fixture.crt",
    SCHEDULING_QUEUE_URL: "https://sqs.eu-west-1.amazonaws.com/123456789012/scheduler-proof",
    SCHEDULING_QUEUE_ARN: "arn:aws:sqs:eu-west-1:123456789012:scheduler-proof" };
  const checked = schedulingConfiguration(env, scope, "worker", () => certificate);
  equal(checked.persistence.maximumPoolSize, 1);
  equal(checked.persistence.connectionTimeoutMs, 5000);
  equal(checked.persistence.statementTimeoutMs, 3000);
  // Source-owned PG constructors are independently tested to bind query_timeout
  // to statementTimeoutMs + 1000ms. At most eight worker queries include
  // completion reconciliation; handler failure can require a reconnect before
  // release and one bounded visibility change. This is a modeled dependency
  // bound, not a claim about arbitrary code or a hard AWS network SLA.
  const queryDeadline = checked.persistence.statementTimeoutMs + 1000;
  equal(8 * queryDeadline + checked.persistence.connectionTimeoutMs < schedulingRuntimeBudgets.workerMinimumRemainingMs, true);
  equal(7 * queryDeadline + 2 * checked.persistence.connectionTimeoutMs + schedulingRuntimeBudgets.queueRequestTimeoutMs
    < schedulingRuntimeBudgets.workerMinimumRemainingMs, true);
  equal(checked.credentials.username, scope.workerUsername);
  // A relay can perform four PG calls including publication reconciliation,
  // one SQS send and one reconnect. Its reserve is independent of due scanning.
  equal(4 * queryDeadline + 2 * checked.persistence.connectionTimeoutMs + schedulingRuntimeBudgets.queueRequestTimeoutMs
    < schedulingRuntimeBudgets.dispatchMinimumRemainingMs, true);
  equal(6 * queryDeadline + checked.persistence.connectionTimeoutMs < schedulingRuntimeBudgets.dueMinimumRemainingMs, true);
  equal(checked.credentials.region, checked.queue.region);
  let regionReads = 0;
  const regionSource = { ...env };
  Object.defineProperty(regionSource, "PERSISTENCE_POSTGRES_IAM_REGION", { get() { regionReads++; return "eu-west-1"; } });
  equal(schedulingConfiguration(regionSource, scope, "worker", () => certificate).credentials.region, "eu-west-1");
  equal(regionReads, 2, "the existing persistence/IAM owners each snapshot once; relationship validation adds no raw source read");
  const invalid = [
    { SCHEDULING_QUEUE_URL: undefined }, { SCHEDULING_QUEUE_ARN: "bad-" + canary },
    { SCHEDULING_QUEUE_ARN: "arn:aws:sqs:eu-west-2:123456789012:scheduler-proof" },
    { SCHEDULING_QUEUE_URL: "https://sqs.eu-west-1.amazonaws.com/123456789012/other-scope" },
    { PERSISTENCE_POSTGRES_SCHEMA: "entity_smoke" }, { PERSISTENCE_SCHEDULING_DATABASE_USERNAME: "core_runtime" },
    { PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: env.PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE.replace("core_scheduling_worker", "core_scheduling_dispatch") },
    { PERSISTENCE_POSTGRES_IAM_REGION: "eu-west-2" },
  ];
  let milliseconds = Date.parse("2026-11-27T00:00:00.000Z");
  const clock = { now: () => new Date(milliseconds) };
  const ids = { generate: () => shared.uuid("ab583987-27e9-42df-a592-0356205f6fc8") };
  const logs = [];
  const app = resources => proof.createKanbienCoreServerSchedulingApp({ ...resources, persistence: { async createAcceptanceRecord() { return "created"; } } });
  const binding = { ...scope, purpose: "worker", appDiagnosticCatalogs: [kanbienCoreAcceptanceDiagnosticCatalog], createApp: app };
  const fullTime = { getRemainingTimeInMillis: () => 60_000 };
  for (const mutation of invalid) {
    let resources = 0;
    const handler = createSchedulingTargetHandler(binding, { env: { ...env, ...mutation }, clock, uuidGenerator: ids,
      logger: { write: record => { logs.push(record); } }, readCertificate: () => certificate,
      createPool() { resources++; throw raw; }, createClient() { resources++; throw raw; } });
    await rejects(() => handler({ Records: [] }, fullTime), error => error.message === "SCHEDULING_INVOCATION_FAILED" && error.cause === undefined);
    equal(resources, 0, "invalid scope/identity/queue bindings must fail before constructing either client");
  }
  equal(JSON.stringify(logs).includes(canary), false);
  for (const failure of ["client", "close", "none"]) {
    let poolEnds = 0, clientEnds = 0, queries = 0;
    const pool = { async query() { queries++; throw raw; }, async connect() { queries++; throw raw; }, async end() { poolEnds++; if (failure === "close") throw raw; } };
    const handler = createSchedulingTargetHandler({ ...binding, createApp(resources) {
      return { ...app(resources), lifecycle: { beforeStop: resources.close } };
    } }, { env, clock, uuidGenerator: ids,
      logger: { write: record => { logs.push(record); } }, readCertificate: () => certificate, createPool: () => pool,
      createClient() { if (failure === "client") throw raw; return { async send() { throw raw; }, destroy() { clientEnds++; } }; } });
    if (failure === "client") await rejects(() => handler({ Records: [] }, fullTime), error => error.message === "SCHEDULING_INVOCATION_FAILED");
    else deepEqual(await handler({ Records: [] }, fullTime), { batchItemFailures: [] });
    equal(poolEnds, 1, `every created pool closes once (${failure}); selected diagnostics: ${logs.map(record => record.fields?.diagnostic?.code).join(",")}`);
    equal(clientEnds, failure === "client" ? 0 : 1);
    equal(queries, 0, "empty managed batches never access persistence");
  }
  const failedSource = { ...env };
  Object.defineProperty(failedSource, "PERSISTENCE_POSTGRES_HOST", { get() { throw raw; } });
  for (const write of [() => { throw raw; }, () => Promise.reject(raw)]) {
    const handler = createSchedulingTargetHandler(binding, { env: failedSource, clock, logger: { write } });
    await rejects(() => handler({}, fullTime), error => error.message === "SCHEDULING_INVOCATION_FAILED");
  }
  await new Promise(resolve => setImmediate(resolve));
  equal(JSON.stringify(logs).includes(canary), false, "neither selected source reports nor outer errors expose provider strings");
  let rejectedPoolEnds = 0, rejectedClientEnds = 0;
  const failingDispatch = createSchedulingTargetHandler({ ...binding, purpose: "dispatch" }, {
    env: { ...env, PLATFORM_SOURCE_COMMIT_SHA: "a".repeat(40), PERSISTENCE_SCHEDULING_DATABASE_USERNAME: scope.dispatchUsername,
      PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: env.PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE.replace(scope.workerUsername, scope.dispatchUsername) },
    clock, uuidGenerator: ids, logger: { write: record => { logs.push(record); } }, readCertificate: () => certificate,
    createPool: () => ({ async query() { throw raw; }, async connect() { throw raw; }, async end() { rejectedPoolEnds++; } }),
    createClient: () => ({ async send() { throw raw; }, destroy() { rejectedClientEnds++; } }),
  });
  await rejects(() => failingDispatch({}, fullTime), error => error.message === "SCHEDULING_INVOCATION_FAILED" && error.cause === undefined);
  equal(rejectedPoolEnds, 1); equal(rejectedClientEnds, 1);
  const reservedContext = { ...fullTime, awsRequestId: "f85b1263-0d22-44a8-8fa1-77485af9d875",
    invokedFunctionArn: "arn:aws:lambda:eu-west-1:123456789012:function:scheduler-proof:1",
    clientContext: { custom: { scheduling_proof_operation_id: "c1c6c162-c9c8-4a2f-9ef9-158d8ce66f1f" } } };
  await rejects(() => failingDispatch({}, reservedContext), error => error.message === "SCHEDULING_INVOCATION_FAILED");
  const startMarkers = logs.flatMap(record => record.fields?.scheduling_invocation ?? []);
  deepEqual(startMarkers, [{ schema: "kanbien/scheduling-proof-invocation/v1",
    operation_id: reservedContext.clientContext.custom.scheduling_proof_operation_id,
    request_id: reservedContext.awsRequestId, function_arn: reservedContext.invokedFunctionArn,
    source_revision: "a".repeat(40), checked_at: clock.now().toISOString() }]);
  equal(logs.some(record => record.fields?.scheduling_runtime?.kind === "dispatch-completed"), false,
    "a start marker must never claim failed dispatch work completed");
  const hostileContext = { ...reservedContext };
  Object.defineProperty(hostileContext, "clientContext", { get() { throw raw; } });
  await rejects(() => failingDispatch({}, hostileContext), error => error.message === "SCHEDULING_INVOCATION_FAILED");
  equal(rejectedPoolEnds, 3); equal(rejectedClientEnds, 3,
    "optional marker metadata cannot prevent or repeat normal invocation resources");
  equal(logs.filter(record => record.fields?.scheduling_invocation).length, 1);
  equal(JSON.stringify(logs).includes(canary), false);
  const badCatalog = createSchedulingTargetHandler({ ...binding, appDiagnosticCatalogs: [kanbienCoreAcceptanceDiagnosticCatalog, kanbienCoreAcceptanceDiagnosticCatalog] }, {
    env, clock, logger: { write: record => { logs.push(record); } }, createPool() { throw new Error("invalid catalog constructed a pool"); },
  });
  await rejects(() => badCatalog({}, fullTime), error => error.message === "SCHEDULING_INVOCATION_FAILED");
  equal(logs.some(record => record.fields?.diagnostic?.code === "scheduling-target.invocation-failed"), true);

  // The same deployed entrypoint can prove connectivity without composing an
  // application, inspecting business rows, or writing scheduler work.
  const preflightContext = { ...fullTime, awsRequestId: "f85b1263-0d22-44a8-8fa1-77485af9d875",
    invokedFunctionArn: "arn:aws:lambda:eu-west-1:123456789012:function:scheduler-proof:1",
    clientContext: { custom: { scheduling_preflight_operation_id: "c1c6c162-c9c8-4a2f-9ef9-158d8ce66f1f" } } };
  const preflightEvent = { kind: "scheduling-preflight/v1" };
  for (const purpose of ["dispatch", "worker"]) {
    for (const failure of ["none", "identity", "privileges", "connect", "query", "rollback", "dns", "queue", "end", "destroy"]) {
      if (purpose === "dispatch" && ["dns", "queue", "destroy"].includes(failure)) continue;
      const statements = [], commands = [], observed = [];
      let ends = 0, releases = 0, destroys = 0, clients = 0, apps = 0;
      const username = purpose === "dispatch" ? scope.dispatchUsername : scope.workerUsername;
      const selectedEnv = { ...env, PLATFORM_SOURCE_COMMIT_SHA: "a".repeat(40),
        PERSISTENCE_SCHEDULING_DATABASE_USERNAME: username,
        PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: env.PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE.replace(scope.workerUsername, username) };
      const handler = createSchedulingTargetHandler({ ...binding, purpose, createApp() { apps++; throw raw; } }, {
        env: selectedEnv, clock, logger: { write: record => observed.push(record) }, readCertificate: () => certificate,
        createPool: () => ({ async query() { throw raw; }, async connect() {
          if (failure === "connect") throw raw;
          return { async query(statement) {
            statements.push(statement);
            if (statement.text.startsWith("SELECT")) {
              if (failure === "query") throw raw;
              return { rows: [{ username: failure === "identity" ? "unexpected" : username, session_username: username,
                database: "kanbienpersistence", allowed: failure !== "privileges" }] };
            }
            if (statement.text === "ROLLBACK" && failure === "rollback") throw raw;
            return { rows: [] };
          }, release() { releases++; } };
        }, async end() { ends++; if (failure === "end") throw raw; } }),
        resolveQueueAddresses: async hostname => { equal(hostname, "sqs.eu-west-1.amazonaws.com");
          if (failure === "dns") return ["invalid-" + canary];
          return ["10.1.2.4", "10.1.2.3", "10.1.2.4"]; },
        createClient() { clients++; return { async send(command) {
          commands.push(command); return { Attributes: { QueueArn: failure === "queue" ? "wrong-" + canary : env.SCHEDULING_QUEUE_ARN } };
        }, destroy() { destroys++; if (failure === "destroy") throw raw; } }; },
      });
      if (failure === "none") {
        const result = await handler(preflightEvent, preflightContext);
        deepEqual(result, { schema: "kanbien/scheduling-runtime-preflight/v1", purpose,
          operation_id: preflightContext.clientContext.custom.scheduling_preflight_operation_id,
          source_revision: selectedEnv.PLATFORM_SOURCE_COMMIT_SHA, request_id: preflightContext.awsRequestId,
          function_arn: preflightContext.invokedFunctionArn, checked_at: clock.now().toISOString(),
          database: { name: "kanbienpersistence", schema: "platform", username },
          queue: purpose === "dispatch" ? null : { arn: env.SCHEDULING_QUEUE_ARN, address_count: 2,
            address_sha256: createHash("sha256").update(JSON.stringify(["10.1.2.3", "10.1.2.4"])).digest("hex") } });
        equal(JSON.stringify(result).includes("10.1.2."), false);
        deepEqual(observed.filter(record => record.fields?.scheduling_preflight).map(record => record.fields.scheduling_preflight), [result],
          "one selected log receipt retains original operation/request correlation");
      } else {
        await rejects(() => handler(preflightEvent, preflightContext), error => error.message === "SCHEDULING_INVOCATION_FAILED" && error.cause === undefined);
        const expectedCheck = { identity: "database-user", privileges: "database-privileges", connect: "database-connection",
          query: "database-identity", rollback: "database-rollback", dns: "queue-dns", queue: "queue-identity", end: "cleanup", destroy: "cleanup" }[failure];
        equal(observed.some(record => record.fields?.diagnostic?.code === "scheduling-target.preflight-failed"
          && record.fields.diagnostic.detail.check === expectedCheck), true, failure);
      }
      equal(apps, 0); equal(ends, 1); equal(releases, failure === "connect" ? 0 : 1);
      equal(clients, destroys); if (purpose === "dispatch") equal(clients, 0, "dispatch preflight needs no queue permission");
      equal(statements.every(statement => ["BEGIN READ ONLY", "ROLLBACK"].includes(statement.text)
        || statement.text.startsWith("SELECT current_user")), true, "only bounded read-only statements execute");
      equal(commands.every(command => command.constructor.name === "GetQueueAttributesCommand"
        && command.input.QueueUrl === env.SCHEDULING_QUEUE_URL && command.input.AttributeNames.join() === "QueueArn"), true);
      equal(JSON.stringify(observed).includes(canary), false);
    }
  }
  for (const [event, context] of [
    [{ kind: "other" }, preflightContext], [{ kind: "scheduling-preflight/v1", private: canary }, preflightContext],
    [preflightEvent, { ...preflightContext, getRemainingTimeInMillis: () => 30_000 }],
    [preflightEvent, { ...preflightContext, invokedFunctionArn: preflightContext.invokedFunctionArn.replace(":1", ":$LATEST") }],
    [preflightEvent, { ...preflightContext, clientContext: undefined }],
  ]) {
    let resources = 0;
    const handler = createSchedulingTargetHandler(binding, { env: { ...env, PLATFORM_SOURCE_COMMIT_SHA: "a".repeat(40) },
      clock, logger: { write: record => logs.push(record) }, readCertificate: () => certificate,
      createPool() { resources++; throw raw; }, createClient() { resources++; throw raw; } });
    await rejects(() => handler(event, context), error => error.message === "SCHEDULING_INVOCATION_FAILED");
    equal(resources, 0);
  }

  // This single-process fixture connects public capabilities, not database atomicity.
  const outbox = persistence.createInMemoryPlatformOutboxStore();
  const memorySchedules = persistence.createInMemoryPlatformScheduleStore();
  const schedules = { ...memorySchedules, async handoverDue(input) {
    const result = await memorySchedules.handoverDue(input);
    if (result.ok && result.value.disposition === "outbox-created") required(await outbox.create(input.outboxEntry));
    return result;
  } };
  const processing = persistence.createInMemoryPlatformProcessingStore();
  const sent = [], visibility = [], reports = [], runtimeLogs = [];
  let sendFails = true, effects = 0, proofFails = false, logFails = false;
  const observationIdentity = { source_revision: "a".repeat(40), request_id: preflightContext.awsRequestId,
    function_arn: preflightContext.invokedFunctionArn };
  const client = { async send(command) {
    if (command.constructor.name === "SendMessageCommand") { if (sendFails) throw raw; sent.push(command.input.MessageBody); return {}; }
    if (command.constructor.name === "ChangeMessageVisibilityCommand") { visibility.push(command.input); return {}; }
    throw new Error("Managed worker must not receive or delete queue messages directly.");
  } };
  const resources = { configuration: checked, pool: { async end() {} }, clock, uuidGenerator: ids, outbox, schedules, processing, client,
    close: async () => undefined, observationIdentity,
    logger: { write(record) { if (logFails) throw raw; runtimeLogs.push(record); } },
    reporter: { report(record) { reports.push(record); return { status: "written" }; } },
    extraCatalogs: [persistence.platformPersistenceDiagnosticCatalog], diagnosticDefinitions: [...persistence.platformPersistenceDiagnosticCatalog.definitions,
      ...kanbienCoreAcceptanceDiagnosticCatalog.definitions] };
  const application = proof.createKanbienCoreServerSchedulingApp({ ...resources, persistence: { async createAcceptanceRecord() {
    effects++; return proofFails ? "unavailable" : "created";
  } } });
  const lifecycleWorker = required(await require("@kanbien/platform-workers").createPlatformWorkerShell({
    apps: [{ ...application, lifecycle: { beforeStart() {}, beforeStop() {} } }],
    deps: { ...require("@kanbien/platform-runtime").createPlatformRuntimeContextDeps({ clock }), diagnostics: resources.reporter },
  }));
  required(await lifecycleWorker.start()); required(await lifecycleWorker.shutdown());
  equal(lifecycleWorker.lifecycle.events().every(event => event.at === clock.now().toISOString()), true,
    "worker lifecycle timestamps use the same injected clock as its durable processing");
  const schedule = required(persistence.createPlatformSchedule({ jobName: proof.kanbienCoreScheduledProofJobName, dueAt: clock.now().toISOString() }, ids));
  required(await schedules.create(schedule));
  const dispatch = await createSchedulingComposition({ ...resources, app: application, purpose: "dispatch" });
  await rejects(() => dispatch.run({ ignored: canary }, fullTime), error => error.diagnosticRecord.code === "aws-lambda.dispatch-outcome-failed");
  equal(runtimeLogs.length, 0, "failed relay is not logged as a completed dispatch");
  equal((await schedules.get(schedule.id)).state, "delivery-created");
  equal(sent.length, 0);
  sendFails = false; milliseconds += 90_001;
  const later = await dispatch.run({}, fullTime);
  equal(later.delivery.inspected, 0); equal(later.published, 1, "an idle due scan still relays old backlog");
  deepEqual(runtimeLogs[0].fields.scheduling_runtime, { schema: "kanbien/scheduling-runtime-observation/v1",
    ...observationIdentity, purpose: "dispatch", observed_at: clock.now().toISOString(), kind: "dispatch-completed", result: later, trigger: null });
  const trigger = { schedule_arn: "arn:aws:scheduler:eu-west-1:123456789012:schedule/proof/due-pass",
    scheduled_at: clock.now().toISOString(), execution_id: "opaque/aws:scheduler=execution", attempt: "1" };
  await dispatch.run({ scheduler: trigger }, fullTime);
  deepEqual(runtimeLogs.at(-1).fields.scheduling_runtime.trigger, { schedule_arn: trigger.schedule_arn, scheduled_at: trigger.scheduled_at,
    execution_sha256: createHash("sha256").update(trigger.execution_id).digest("hex"), attempt: 1 });
  const unsafeTrigger = {}; Object.defineProperty(unsafeTrigger, "scheduler", { enumerable: true, get() { throw raw; } });
  await dispatch.run(unsafeTrigger, fullTime);
  equal(runtimeLogs.at(-1).fields.scheduling_runtime.trigger, null, "malformed event metadata cannot prevent a due pass");
  equal(JSON.stringify(runtimeLogs).includes(trigger.execution_id), false);
  equal(sent.length, 1);
  const native = body => ({ Records: [{ eventSource: "aws:sqs", eventSourceARN: env.SCHEDULING_QUEUE_ARN,
    messageId: "native-id", receiptHandle: "fixture-receipt", body }] });
  const worker = await createSchedulingComposition({ ...resources, app: application, purpose: "worker" });
  deepEqual(await worker.run(native(sent[0]), { getRemainingTimeInMillis: () => 44_999 }), { batchItemFailures: [{ itemIdentifier: "native-id" }] });
  equal(effects, 0); equal(await processing.get(schedule.id), null);
  await worker.close();
  const deliver = async body => { const next = await createSchedulingComposition({ ...resources, app: application, purpose: "worker" });
    try { return await next.run(native(body), fullTime); } finally { await next.close(); } };
  deepEqual(await deliver(sent[0]), { batchItemFailures: [] });
  equal(effects, 1); equal((await processing.get(schedule.id)).completion.outcome, "succeeded");
  deepEqual(await deliver(sent[0]), { batchItemFailures: [] }); equal(effects, 1, "new invocation suppresses duplicate completed work");
  const deliveredLogs = runtimeLogs.map(row => row.fields?.scheduling_runtime).filter(row => row?.kind === "delivery-completed");
  deepEqual(deliveredLogs.map(row => [row.outbox_sha256, row.attempt, row.idempotency]), [
    [createHash("sha256").update(schedule.id).digest("hex"), 1, "durable-processed"],
    [createHash("sha256").update(schedule.id).digest("hex"), 1, "durable-skipped"],
  ]);
  equal(JSON.stringify(runtimeLogs).includes(schedule.id), false, "no raw outbox identity leaves runtime evidence");
  logFails = true;
  deepEqual(await deliver(sent[0]), { batchItemFailures: [] }); equal(effects, 1, "logger failure cannot replay completed work");
  logFails = false;
  const withoutMetadata = await createSchedulingComposition({ ...resources, observationIdentity: undefined, app: application, purpose: "worker" });
  const beforeMissingMetadata = runtimeLogs.filter(row => row.fields?.scheduling_runtime).length;
  deepEqual(await withoutMetadata.run(native(sent[0]), fullTime), { batchItemFailures: [] });
  await withoutMetadata.close();
  equal(runtimeLogs.filter(row => row.fields?.scheduling_runtime).length, beforeMissingMetadata, "missing real invocation metadata omits evidence, not execution");
  const wrongSource = native(sent[0]); wrongSource.Records[0].eventSourceARN += "-other";
  const guarded = await createSchedulingComposition({ ...resources, app: application, purpose: "worker" });
  await rejects(() => guarded.run(wrongSource, fullTime)); await guarded.close(); equal(effects, 1);

  const nextIds = { generate: () => shared.uuid("7bd34f60-9fbe-42c9-8ea9-dd5df2775ba6") };
  const retrySchedule = required(persistence.createPlatformSchedule({ jobName: proof.kanbienCoreScheduledProofJobName, dueAt: clock.now().toISOString() }, nextIds));
  required(await schedules.create(retrySchedule)); await dispatch.run({}, fullTime); proofFails = true;
  const retryBody = sent[1];
  for (let attempt = 1; attempt <= 3; attempt++) {
    deepEqual(await deliver(retryBody), { batchItemFailures: [{ itemIdentifier: "native-id" }] });
    const state = await processing.get(retrySchedule.id); equal(state.attempt, attempt);
    if (attempt < 3) { equal(state.state, "retry-eligible"); equal(Date.parse(state.retryAt), milliseconds + 5000); }
    else equal(state.completion.outcome, "terminal-failure");
    milliseconds += 5000;
  }
  equal(visibility.length, 2); equal(visibility.every(value => value.VisibilityTimeout === 5), true);
  const beforeTerminal = effects; deepEqual(await deliver(retryBody), { batchItemFailures: [{ itemIdentifier: "native-id" }] });
  equal(effects, beforeTerminal, "terminal work remains unacknowledged for native redrive without executing again");
  equal(JSON.stringify(reports).includes(canary), false);
  equal(runtimeLogs.filter(row => row.fields?.scheduling_runtime?.kind === "delivery-completed").length, 2,
    "failed and terminal work is never logged as successful delivery");
  equal(JSON.stringify(runtimeLogs).includes(canary), false);
  // Feed actual target-composition log projections through the provider proof
  // reader, rather than keeping a second hand-written DTO fixture in Python.
  // Only AWS transport/system messages are controlled in this handoff test.
  const runtimeObservations = runtimeLogs.map(row => row.fields?.scheduling_runtime).filter(Boolean);
  const readback = execFileSync("python3", ["-B", "-c", `
import importlib.util,json,sys
from datetime import datetime,timedelta
spec=importlib.util.spec_from_file_location("runtime_proof","scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/proof.py")
owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
rows=json.load(sys.stdin)
for body in rows:
 at=datetime.fromisoformat(body["observed_at"].replace("Z","+00:00")); stamp=int(at.timestamp()*1000)
 messages=[{"type":"platform.start","record":{"requestId":body["request_id"],"version":body["function_arn"].rsplit(":",1)[1]}},
  {"level":"info","message":"Scheduling runtime observation.","fields":{"scheduling_runtime":body}},
  {"type":"platform.report","record":{"requestId":body["request_id"],"status":"success","metrics":{"billedDurationMs":1000,"memorySizeMB":512}}}]
 function,version=body["function_arn"].rsplit(":",2)[1:]
 stream=f"{at:%Y/%m/%d}/{function}[{version}][controlled-runtime-handoff]"
 events=[{"eventId":str(i),"logStreamName":stream,"timestamp":stamp+i-1,"message":json.dumps(value)} for i,value in enumerate(messages)]
 expected={"purpose":body["purpose"],"source_revision":body["source_revision"],"version_arn":body["function_arn"],"image_uri":"controlled","log_group":"controlled"}
 result=owner.runtime_records(events,expected=expected,started_at=(at-timedelta(seconds=1)).isoformat().replace("+00:00","Z"),ended_at=(at+timedelta(seconds=1)).isoformat().replace("+00:00","Z"))
 assert result[0]["observation"]==body
print(len(rows))
`], { input: JSON.stringify(runtimeObservations), encoding: "utf8", timeout: 10_000 });
  equal(Number(readback.trim()), runtimeObservations.length);
  function required(result) { if (!result.ok) throw result.error; return result.value; }
}

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
