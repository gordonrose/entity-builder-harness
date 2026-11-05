#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-persistence-observability-runtime
//   version: 3
//   status: draft
//   created_on: "2026-10-26"
//   updated_on: "2026-10-31"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [sre, security]
//   kind: script
//   purpose: Prove the packaged server owns an independent PostgreSQL readiness observation and sends its approved metric to a task-local OTLP collector.
//   portability: { class: internal, targets: [] }
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.core-server-persistence-composition
//     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh

import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { createServer as createTcpServer } from "node:net";
import { join, resolve } from "node:path";

import { fixtureRuntime } from "./fixture-runtime.mjs";
const compiled = fixtureRuntime(process.argv[2]);
if (compiled.length === 0) throw new Error("Usage: observability-runtime-test.mjs <compiled-output-directory>");

const collector = await startCollector();
const serverPort = await availablePort();
const fakeDriver = join(compiled, "node_modules/pg");
fs.mkdirSync(fakeDriver, { recursive: true });
fs.writeFileSync(join(fakeDriver, "index.js"), `
exports.Pool = class Pool {
  constructor(options) { globalThis.__kanbienPersistencePoolOptions = options; globalThis.__kanbienPoolConstructions = (globalThis.__kanbienPoolConstructions ?? 0) + 1; }
  on() { return this; }
  async query() { globalThis.__kanbienReadinessQueries = (globalThis.__kanbienReadinessQueries ?? 0) + 1; if (globalThis.__kanbienReadinessFailure) throw { code: '28P01', message: 'password=synthetic-readiness-canary' }; return { rows: [], rowCount: 1 }; }
  async end() { globalThis.__kanbienPersistencePoolEnded = true; globalThis.__kanbienPoolEndCalls = (globalThis.__kanbienPoolEndCalls ?? 0) + 1; }
};
`);

const actualCertificate = fs.readFileSync("platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt", "utf8");
const originalRead = fs.readFileSync;
const originalLog = console.log;
const originalError = console.error;
const output = [];
fs.readFileSync = (path, ...args) => path === "/app/assets/fixture.crt"
  ? actualCertificate
  : originalRead(path, ...args);
console.log = (...values) => output.push(values.join(" "));
console.error = (...values) => output.push(values.join(" "));

try {
  const require = createRequire(join(compiled, "observability-runtime-test.cjs"));
  const server = require(join(compiled, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.js"));
  const telemetry = require(join(compiled, "infra/04.deploy/03.product/entrypoints/kanbien-platform-observability.js"));
  const environment = {
    NODE_ENV: "test",
    HOST: "127.0.0.1",
    PORT: String(serverPort),
    PLATFORM_HEALTH_READYZ_EXPOSURE: "synthetic-private-health-setting",
    PLATFORM_SERVER_EXIT_AFTER_START: "1",
    PLATFORM_SOURCE_COMMIT_SHA: "a".repeat(40),
    PERSISTENCE_POSTGRES_HOST: "postgres",
    PERSISTENCE_POSTGRES_PORT: "5432",
    PERSISTENCE_POSTGRES_DATABASE: "kanbienpersistence",
    PERSISTENCE_POSTGRES_SCHEMA: "platform",
    PERSISTENCE_POSTGRES_IAM_REGION: "eu-west-1",
    PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-ABCDEFGHIJKLMNOP/core_runtime",
    PERSISTENCE_RUNTIME_DATABASE_USERNAME: "core_runtime",
    PERSISTENCE_MIGRATION_DATABASE_USERNAME: "core_schema_migration",
    PERSISTENCE_ADMINISTRATOR_CREDENTIALS: JSON.stringify({ username: "core_administrator", password: "synthetic-administrator" }),
    PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-administrator",
    PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME: "core_runtime",
    PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/fixture.crt",
    PERSISTENCE_ACCEPTANCE_RECORD_ID: "core-persistence-config-fixture",
    PERSISTENCE_ACCEPTANCE_FACT_DIGEST: "a".repeat(64),
    PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN: "synthetic-test-token",
    PLATFORM_OBSERVABILITY_METRICS_PROVIDER: "cloudwatch-otel",
    PLATFORM_OBSERVABILITY_METRICS_ENDPOINT: "http://127.0.0.1:4318/v1/metrics",
    PLATFORM_OBSERVABILITY_METRICS_REGION: "eu-west-1",
    PLATFORM_OBSERVABILITY_SERVICE_NAME: "kanbien-core-server-persistence",
    PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT: "kanbien-core-platform",
    PLATFORM_OBSERVABILITY_EXPORT_INTERVAL_MS: "30000",
    PLATFORM_OBSERVABILITY_EXPORT_TIMEOUT_MS: "5000",
    PLATFORM_OBSERVABILITY_TARGET: "kanbien-core-platform",
    PLATFORM_OBSERVABILITY_SCOPE: "core-server-persistence",
    PLATFORM_OBSERVABILITY_WORKLOAD: "core-server",
    PLATFORM_OBSERVABILITY_DEPENDENCY: "postgresql",
    PLATFORM_OBSERVABILITY_READINESS_CADENCE_MS: "30000",
    PLATFORM_OBSERVABILITY_READINESS_TIMEOUT_MS: "5000",
    PLATFORM_OBSERVABILITY_READINESS_STALE_AFTER_MS: "180000",
    PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON: '[{"sourceName":"platform.dependency.readiness","sourceKind":"gauge","sourceUnit":"count","instrumentName":"kanbien.core_server.postgresql_readiness","description":"Periodic PostgreSQL readiness from the core server","allowedLabelNames":["target","scope","workload","dependency","readiness"],"cardinalityLimit":16}]',
  };
  const checked = telemetry.observabilityConfigurationFromTargetEnvironment(environment, true);
  assert.equal(checked.ok, true);
  let constructions = 0;
  const construct = () => { constructions++; return {}; };
  const failed = (env, expected) => {
    const result = telemetry.observabilityConfigurationFromTargetEnvironment(env, true);
    assert.equal(result.ok, false);
    assert.equal(result.error.code, "KANBIEN_PLATFORM_TARGET_OBSERVABILITY_CONFIG_INVALID");
    assert.equal(result.error.diagnosticRecord.code, "observability.configuration-invalid");
    assert.equal(result.error.diagnosticRecord.detail.effect, "not-started");
    for (const issue of expected) assert.ok(result.error.diagnosticRecord.detail.issues.some((actual) => JSON.stringify(actual) === JSON.stringify(issue)), JSON.stringify(issue));
    assert.equal(JSON.stringify(result).includes("synthetic-private-canary"), false);
    const factory = telemetry.observabilityFromTargetEnvironment(env, construct);
    // Readiness is optional for the general server/worker factory.
    if (expected.some((issue) => !issue.setting.startsWith("readiness."))) assert.equal(factory.ok, false);
    return result;
  };
  for (const provider of [undefined, "", "none"]) {
    const disabled = { PLATFORM_OBSERVABILITY_METRICS_PROVIDER: provider };
    Object.defineProperty(disabled, "PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON", { get() { throw new Error("Disabled settings must not be inspected"); } });
    assert.deepEqual(telemetry.observabilityConfigurationFromTargetEnvironment(disabled, true), { ok: true, value: { options: undefined, readiness: undefined } });
  }
  for (const [value, reason] of [["other", "unsupported"], [" ", "blank"], [1, "wrong-type"]]) failed({ ...environment, PLATFORM_OBSERVABILITY_METRICS_PROVIDER: value }, [{ setting: "metrics.provider", reason }]);
  for (const [value, reason] of [[undefined, "missing"], [" ", "blank"], [1, "wrong-type"], ["synthetic-private-canary", "invalid-json"], ["null", "wrong-shape"], ["{}", "wrong-shape"], ["[]", "empty"]]) {
    failed({ ...environment, PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON: value }, [{ setting: "metrics.series", reason }]);
  }
  for (const [value, reason] of [[undefined, "missing"], [" ", "blank"], ["NaN", "invalid-integer"], ["Infinity", "not-finite"], ["-1", "not-positive"], ["1.5", "invalid-integer"], ["999", "interval-too-short"]]) {
    failed({ ...environment, PLATFORM_OBSERVABILITY_EXPORT_INTERVAL_MS: value }, [{ setting: "metrics.export-interval", reason }]);
  }
  for (const value of [" 1000 ", "1e3", "0x3e8", "+1000", "01000"]) {
    const result = telemetry.observabilityConfigurationFromTargetEnvironment({ ...environment, PLATFORM_OBSERVABILITY_EXPORT_INTERVAL_MS: value, PLATFORM_OBSERVABILITY_EXPORT_TIMEOUT_MS: "1000", PLATFORM_OBSERVABILITY_SERVICE_NAME: " padded " });
    assert.equal(result.ok, true);
    assert.equal(result.value.options.exportIntervalMs, 1000);
    assert.equal(result.value.options.serviceName, " padded ");
  }
  failed({ ...environment, PLATFORM_OBSERVABILITY_METRICS_ENDPOINT: "http://collector.metrics.internal:4318/v1/metrics" }, [{ setting: "metrics.delivery-boundary", reason: "boundary-mismatch" }]);
  failed({ ...environment, PLATFORM_OBSERVABILITY_DELIVERY_BOUNDARY: "private-collector-service" }, [{ setting: "metrics.delivery-boundary", reason: "boundary-mismatch" }]);
  for (const [value, reason] of [[1, "wrong-type"], [" ", "blank"], ["public", "unsupported"]]) failed({ ...environment, PLATFORM_OBSERVABILITY_DELIVERY_BOUNDARY: value }, [{ setting: "metrics.delivery-boundary", reason }]);
  assert.equal(telemetry.observabilityConfigurationFromTargetEnvironment({ ...environment, PLATFORM_OBSERVABILITY_DELIVERY_BOUNDARY: "private-collector-service", PLATFORM_OBSERVABILITY_METRICS_ENDPOINT: "http://collector.metrics.internal:4318/v1/metrics" }).ok, true);
  const combined = failed({ ...environment, PLATFORM_OBSERVABILITY_SERVICE_NAME: " ", PLATFORM_OBSERVABILITY_EXPORT_TIMEOUT_MS: "30001", PLATFORM_OBSERVABILITY_READINESS_TIMEOUT_MS: "30000", PLATFORM_OBSERVABILITY_READINESS_STALE_AFTER_MS: "59999" }, [
    { setting: "metrics.service-name", reason: "blank" }, { setting: "metrics.export-timeout", reason: "timeout-exceeds-interval" },
    { setting: "readiness.timeout", reason: "timeout-not-shorter-than-cadence" }, { setting: "readiness.stale-after", reason: "stale-deadline-too-short" },
  ]);
  assert.equal(combined.error.diagnosticRecord.detail.truncated, false);
  const series = JSON.parse(environment.PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON)[0];
  failed({ ...environment, PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON: JSON.stringify([series, { ...series, allowedLabelNames: ["target", "target"], description: " " }]) }, [
    { setting: "series.source-name", reason: "duplicate", index: 1, relatedIndex: 0 },
    { setting: "series.description", reason: "blank", index: 1 },
    { setting: "series.allowed-labels", reason: "duplicate", index: 1, attributeIndex: 1, relatedIndex: 0 },
  ]);
  assert.equal(constructions, 0, "Invalid metrics must not reach runtime construction.");
  const unknown = telemetry.createTargetObservabilityRuntime(checked.value.options, () => { throw new Error("synthetic-private-canary"); });
  assert.equal(unknown.ok, false);
  assert.deepEqual(unknown.error.diagnosticRecord.detail, { phase: "runtime-construction", reason: "unclassified-construction-failure", effect: "not-assessed" });
  assert.equal(JSON.stringify(unknown).includes("synthetic-private-canary"), false);

  const fakeRuntime = { metrics: { record() {} }, async forceFlush() {}, async shutdown() {} };
  let selectedBinding, selectedObservations, receivedOptions, constructorCalls = 0;
  const compatibleConstructor = (options, binding, observations) => { constructorCalls++; receivedOptions = options; selectedBinding = binding; selectedObservations = observations; return fakeRuntime; };
  assert.equal(telemetry.createTargetObservabilityRuntime(checked.value.options, compatibleConstructor).value, fakeRuntime);
  assert.equal(receivedOptions, checked.value.options);
  assert.equal(typeof selectedBinding?.report, "function", "Target selects process-owned diagnostics without a route profile.");
  assert.equal(typeof selectedObservations?.reporter?.report, "function");
  assert.deepEqual(selectedObservations.context, { capability: "observability", operation: "metrics", stage: "startup" });
  const injected = { report() { throw new Error("synthetic-private-canary"); } };
  assert.equal(telemetry.createTargetObservabilityRuntime(checked.value.options, compatibleConstructor, injected).value, fakeRuntime);
  assert.equal(selectedBinding, injected);
  assert.equal(telemetry.createTargetObservabilityRuntime(checked.value.options, compatibleConstructor, false).value, fakeRuntime);
  assert.equal(selectedBinding, undefined, "Existing constructor remains argument two; explicit false disables lifecycle reporting.");
  assert.equal(selectedObservations, undefined, "Existing explicit false also disables the default boundary reporter.");
  assert.deepEqual(telemetry.createTargetObservabilityRuntime(undefined, compatibleConstructor, injected), { ok: true, value: undefined });
  assert.deepEqual(telemetry.observabilityFromTargetEnvironment({ PLATFORM_OBSERVABILITY_METRICS_PROVIDER: "none" }, compatibleConstructor, injected), { ok: true, value: undefined });
  assert.equal(constructorCalls, 3, "Disabled provider constructs neither runtime nor target reporter.");
  const sourceCore = require(join(compiled, "packages/core/src/monitoring/index.js"));
  const sourceRecords = Array.from({ length: 9 }, (_, ordinal) => sourceCore.coreMonitoringValidationDiagnosticRecord({ operation: "signal-definition", field: "signal-intent", reason: "closed-value-rejected", ordinal, effect: "rejected" }));
  const sourceFailure = Object.freeze({ diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: sourceRecords.slice(1), private: "synthetic-private-canary" });
  const observedBoundaries = [], observedContexts = [];
  const sourceObservation = { reporter: { report(record, context) { observedBoundaries.push(record); observedContexts.push(context); return { status: "written" }; } }, context: { capability: "observability", operation: "metrics", stage: "startup" } };
  const sourceResult = telemetry.createTargetObservabilityRuntime(checked.value.options, () => { throw sourceFailure; }, false, sourceObservation);
  assert.equal(sourceResult.ok, false);
  assert.equal(sourceResult.error.diagnosticRecord.code, "observability.runtime-construction-failed", "Legacy construction result remains primary.");
  assert.equal(observedBoundaries.length, 10);
  assert.deepEqual(observedBoundaries[0].detail, { operation: "metric-runtime-construction", phase: "runtime-construction", reason: "threw", effect: "unknown" });
  assert.deepEqual(observedBoundaries.slice(1), sourceRecords);
  assert.ok(observedContexts.every((context) => context.stage === "startup"));
  assert.equal(JSON.stringify(observedBoundaries).includes("synthetic-private-canary"), false);
  const observability = require(join(compiled, "platform/observability/src/diagnostics.js"));
  const originalReporter = observability.createPlatformDiagnosticReporter;
  let reporterAttempts = 0;
  try {
    observability.createPlatformDiagnosticReporter = () => { reporterAttempts++; throw new Error("synthetic-private-canary"); };
    assert.equal(telemetry.createTargetObservabilityRuntime(checked.value.options, compatibleConstructor).value, fakeRuntime);
    assert.equal(constructorCalls, 4, "Diagnostic setup failure must still call the original constructor once.");
    assert.equal(selectedBinding, undefined);
    assert.deepEqual(telemetry.createTargetObservabilityRuntime(undefined, compatibleConstructor), { ok: true, value: undefined });
    assert.equal(reporterAttempts, 1, "Disabled metrics must not attempt reporter construction.");
  } finally { observability.createPlatformDiagnosticReporter = originalReporter; }

  const previousExit = process.exitCode;
  let tokenRequests = 0;
  const Signer = require("@aws-sdk/rds-signer").Signer;
  const originalGetAuthToken = Signer.prototype.getAuthToken;
  const invalidEnvironment = { ...environment, PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN: undefined, PLATFORM_OBSERVABILITY_SERVICE_NAME: " ", PLATFORM_OBSERVABILITY_READINESS_TIMEOUT_MS: "30000" };
  try {
    Signer.prototype.getAuthToken = async () => { tokenRequests++; return "synthetic-test-token"; };
    await server.runKanbienCoreServerPersistenceMain(invalidEnvironment);
  } finally {
    Signer.prototype.getAuthToken = originalGetAuthToken;
  }
  assert.equal(process.exitCode, 1);
  process.exitCode = previousExit;
  assert.equal(globalThis.__kanbienPoolConstructions ?? 0, 0, "Known configuration failures must precede database allocation.");
  assert.equal(tokenRequests, 0, "Validation must not request an IAM token; preparing a lazy signer is not token generation.");
  const rejected = output.map((line) => JSON.parse(line)).find((record) => record.diagnostic?.code === "observability.configuration-invalid");
  assert.ok(rejected, "Startup must preserve the governed observability record.");
  assert.equal(rejected.error.code, "KANBIEN_PLATFORM_TARGET_OBSERVABILITY_CONFIG_INVALID");
  assert.deepEqual(rejected.diagnostic.detail.issues, [{ setting: "metrics.service-name", reason: "blank" }, { setting: "readiness.timeout", reason: "timeout-not-shorter-than-cadence" }]);

  const adapter = require("@kanbien/platform-adapter-aws-observability-cloudwatch");
  const originalConstruct = adapter.createCloudWatchOtelMetricsRuntime;
  try {
    adapter.createCloudWatchOtelMetricsRuntime = () => { throw new Error("synthetic-private-canary"); };
    globalThis.__kanbienPersistencePoolEnded = false;
    await server.runKanbienCoreServerPersistenceMain(environment);
    assert.equal(process.exitCode, 1);
    assert.equal(globalThis.__kanbienPersistencePoolEnded, true, "A later unexpected exporter construction failure must close the already-created pool.");
    const constructionFailure = output.map((line) => JSON.parse(line)).find((record) => record.diagnostic?.code === "observability.runtime-construction-failed");
    assert.ok(constructionFailure);
    assert.equal(constructionFailure.diagnostic.detail.effect, "not-assessed");
  } finally {
    adapter.createCloudWatchOtelMetricsRuntime = originalConstruct;
    process.exitCode = previousExit;
  }

  const processModule = require(join(compiled, "platform/server/src/main.js"));
  const originalStart = processModule.startPlatformServerProcess;
  const readinessModule = require(join(compiled, "platform/observability/src/readiness-observation.js"));
  const originalObserverFactory = readinessModule.createPlatformReadinessObserver;
  let healthRequests = 0, observerConstructions = 0, projectionCases = 0;
  try {
    readinessModule.createPlatformReadinessObserver = (options) => {
      observerConstructions++;
      assert.equal(options.observations?.reporter, options.diagnostics, "Actual target uses its selected reporter for raw readiness boundaries too.");
      assert.deepEqual(options.observations?.context, { capability: "observability", operation: "readiness-observation", stage: "readiness" });
      const codes = new Set(options.observations.definitions.map((definition) => definition.code));
      for (const code of ["core.monitoring.validation-rejected", "persistence.credential-rejected", "security.peer-identity-verification-failed", "observability.boundary-failed", "platform-contracts.operational-event-rejected", "platform-contracts.operational-boundary-failed"]) assert.ok(codes.has(code), code);
      const actualObserver = originalObserverFactory(options);
      const exerciseProjection = observerConstructions === 1;
      return { observe: async () => {
        if (exerciseProjection) for (const field of ["identity", "clock", "event"]) {
          const queriesBefore = globalThis.__kanbienReadinessQueries ?? 0;
          const closesBefore = globalThis.__kanbienPoolEndCalls ?? 0;
          const outputBefore = output.length;
          const projectionFailure = Object.freeze(new Error("synthetic-private-canary"));
          let probes = 0;
          const actualProbe = options.probe;
          const failedOptions = { ...options, probe: async () => {
            probes++;
            const actualResult = await actualProbe();
            assert.equal(actualResult.readiness, "ready", "Use the real target probe result, not a synthetic dependency outcome.");
            Object.defineProperties(actualResult, { diagnosticRecord: { value: sourceRecords[0], enumerable: true }, relatedDiagnosticRecords: { value: sourceRecords.slice(1), enumerable: true } });
            return actualResult;
          }, ...(field === "clock" ? { clock: { now() { throw projectionFailure; } } } : {}) };
          if (field === "identity") Object.defineProperty(failedOptions, "identity", { get() { throw projectionFailure; } });
          if (field === "event") failedOptions.identity = { ...options.identity, target: "synthetic-private-canary".repeat(10) };
          const failingObserver = originalObserverFactory(failedOptions);
          await assert.rejects(failingObserver.observe(), (error) => field === "event" ? error instanceof Error && error.message === "PLATFORM_OPERATIONAL_EVENT_INVALID" : error === projectionFailure);
          assert.equal(probes, 1); assert.equal((globalThis.__kanbienReadinessQueries ?? 0) - queriesBefore, 1, "A later projection failure must not replay the actual target probe.");
          assert.equal(globalThis.__kanbienPoolEndCalls ?? 0, closesBefore, "Primitive observation failure does not own or close the target pool.");
          const observed = output.slice(outputBefore).map((line) => JSON.parse(line)).filter((record) => record.message === "platform.diagnostic.observed" && record.fields?.operation === "readiness-observation");
          assert.equal(observed.length, field === "event" ? 11 : 10);
          assert.deepEqual(observed[0].fields.diagnostic.detail, { operation: "readiness-observation", phase: field === "identity" ? "identity-projection" : field === "event" ? "event-validation" : "clock", field, reason: field === "event" ? "invalid-event" : "threw", effect: "event-not-returned" });
          if (field === "event") assert.deepEqual(observed[1].fields.diagnostic, { schema: "core/diagnostic-record/v1", code: "platform-contracts.operational-event-rejected", definitionVersion: 1,
            detail: { operation: "readiness-event", field: "target", condition: "invalid-format", phase: "validation", effect: "predicate-rejected" } });
          assert.deepEqual(observed.slice(field === "event" ? 2 : 1).map((record) => record.fields.diagnostic), sourceRecords, "Successful real probe source9 survives a later projection/event failure alongside independent owned locations.");
          assert.ok(observed.every((record) => record.fields.stage === "readiness"));
          assert.equal(JSON.stringify(observed).includes("synthetic-private-canary"), false);
          projectionCases++;
        }
        return actualObserver.observe();
      } };
    };
    processModule.startPlatformServerProcess = async (options) => {
      assert.deepEqual(options.diagnosticCatalogs.map((catalog) => catalog.owner), ["persistence"], "The actual target explicitly selects its dependency catalog.");
      const started = await originalStart(options);
      if (started.ok) {
        try {
          const queriesBefore = globalThis.__kanbienReadinessQueries ?? 0;
          const health = await fetch(`http://127.0.0.1:${started.value.handle.port}/readyz`);
          assert.equal(globalThis.__kanbienReadinessQueries - queriesBefore, 1, "Actual target health requests invoke one query before the independent observer starts.");
          assert.equal(health.status, globalThis.__kanbienReadinessFailure ? 503 : 200);
          const summary = await health.json();
          assert.equal(JSON.stringify(summary).includes("diagnostic"), false);
          healthRequests++;
        } catch (error) { await started.value.close(); throw error; }
      }
      return started;
    };
    const firstClose = globalThis.__kanbienPoolEndCalls ?? 0;
    await server.runKanbienCoreServerPersistenceMain(environment);
    assert.equal(globalThis.__kanbienPoolEndCalls - firstClose, 1, "Actual successful target still closes its pool once.");
    globalThis.__kanbienReadinessFailure = true;
    collector.fail = true; // Real OTLP failure callback must survive a resolved shutdown.
    const secondClose = globalThis.__kanbienPoolEndCalls ?? 0;
    await server.runKanbienCoreServerPersistenceMain({ ...environment, PORT: String(await availablePort()) });
    assert.equal(globalThis.__kanbienPoolEndCalls - secondClose, 1);
    assert.equal(healthRequests, 2);
    assert.equal(observerConstructions, 2); assert.equal(projectionCases, 3);
  } finally { processModule.startPlatformServerProcess = originalStart; readinessModule.createPlatformReadinessObserver = originalObserverFactory; }
} finally {
  fs.readFileSync = originalRead;
  console.log = originalLog;
  console.error = originalError;
  await closeServer(collector.server);
}

assert.equal(globalThis.__kanbienPersistencePoolEnded, true, "Server shutdown must close the target-owned PostgreSQL pool.");
assert.match(output.join("\n"), /platform\.dependency\.readiness_observed/, "The independent observer must emit the allowlisted readiness event on startup.");
assert.equal(output.join("\n").includes("synthetic-test-token"), false, "Readiness output must not expose an authentication token.");
assert.equal(output.join("\n").includes("synthetic-administrator"), false, "Readiness output must not expose a credential fixture.");
assert.equal(output.join("\n").includes("synthetic-readiness-canary"), false, "The failed readiness query must not disclose provider text.");
assert.equal(output.join("\n").includes("synthetic-private-canary"), false, "Neither rejected configuration nor unexpected SDK exceptions may disclose values.");
const records = output.map((line) => JSON.parse(line));
const failedReadiness = records.find((record) => record.fields?.readiness === "not-ready");
assert.equal(failedReadiness.fields.diagnostic_code, "persistence.credential-rejected");
const startupConfiguration = records.filter((record) => record.message === "platform.diagnostic.observed"
  && record.fields?.capability === "platform-server" && record.fields?.operation === "configure" && record.fields?.stage === "configuration");
const choiceCodes = new Set(["platform-server.listener-configuration-selected", "platform-server.port-configuration-fallback",
  "platform-server.health-exposure-selected", "platform-server.health-exposure-fallback"]);
const startupChoices = startupConfiguration.filter((record) => choiceCodes.has(record.fields.diagnostic.code));
const diagnostic = (code, detail) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
const expectedChoices = [
  diagnostic("platform-server.listener-configuration-selected", { phase: "configuration", setting: "http.host", source: "environment", reason: "provided", effect: "selected" }),
  diagnostic("platform-server.listener-configuration-selected", { phase: "configuration", setting: "http.port", source: "environment", reason: "provided", effect: "selected" }),
  diagnostic("platform-server.health-exposure-selected", { phase: "configuration", setting: "http.health.liveness-exposure", source: "default", exposure: "public", reason: "missing", effect: "default-selected" }),
  diagnostic("platform-server.health-exposure-fallback", { phase: "configuration", setting: "http.health.readiness-exposure", source: "default", exposure: "public", reason: "unsupported", effect: "default-selected" }),
];
assert.deepEqual(startupChoices.map((record) => record.fields.diagnostic), [...expectedChoices, ...expectedChoices],
  "Both real starts retain their exact four listener/health choices, including the unsupported readiness fallback.");
const expectedOmissions = [
  diagnostic("platform-server.configuration-omitted", { phase: "configuration", setting: "http.cors-origin", reason: "missing", effect: "omitted" }),
  diagnostic("platform-server.configuration-omitted", { phase: "configuration", setting: "http.cors-allowlist", reason: "missing", effect: "omitted" }),
];
assert.deepEqual(startupConfiguration.filter((record) => record.fields.diagnostic.code === "platform-server.configuration-omitted").map((record) => record.fields.diagnostic), [...expectedOmissions, ...expectedOmissions],
  "Both starts omit absent CORS choices, not their valid supplied release identities.");
assert.equal(output.join("\n").includes("synthetic-private-health-setting"), false);
assert.equal(records.some((record) => record.message === "platform.server.started" && Object.hasOwn(record.fields, "host")), false);
const failure = records.find((record) => record.message === "platform.diagnostic.observed" && record.fields?.diagnostic?.code === "persistence.credential-rejected");
assert.equal(failure.fields.diagnostic.detail.operation, "readiness");
assert.equal(failure.fields.diagnostic.detail.phase, "pool_query");
const healthFailure = records.find((record) => record.message === "platform.diagnostic.observed" && record.fields?.capability === "health" && record.fields?.diagnostic?.code === "persistence.credential-rejected");
assert.deepEqual(healthFailure?.fields.diagnostic, { schema: "core/diagnostic-record/v1", code: "persistence.credential-rejected", definitionVersion: 2,
  detail: { phase: "pool_query", classification: "authentication_rejected", codeStatus: "recognized", operation: "readiness", effect: "not-assessed" } });
assert.ok(records.some((record) => record.fields?.capability === "health" && record.fields?.diagnostic?.code === "health.check-not-ready"), "Actual target /readyz must deliver generic health evidence alongside the preserved dependency record.");
const exportFailures = records.filter((record) => record.message === "platform.diagnostic.observed" && record.fields?.diagnostic?.code === "observability.metric-export-failed");
assert.equal(exportFailures.length, 1, "A failing real exporter must produce one process-owned observation through the default target binding.");
assert.deepEqual(exportFailures[0].fields.diagnostic, { schema: "core/diagnostic-record/v1", code: "observability.metric-export-failed", definitionVersion: 1,
  detail: { phase: "export", reason: "callback-failed", effect: "unknown" } });
assert.equal(exportFailures[0].fields.capability, "observability");
assert.equal(exportFailures[0].fields.operation, "export");
assert.equal(exportFailures[0].fields.stage, "runtime");
assert.equal(records.some((record) => ["observability.metric-flush-failed", "observability.metric-shutdown-failed"].includes(record.fields?.diagnostic?.code)), false,
  "Callback failure must not invent a rejected lifecycle operation or claim delivery.");
assert.equal(collector.requests, 2, "The task-local collector must receive both healthy and failed readiness metrics during controlled shutdown.");
console.log("Core-server persistence observability runtime proof passed.");

async function startCollector() {
  let requests = 0;
  let fail = false;
  const server = createServer((request, response) => {
    if (request.method === "POST" && request.url === "/v1/metrics") requests += 1;
    request.resume();
    response.writeHead(fail ? 400 : 200).end();
  });
  await new Promise((resolvePromise, reject) => server.once("error", reject).listen(4318, "127.0.0.1", resolvePromise));
  return { server, get requests() { return requests; }, set fail(value) { fail = value; } };
}

async function availablePort() {
  const server = createTcpServer();
  await new Promise((resolvePromise, reject) => server.once("error", reject).listen(0, "127.0.0.1", resolvePromise));
  const address = server.address();
  if (typeof address !== "object" || address === null) throw new Error("Local server port was not allocated.");
  await closeServer(server);
  return address.port;
}

async function closeServer(server) {
  await new Promise((resolvePromise, reject) => server.close((error) => error === undefined ? resolvePromise(undefined) : reject(error)));
}
