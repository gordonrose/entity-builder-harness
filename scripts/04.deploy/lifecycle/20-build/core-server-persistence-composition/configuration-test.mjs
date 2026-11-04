#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-persistence-configuration
//   version: 6
//   status: draft
//   created_on: "2026-10-24"
//   updated_on: "2026-11-04"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [security, sre]
//   kind: script
//   purpose: Prove configuration failures stop all persistence entrypoints before pool creation, without database or target access.
//   portability: { class: internal, targets: [] }
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.core-server-persistence-composition
//     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh

import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import { createServer } from "node:net";
import { join, resolve } from "node:path";

import { fixtureRuntime } from "./fixture-runtime.mjs";
const compiled = fixtureRuntime(process.argv[2]);
// No real driver is loaded. Any attempt to create a pool is a test failure.
const fakeDriver = join(compiled, "node_modules/pg");
fs.mkdirSync(fakeDriver, { recursive: true });
fs.writeFileSync(join(fakeDriver, "index.js"), 'exports.Pool = class { constructor(options) { globalThis.poolAttempts += 1; globalThis.lastPoolOptions = options; throw new Error("database-access-before-validation"); } };');
const fakeSigner = join(compiled, "node_modules/@aws-sdk/rds-signer");
fs.mkdirSync(fakeSigner, { recursive: true });
fs.writeFileSync(join(fakeSigner, "index.js"), 'exports.Signer = class { constructor(options) { globalThis.signerOptions.push(options); } async getAuthToken() { globalThis.tokenRequests += 1; return "synthetic-token"; } };');
globalThis.poolAttempts = 0;
globalThis.signerOptions = [];
globalThis.tokenRequests = 0;
let rejectedCases = 0;
const require = createRequire(join(compiled, "configuration-test.cjs"));
const entrypoints = join(compiled, "infra/04.deploy/03.product/entrypoints");
const config = require(join(entrypoints, "kanbien-core-server-persistence-configuration.js"));
const taskDiagnostics = require(join(entrypoints, "kanbien-core-server-persistence-operation-diagnostics.js"));
await privateTaskDiagnosticRegression();
const server = require(join(entrypoints, "kanbien-core-server-persistence.main.js"));
const migration = require(join(entrypoints, "kanbien-core-server-persistence-migration.main.js"));
const administration = require(join(entrypoints, "kanbien-core-server-persistence-administration.main.js"));
const roleCredential = require(join(entrypoints, "kanbien-core-server-persistence-role-credential.js"));
const iamAuthentication = require(join(entrypoints, "kanbien-core-server-persistence-iam-authentication.js"));
const restore = require(join(entrypoints, "kanbien-core-server-persistence-restore-verifier.main.js"));
const valid = {
  PERSISTENCE_POSTGRES_HOST: "postgres", PERSISTENCE_POSTGRES_PORT: "5432",
  PERSISTENCE_POSTGRES_DATABASE: "kanbienpersistence", PERSISTENCE_POSTGRES_SCHEMA: "platform",
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
};

destinationPortConstraintRegression();
configurationReasonSelectionRegression();
await startupDiagnosticContextRegression();
await configurationResponsibilityRegression();
await implementationSelectionRegression();

function configurationReasonSelectionRegression() {
  const core = require(join(compiled, "packages/core/src/config/index.js"));
  const future = "fixture-future-reason";
  const filename = join(entrypoints, "kanbien-core-server-persistence-configuration.js");
  const localRequire = createRequire(filename), fixture = { exports: {} };
  new Function("require", "module", "exports", fs.readFileSync(filename, "utf8"))(
    name => name === "@kanbien/core/config" ? { ...core,
      configReasonNames: Object.freeze({ ...core.configReasonNames, future }),
      configIssueReasons: [...core.configIssueReasons, future],
      configValueIssueReasons: [...core.configValueIssueReasons, future],
    } : localRequire(name), fixture, fixture.exports,
  );
  const published = JSON.parse(fs.readFileSync("infra/04.deploy/03.product/entrypoints/contracts/diagnostics.v1.json", "utf8"));
  assert.deepEqual(config.persistenceTaskConfigurationDiagnosticCatalog, published.catalog);
  assert.deepEqual(fixture.exports.persistenceTaskConfigurationDiagnosticCatalog, published.catalog,
    "using the entire growing vocabulary/list would widen a retained target definition and fail this assertion");
}

async function configurationResponsibilityRegression() {
  const core = require(join(compiled, "packages/core/src/config/index.js"));
  const listener = require(join(compiled, "platform/server/src/configuration/runtime.js"));
  for (const [text, port] of [["0x10", 16], ["1e3", 1000], [" 5432 ", 5432]]) {
    assert.equal(listener.resolvePlatformServerRuntimeConfiguration({ env: { PORT: text } }).port, port,
      "the listener's existing number spellings remain a justified local policy");
    assert.equal(core.validateConfigSettings(core.recordConfigSource({ PORT: text }), [
      { setting: "database.port", source: "PORT", rule: core.destinationPortConstraint },
    ]).ok, false, "collapsing the two parsers must fail their different acceptance assertions");
  }
  assert.equal(listener.resolvePlatformServerRuntimeConfigurationWithDiagnostics({ env: {}, port: 0 }).configuration.port, 0);
  function load(name, replacements) {
    const filename = join(entrypoints, name + ".js"), local = createRequire(filename), fixture = { exports: {} };
    new Function("require", "module", "exports", fs.readFileSync(filename, "utf8"))(
      dependency => Object.hasOwn(replacements, dependency) ? replacements[dependency] : local(dependency), fixture, fixture.exports,
    );
    return fixture.exports;
  }
  const platform = require(join(compiled, "platform/config/src/index.js"));
  const configured = check => load("kanbien-core-server-persistence-configuration", {
    "@kanbien/platform-config": { ...platform, loadPlatformConfiguration(input) {
      const result = check(input.source, input.requirements.map(item => ({ ...item, source: input.bindings[item.setting] })));
      return result.ok ? input.assemble(result.value) : result;
    } },
  });
  let checkedCalls = 0;
  const checked = configured((...args) => {
    checkedCalls++;
    const result = core.validateConfigSettings(...args);
    return result.ok ? { ok: true, value: { ...result.value, "database.port": 5433 } } : result;
  });
  const supplied = { ...valid, UNDECLARED_PRIVATE: "synthetic-unchecked-canary" };
  for (const purpose of ["server", "migration", "restore", "administration"]) {
    const expected = config.persistenceConfigurationResult(supplied, purpose);
    assert.equal(expected.ok, true);
    assert.equal(expected.value.maximumPoolSize, purpose === "server" ? 4 : 1);
    assert.equal(expected.value.connectionTimeoutMs, 5000);
    const unneeded = purpose === "administration" ? "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE" : "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE";
    assert.equal(config.persistenceConfigurationResult({ ...supplied, [unneeded]: undefined }, purpose).ok, true,
      "a requirement conditional on another purpose must not become universally required");
  }
  const result = checked.persistenceConfigurationResult(supplied, "server");
  assert.equal(checkedCalls, 1, "an import without a checker call must fail");
  assert.equal(result.ok, true);
  assert.equal(result.value.port, 5433, "original unchecked input must not replace the checked answer");
  assert.equal(JSON.stringify(result).includes(supplied.UNDECLARED_PRIVATE), false);

  async function runActualCaller(configuration, expectedIssues) {
    let dependentChecks = 0, received;
    const runner = load("kanbien-core-server-persistence.main", {
      "./kanbien-core-server-persistence-configuration": configuration,
      "./kanbien-core-server-persistence-iam-authentication": { ...iamAuthentication,
        persistenceIamAuthenticationResult(env, value, key) {
          dependentChecks++; received = value;
          // Stop this fixture at the next real validator, before any token/pool work.
          return iamAuthentication.persistenceIamAuthenticationResult({ ...env, [key]: undefined }, value, key);
        } },
    });
    const error = console.error, exit = process.exitCode, output = [], pools = globalThis.poolAttempts, tokens = globalThis.tokenRequests;
    try {
      console.error = line => output.push(JSON.parse(line));
      await runner.runKanbienCoreServerPersistenceMain(supplied);
      assert.equal(process.exitCode, 1);
      assert.equal(globalThis.poolAttempts, pools); assert.equal(globalThis.tokenRequests, tokens);
      assert.equal(output.length, 1);
      assert.deepEqual(output[0].diagnostic_context, { capability: "persistence", operation: "startup", stage: "startup" });
      assert.equal(JSON.stringify(output).includes(supplied.UNDECLARED_PRIVATE), false);
      if (expectedIssues) {
        assert.equal(dependentChecks, 0, "ignored failure must not reach dependent authentication");
        assert.equal(output[0].error.code, "configuration-invalid");
        assert.deepEqual(output[0].diagnostic.detail.issues, expectedIssues);
      } else {
        assert.equal(dependentChecks, 1);
        assert.equal(received.port, 5433, "the real caller must pass the checked answer onwards");
      }
    } finally { console.error = error; process.exitCode = exit; }
  }
  await runActualCaller(checked);
  for (const issues of [[{ setting: "database.port", reason: "missing" }],
    [{ setting: "database.host", reason: "missing" }, { setting: "database.port", reason: "out-of-range" }]]) {
    const failed = configured(() => ({ ok: false, error: { code: "CONFIGURATION_INVALID", issues } }));
    await runActualCaller(failed, issues);
  }
  for (const omitted of ["database.host", "database.port", "database.name", "database.schema", "authentication.reference"]) {
    const missing = configured((source, definitions) => core.validateConfigSettings(source, definitions.filter(item => item.setting !== omitted)));
    await runActualCaller(missing, [{ setting: omitted, reason: "missing" }]);
  }
}

function destinationPortConstraintRegression() {
  for (const purpose of ["server", "migration", "restore", "administration"]) {
    for (const port of ["1", "65535"]) {
      const result = config.persistenceConfigurationResult({ ...valid, PERSISTENCE_POSTGRES_PORT: port }, purpose);
      assert.equal(result.ok, true);
      assert.equal(result.value.port, Number(port));
    }
  }
  const filename = join(entrypoints, "kanbien-core-server-persistence-configuration.js");
  const localRequire = createRequire(filename);
  const core = require(join(compiled, "packages/core/src/config/index.js"));
  const narrowed = Object.freeze({ ...core.destinationPortConstraint, minimum: 2, maximum: 65_534 });
  const requirementFile = join(compiled, "platform/adapters/aws/persistence/postgresql/src/configuration/contract/requirements.js");
  const requirementRequire = createRequire(requirementFile), requirements = { exports: {} };
  new Function("require", "module", "exports", fs.readFileSync(requirementFile, "utf8"))(
    name => name === "@kanbien/core/config" ? { ...core, destinationPortConstraint: narrowed } : requirementRequire(name), requirements, requirements.exports,
  );
  const composition = require(join(entrypoints, "kanbien-core-server-persistence-composition.js"));
  const fixture = { exports: {} };
  new Function("require", "module", "exports", fs.readFileSync(filename, "utf8"))(
    name => name === "./kanbien-core-server-persistence-composition" ? { ...composition, selectPersistenceImplementation(value) {
      const selected = composition.selectPersistenceImplementation(value);
      return selected.ok ? { ok: true, value: { ...selected.value, requirements: requirements.exports.postgreSqlPersistenceRequirements } } : selected;
    } } : localRequire(name), fixture, fixture.exports,
  );
  for (const port of ["2", "5432", "65534"]) {
    assert.equal(fixture.exports.persistenceConfigurationResult({ ...valid, PERSISTENCE_POSTGRES_PORT: port }, "server").ok, true);
  }
  for (const port of ["1", "65535"]) {
    const result = fixture.exports.persistenceConfigurationResult({ ...valid, PERSISTENCE_POSTGRES_PORT: port }, "server");
    assert.equal(result.ok, false, "copied target bounds must fail this shared-binding counterexample");
    assert.deepEqual(result.error.diagnostic.detail.issues, [{ setting: "database.port", reason: "out-of-range" }]);
  }
  assert.deepEqual(core.destinationPortConstraint, { kind: "integer", minimum: 1, maximum: 65_535 });
}

async function startupDiagnosticContextRegression() {
  const error = console.error, exit = process.exitCode, attempts = globalThis.poolAttempts;
  const rejected = { ...valid, PERSISTENCE_POSTGRES_PORT: undefined };
  try {
    console.error = () => { throw new Error('synthetic-output-canary'); };
    await server.runKanbienCoreServerPersistenceMain(rejected);
    assert.equal(process.exitCode, 1, 'output failure must preserve startup rejection');
    assert.equal(globalThis.poolAttempts, attempts, 'output failure must never retry dependent work');
  } finally { console.error = error; process.exitCode = exit; }
  const missing = config.persistenceConfigurationResult(rejected, 'server');
  assert.equal(missing.ok, false);
  const evidence = config.persistenceStartupDiagnosticBinding.select(missing.error.diagnostic, { capability: 'wrong', operation: 'wrong', stage: 'runtime' });
  assert.deepEqual(evidence.context, { capability: 'persistence', operation: 'startup', stage: 'startup' }, 'caller cannot override fixed startup attribution');
  assert.equal(config.persistenceStartupDiagnosticBinding.select({ ...missing.error.diagnostic, detail: { issues: [{ setting: 'unregistered.setting', reason: 'missing' }] } }), undefined);
}

async function privateTaskDiagnosticRegression() {
  const { parseDiagnosticRecord } = require(join(compiled, "packages/core/src/diagnostics/index.js"));
  const record = (code, detail) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
  const literals = [
    record("kanbien-core-server.operations.administration-predicate-rejected", { task: "administration", operation: "bounded-role", field: "exists", condition: "false", effect: "predicate-rejected" }),
    record("kanbien-core-server.operations.administration-boundary-failed", { task: "administration", operation: "role-facts", phase: "role-facts-query", condition: "threw", effect: "unknown" }),
    record("kanbien-core-server.operations.verification-predicate-rejected", { task: "verification", operation: "verification", field: "fact", condition: "empty", effect: "predicate-rejected" }),
    record("kanbien-core-server.operations.verification-boundary-failed", { task: "verification", operation: "verification", phase: "fetch", condition: "rejected", effect: "unknown" }),
  ];
  const built = [
    taskDiagnostics.administrationPredicateRecord({ operation: "bounded-role", field: "exists", condition: "false" }),
    taskDiagnostics.administrationBoundaryRecord({ operation: "role-facts", phase: "role-facts-query", effect: "unknown" }),
    taskDiagnostics.verificationPredicateRecord({ operation: "verification", field: "fact", condition: "empty" }),
    taskDiagnostics.verificationBoundaryRecord({ operation: "verification", phase: "fetch", condition: "rejected", effect: "unknown" }),
  ];
  assert.deepEqual(built, literals);
  assert.deepEqual(taskDiagnostics.persistenceTaskOperationDiagnosticCatalog.definitions.map(({ code }) => code), literals.map(({ code }) => code));
  const definitions = taskDiagnostics.persistenceTaskOperationDiagnosticCatalog.definitions;
  for (const value of literals) {
    const definition = definitions.find(({ code }) => code === value.code);
    assert.equal(parseDiagnosticRecord(definition, value).ok, true);
    for (const bad of [{ ...value, definitionVersion: 2 }, { ...value, detail: { ...value.detail, raw: "PRIVATE-canary" } }, { ...value, detail: { ...value.detail, effect: "definitely-rolled-back" } }]) assert.equal(parseDiagnosticRecord(definition, bad).ok, false);
  }
  assert.equal(taskDiagnostics.persistenceTaskFailureContract.schema, "deploy/persistence-task-failure/v1");
  assert.equal(taskDiagnostics.persistenceTaskFailureContract.maxObservations, 8);
  assert.deepEqual(taskDiagnostics.persistenceTaskFailureContract.codes.verification, ["VERIFIER_CONFIGURATION_INVALID", "KANBIEN_CORE_PERSISTENCE_VERIFICATION_REJECTED", "KANBIEN_CORE_PERSISTENCE_VERIFICATION_UNAVAILABLE", "KANBIEN_CORE_PERSISTENCE_HEALTH_VERIFICATION_REJECTED", "KANBIEN_CORE_PERSISTENCE_HEALTH_VERIFICATION_UNAVAILABLE"]);
  const source9 = Array.from({ length: 9 }, (_, ordinal) => record("core.persistence.in-memory-boundary-failed", { operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal }));
  const cause = { diagnosticRecord: source9[0], relatedDiagnosticRecords: source9.slice(1) };
  let receiver;
  const external = { onObservation(own, source) { receiver = this; assert.deepEqual(own, literals[0]); assert.deepEqual([source.diagnosticRecord, ...source.relatedDiagnosticRecords], source9); } };
  const session = new taskDiagnostics.PersistenceTaskObservations("administration", external);
  taskDiagnostics.observePersistenceTask(session.options, built[0], cause);
  assert.equal(receiver, external);
  const envelope = session.failure("PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED");
  assert.deepEqual(envelope, { schema: "deploy/persistence-task-failure/v1", task: "administration", verdict: "rejected", code: "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED", diagnostic: source9[0], related_diagnostics: source9.slice(1), observations: [literals[0]] });
  assert.notEqual(envelope.diagnostic, source9[0], "Source records are validated copies, not caller identity claims.");
  assert.deepEqual(session.failure("PRIVATE-canary").code, "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED");
  assert.equal(taskDiagnostics.persistenceTaskFailureContract.maxSourceBundles, 8);
  assert.equal(taskDiagnostics.persistenceTaskFailureContract.maxOverflowCount, Number.MAX_SAFE_INTEGER);
  const bounded = new taskDiagnostics.PersistenceTaskObservations("administration");
  const bundles = Array.from({ length: 12 }, (_, index) => ({ diagnosticRecord: source9[0], relatedDiagnosticRecords: [...source9.slice(1, 8), { ...source9[8], detail: { ...source9[8].detail, ordinal: index + 8 } }] }));
  for (const bundle of bundles) taskDiagnostics.observePersistenceTask(bounded.options, built[1], bundle);
  taskDiagnostics.observePersistenceTask(bounded.options, built[1], bundles[0]);
  taskDiagnostics.observePersistenceTask(bounded.options, built[1], bundles[11]);
  const overload = bounded.failure("PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED");
  assert.deepEqual([overload.diagnostic, ...overload.related_diagnostics], source9);
  assert.equal(overload.observations.length, 8);
  assert.deepEqual(overload.source_bundles, bundles.slice(1, 9).map((bundle) => ({ diagnostic: bundle.diagnosticRecord, related_diagnostics: bundle.relatedDiagnosticRecords })), "same primary with different companion eight remains distinct");
  assert.deepEqual(overload.overflow, { observations: 6, source_bundles: 4 }, "count each omitted occurrence, not invented distinct causes");
  const accessor = [];
  Object.defineProperty(accessor, "0", { enumerable: true, get() { throw new Error("PRIVATE-canary"); } });
  accessor.length = 1;
  for (const malformed of [accessor, Array(1), Array(9).fill(built[0]), [built[2]], [literals[4]], [{ ...built[0], detail: { ...built[0].detail, raw: "PRIVATE-canary" } }]]) {
    const value = session.envelope("PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED", cause, malformed);
    assert.deepEqual([value.diagnostic, ...value.related_diagnostics], source9);
    assert.deepEqual(value.observations, [], "Invalid own evidence cannot consume or invalidate source9.");
  }
  let sourceGetterReads = 0;
  taskDiagnostics.observePersistenceTask({ onObservation(own, source) { assert.deepEqual(own, literals[0]); assert.deepEqual(source, {}); } }, built[0], { get diagnosticRecord() { sourceGetterReads++; throw new Error("PRIVATE-canary"); } });
  assert.equal(sourceGetterReads, 0);
  const late = new taskDiagnostics.PersistenceTaskObservations("administration");
  late.markPublished();
  const oldError = console.error, oldExit = process.exitCode, emitted = [];
  try {
    process.exitCode = 73;
    console.error = (text) => emitted.push(JSON.parse(text));
    taskDiagnostics.observePersistenceTask(late.options, built[1], cause);
    assert.equal(process.exitCode, 73, "Diagnostic-only cleanup delivery cannot force a process failure.");
    assert.deepEqual(emitted[0], { schema: "deploy/persistence-task-failure/v1", task: "administration", verdict: "rejected", code: "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED", diagnostic: source9[0], related_diagnostics: source9.slice(1), observations: [literals[1]] });
    console.error = () => { throw new Error("PRIVATE-canary"); };
    assert.doesNotThrow(() => taskDiagnostics.observePersistenceTask(late.options, built[1], cause));
    assert.equal(process.exitCode, 73);
  } finally { console.error = oldError; process.exitCode = oldExit; }
  const unhandled = [], sinkError = new Error("PRIVATE-canary"), rejected = Promise.reject(sinkError);
  let shadowReads = 0;
  Object.defineProperty(rejected, "then", { get() { shadowReads++; throw sinkError; } });
  const listener = (reason) => unhandled.push(reason);
  process.on("unhandledRejection", listener);
  try {
    for (const returned of [rejected, { then(_resolve, reject) { reject(sinkError); } }, { then() { throw sinkError; } }]) taskDiagnostics.observePersistenceTask({ onObservation() { return returned; } }, built[0]);
    assert.doesNotThrow(() => taskDiagnostics.observePersistenceTask({ onObservation() { throw sinkError; } }, built[0]));
    await new Promise((resolve) => setImmediate(resolve));
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(shadowReads, 0);
    assert.deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", listener); }
}
for (const [purpose, timeout] of [["server", 5000], ["migration", 240000], ["restore", 30000]]) {
  assert.equal(config.persistenceConfiguration(valid, purpose).statementTimeoutMs, timeout);
}
const certificate = fs.readFileSync("platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt", "utf8");
const originalRead = fs.readFileSync;
let certificateText = certificate;
let certificateReadError;
let reads = 0;
fs.readFileSync = (path, ...args) => {
  if (path === "/app/assets/fixture.crt") { reads += 1; if (certificateReadError !== undefined) throw certificateReadError; return certificateText; }
  throw new Error("unexpected-certificate-path");
};
try {
  assert.equal(config.persistenceCertificateAuthority(valid), certificate);
  const before = reads;
  assert.equal(config.persistenceCertificateAuthority({ ...valid, PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/../outside.crt" }), undefined);
  assert.equal(reads, before, "traversal must fail before filesystem access");
  certificateText = "-----BEGIN CERTIFICATE-----broken-----END CERTIFICATE-----";
  assert.equal(config.persistenceCertificateAuthority(valid), undefined);
  certificateText = certificate;
  await certificateSourceRegression();
  for (const [key, values] of Object.entries({
    PERSISTENCE_POSTGRES_HOST: [undefined, "", " postgres", "https://postgres"],
    PERSISTENCE_POSTGRES_PORT: [undefined, "", "0", "65536", "5432.5", " 5432", "5e3"],
    PERSISTENCE_POSTGRES_DATABASE: [undefined, "", "bad-name"],
    PERSISTENCE_POSTGRES_SCHEMA: [undefined, "", "BadSchema"],
  })) {
    for (const value of values) {
      const env = { ...valid, [key]: value };
      for (const run of [server.runKanbienCoreServerPersistenceMain, migration.runKanbienCoreServerPersistenceMigration, administration.runKanbienCoreServerPersistenceAdministration, restore.runKanbienCoreServerPersistenceRestoreVerifier]) {
        const expected = config.persistenceConfigurationResult(env, run === administration.runKanbienCoreServerPersistenceAdministration ? "administration" : "server");
        assert.equal(expected.ok, false);
        const setting = Object.entries(config.persistenceConfigurationBindings).find(([, source]) => source === key)[0];
        const reason = value === undefined ? "missing" : value === "" ? "blank" : value !== value.trim() ? "surrounding-whitespace"
          : key === "PERSISTENCE_POSTGRES_PORT" ? /^[+-]?\d+$/.test(value) ? "out-of-range" : "invalid-integer" : "invalid-format";
        assert.deepEqual(expected.error.diagnostic.detail.issues, [{ setting, reason }]);
        await rejectedBeforePool(run, env, expected.error.diagnostic);
      }
    }
  }
  const multiple = { ...valid, PERSISTENCE_POSTGRES_HOST: undefined, PERSISTENCE_POSTGRES_PORT: "0", PERSISTENCE_POSTGRES_SCHEMA: "" };
  const multiResult = config.persistenceConfigurationResult(multiple, "server");
  assert.equal(multiResult.ok, false);
  assert.deepEqual(multiResult.error.diagnostic.detail.issues, [
    { setting: "database.host", reason: "missing" }, { setting: "database.port", reason: "out-of-range" }, { setting: "database.schema", reason: "blank" },
  ]);
  for (const run of [server.runKanbienCoreServerPersistenceMain, migration.runKanbienCoreServerPersistenceMigration, administration.runKanbienCoreServerPersistenceAdministration, restore.runKanbienCoreServerPersistenceRestoreVerifier]) await rejectedBeforePool(run, multiple, multiResult.error.diagnostic);
  const formats = { ...valid, PERSISTENCE_POSTGRES_HOST: "https://synthetic-private.example", PERSISTENCE_POSTGRES_PORT: "5e3", PERSISTENCE_POSTGRES_DATABASE: "bad-name", PERSISTENCE_POSTGRES_SCHEMA: "BadSchema" };
  const formatResult = config.persistenceConfigurationResult(formats, "server");
  assert.equal(formatResult.ok, false);
  assert.deepEqual(formatResult.error.diagnostic.detail.issues, [
    { setting: "database.host", reason: "invalid-format" }, { setting: "database.port", reason: "invalid-integer" },
    { setting: "database.name", reason: "invalid-format" }, { setting: "database.schema", reason: "invalid-format" },
  ]);
  for (const run of [server.runKanbienCoreServerPersistenceMain, migration.runKanbienCoreServerPersistenceMigration, administration.runKanbienCoreServerPersistenceAdministration, restore.runKanbienCoreServerPersistenceRestoreVerifier]) await rejectedBeforePool(run, formats, formatResult.error.diagnostic);
  for (const [run, key] of [
    [server.runKanbienCoreServerPersistenceMain, "PERSISTENCE_RUNTIME_DATABASE_USERNAME"],
    [migration.runKanbienCoreServerPersistenceMigration, "PERSISTENCE_MIGRATION_DATABASE_USERNAME"],
    [administration.runKanbienCoreServerPersistenceAdministration, "PERSISTENCE_ADMINISTRATOR_CREDENTIALS"],
    [administration.runKanbienCoreServerPersistenceAdministration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME"],
    [administration.runKanbienCoreServerPersistenceAdministration, "PERSISTENCE_MIGRATION_DATABASE_USERNAME"],
    [restore.runKanbienCoreServerPersistenceRestoreVerifier, "PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME"],
  ]) {
    for (const value of ["", "bad role", "core_runtime\u0000canary"]) {
      await rejectedBeforePool(run, { ...valid, [key]: value });
    }
  }
  await rejectedBeforePool(migration.runKanbienCoreServerPersistenceMigration, { ...valid, PERSISTENCE_MIGRATION_OPERATION: "unknown" });
  await rejectedBeforePool(administration.runKanbienCoreServerPersistenceAdministration, { ...valid, PERSISTENCE_RUNTIME_DATABASE_USERNAME: valid.PERSISTENCE_MIGRATION_DATABASE_USERNAME });
  certificateText = "not-a-certificate";
  for (const run of [server.runKanbienCoreServerPersistenceMain, migration.runKanbienCoreServerPersistenceMigration, administration.runKanbienCoreServerPersistenceAdministration, restore.runKanbienCoreServerPersistenceRestoreVerifier]) await rejectedBeforePool(run, valid);
  certificateText = certificate;
  await roleCredentialRegression();
  await maintenanceInstructionsRegression();
  await operationProducerRegression();
  await migrationCleanupRegression();
  await iamConfigurationRegression();
  await iamAuthenticationRegression();
  await administratorCredentialRegression();
  await administrationConfigurationRegression();
  administrationDiagnosticRegression();
  restoreDiagnosticRegression();
  await restoreTransportProbeRegression();
  targetTemplateRegression();
  assert.equal(globalThis.poolAttempts, 0);
  console.log(`Persistence configuration regression passed (${rejectedCases} entrypoint failures before pool creation; migration deadline and TLS authority validated).`);
} finally { fs.readFileSync = originalRead; }

async function maintenanceInstructionsRegression() {
  const net = require("node:net"), tls = require("node:tls");
  const originalTcp = net.connect, originalTls = tls.connect;
  let probes = 0;
  net.connect = tls.connect = () => { probes++; throw new Error("N03-rejected-instruction-started-probe"); };
  const record = (code, issues) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail: { issues } });
  try {
    for (const [value, reason] of [[false, "wrong-type"], ["", "blank"], [" apply ", "surrounding-whitespace"], ["synthetic-N03-private", "unsupported-value"]]) {
      await rejectedBeforePool(migration.runKanbienCoreServerPersistenceMigration, { ...valid, PERSISTENCE_MIGRATION_OPERATION: value },
        record("persistence.migration-instructions-invalid", [{ setting: "migration.operation", reason }]), "PERSISTENCE_MIGRATION_CONFIGURATION_INVALID");
    }
    await rejectedBeforePool(restore.runKanbienCoreServerPersistenceRestoreVerifier, { ...valid, PERSISTENCE_RESTORE_DIAGNOSTIC_MODE: "synthetic-N03-private", PERSISTENCE_ACCEPTANCE_RECORD_ID: undefined },
      record("persistence.verification-instructions-invalid", [{ setting: "verification.mode", reason: "unsupported-value" }]), "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID");
    for (const [key, setting] of [["PERSISTENCE_ACCEPTANCE_RECORD_ID", "verification.expected-record-id"], ["PERSISTENCE_ACCEPTANCE_FACT_DIGEST", "verification.expected-fingerprint"]]) {
      for (const [value, reason] of [[undefined, "missing"], [false, "wrong-type"], [" \t", "blank"], [" value ", "surrounding-whitespace"], ["synthetic-N03-private", "invalid-format"]]) {
        await rejectedBeforePool(restore.runKanbienCoreServerPersistenceRestoreVerifier, { ...valid, [key]: value },
          record("persistence.verification-instructions-invalid", [{ setting, reason }]), "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID");
      }
    }
    await rejectedBeforePool(restore.runKanbienCoreServerPersistenceRestoreVerifier, { ...valid, PERSISTENCE_ACCEPTANCE_RECORD_ID: undefined, PERSISTENCE_ACCEPTANCE_FACT_DIGEST: "bad" },
      record("persistence.verification-instructions-invalid", [{ setting: "verification.expected-record-id", reason: "missing" }, { setting: "verification.expected-fingerprint", reason: "invalid-format" }]));
    assert.equal(probes, 0, "all control failures must stop before TCP or TLS probes");
    for (const key of ["PERSISTENCE_MIGRATION_OPERATION", "PERSISTENCE_RESTORE_DIAGNOSTIC_MODE", "PERSISTENCE_ACCEPTANCE_RECORD_ID", "PERSISTENCE_ACCEPTANCE_FACT_DIGEST"]) {
      const cause = Object.freeze(new Error("synthetic-N03-source-private"));
      const env = Object.defineProperty({ ...valid }, key, { enumerable: true, get() { throw cause; } });
      await assert.rejects(() => key === "PERSISTENCE_MIGRATION_OPERATION" ? migration.runKanbienCoreServerPersistenceMigration(env) : restore.runKanbienCoreServerPersistenceRestoreVerifier(env), error => error === cause);
    }
  } finally { net.connect = originalTcp; tls.connect = originalTls; }
  const fields = config.persistenceTaskDiagnosticFields(record("persistence.verification-instructions-invalid", [{ setting: "verification.mode", reason: "unsupported-value" }]));
  assert.deepEqual(fields, { diagnostic: record("persistence.verification-instructions-invalid", [{ setting: "verification.mode", reason: "unsupported-value" }]) });
  assert.deepEqual(config.persistenceTaskDiagnosticFields(record("persistence.verification-instructions-invalid", [{ setting: "PERSISTENCE_RESTORE_DIAGNOSTIC_MODE", reason: "unsupported-value" }])), {});
  assert.deepEqual(config.persistenceTaskDiagnosticFields(record("persistence.migration-instructions-invalid", [{ setting: "migration.operation", reason: "missing" }])), {});
}

async function certificateSourceRegression() {
  const runs = [server.runKanbienCoreServerPersistenceMain, migration.runKanbienCoreServerPersistenceMigration, administration.runKanbienCoreServerPersistenceAdministration, restore.runKanbienCoreServerPersistenceRestoreVerifier];
  for (const [value, reason] of [[undefined, "missing"], [null, "wrong-type"], ["", "blank"], [" \t", "blank"], [" /app/assets/fixture.crt", "surrounding-whitespace"],
    ["/private/synthetic-secret-canary.crt", "location-not-allowed"], ["/app/assets/../fixture.crt", "path-not-normalized"], ["/app/assets/fixture.pem", "extension-not-allowed"]]) {
    const env = { ...valid, PERSISTENCE_POSTGRES_CA_PATH: value };
    const before = reads;
    const result = config.persistenceCertificateAuthorityResult(env);
    assert.equal(result.ok, false);
    assert.deepEqual(result.error.diagnostic.detail, { source: "database.tls.authority-source", reason, phase: "configuration-source-validation", effect: "not-started" });
    for (const run of runs) await rejectedBeforePool(run, env, result.error.diagnostic);
    assert.equal(reads, before, "source policy rejection must not read files");
  }
  for (const [code, reason] of [["ENOENT", "not-found"], ["EACCES", "read-denied"], ["EPERM", "read-denied"], ["ENOTDIR", "not-a-directory"], ["EISDIR", "is-a-directory"], ["synthetic-secret-canary", "unclassified-read-failure"], [undefined, "unclassified-read-failure"]]) {
    certificateReadError = { code, message: "private-path synthetic-secret-canary" };
    const result = config.persistenceCertificateAuthorityResult(valid);
    assert.equal(result.ok, false);
    assert.equal(result.error.diagnostic.detail.reason, reason);
    assert.equal(JSON.stringify(result).includes("canary"), false);
    for (const run of runs) await rejectedBeforePool(run, valid, result.error.diagnostic);
  }
  certificateReadError = Object.defineProperty({}, "code", { get() { throw new Error("synthetic-secret-canary"); } });
  assert.equal(config.persistenceCertificateAuthorityResult(valid).error.diagnostic.detail.reason, "unclassified-read-failure");
  certificateReadError = undefined;
  for (const content of ["synthetic-secret-canary", "-----BEGIN CERTIFICATE-----synthetic-secret-canary-----END CERTIFICATE-----"]) {
    certificateText = content;
    const result = config.persistenceCertificateAuthorityResult(valid);
    assert.equal(result.ok, false);
    assert.equal(result.error.diagnostic.code.startsWith("security."), true);
    assert.equal(JSON.stringify(result).includes("canary"), false);
    for (const run of runs) await rejectedBeforePool(run, valid, result.error.diagnostic);
  }
  certificateText = `${certificate}\n-----BEGIN CERTIFICATE-----`;
  assert.equal(config.persistenceCertificateAuthorityResult(valid).ok, true, "loader remains explicitly compatible until strict marker policy is approved");
  certificateText = certificate;
  assert.deepEqual(config.persistenceTaskDiagnosticFields(Object.defineProperty({}, "code", { get() { throw new Error("synthetic-secret-canary"); } })), {});
}

function administrationDiagnosticRegression() {
  for (const code of [
    "PERSISTENCE_RUNTIME_DML_NOT_CONFIRMED",
    "PERSISTENCE_RUNTIME_PERMISSION_DENIAL_NOT_CONFIRMED",
    "PERSISTENCE_RUNTIME_PERMISSION_UNEXPECTEDLY_PERMITTED",
    "PERSISTENCE_RUNTIME_ADMINISTRATION_UNEXPECTEDLY_PERMITTED",
  ]) assert.equal(administration.administrationFailureCode(new Error(code)), code, "closed privilege-probe outcome must remain diagnostically distinct");
  assert.equal(administration.administrationFailureCode(new Error("password=synthetic-canary")), "PERSISTENCE_ADMINISTRATION_NOT_CONFIRMED", "unexpected provider detail must not enter a diagnostic code");
}

function restoreDiagnosticRegression() {
  for (const [providerCode, diagnostic] of [
    ["28P01", "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED"],
    ["42501", "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED"],
    ["42P01", "KANBIEN_CORE_PERSISTENCE_RESTORE_CONTENT_UNAVAILABLE"],
    ["ETIMEDOUT", "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE"],
    ["ENETUNREACH", "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE"],
    ["ERR_TLS_CERT_ALTNAME_INVALID", "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID"],
  ]) assert.equal(restore.restoreVerificationFailureCode({ code: providerCode }), diagnostic);
  assert.equal(restore.restoreVerificationFailureCode(new Error("SASL: SCRAM-SERVER-FIRST-MESSAGE: client password must be a string")), "KANBIEN_CORE_PERSISTENCE_RESTORE_IAM_TOKEN_MATERIAL_INVALID", "the one fixed node-postgres token-material invariant has its own closed remediation code");
  assert.equal(restore.restoreVerificationFailureCode(new Error("SASL: unexpected password=synthetic-canary")), "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE", "nearby provider detail must not become an allowlisted diagnostic");
  assert.equal(restore.restoreVerificationFailureCode({ cause: { code: "UNABLE_TO_VERIFY_LEAF_SIGNATURE" }, message: "password=synthetic-canary" }), "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID", "only an allowlisted causal machine code may cross the diagnostic boundary");
  assert.equal(restore.restoreVerificationFailureCode({ errors: [{ code: "28P01", message: "password=synthetic-canary" }] }), "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED", "an allowlisted nested PostgreSQL code may cross the boundary without its message");
  assert.equal(restore.restoreVerificationFailureCode({ errors: [{ errors: [{ code: "42501", message: "password=synthetic-canary" }] }] }), "KANBIEN_CORE_PERSISTENCE_RESTORE_PERMISSION_DENIED", "bounded aggregate traversal retains only allowlisted machine codes");
  assert.equal(restore.restoreVerificationFailureCode(new Error("password=synthetic-canary")), "KANBIEN_CORE_PERSISTENCE_RESTORE_VERIFICATION_UNAVAILABLE", "raw provider detail must never become a diagnostic code");
  assert.equal(restore.restoreConnectionFailureCode(new Error("password=synthetic-canary")), "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE", "an opaque connection failure must remain closed but distinguish the failed boundary");
  assert.equal(restore.restoreTransportFailureCode(new Error("password=synthetic-canary")), "KANBIEN_CORE_PERSISTENCE_RESTORE_TRANSPORT_UNAVAILABLE", "an opaque preflight failure must remain a closed transport result");
  assert.equal(restore.restoreTlsPreflightFailureCode(new Error("password=synthetic-canary")), "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_NEGOTIATION_UNAVAILABLE", "an opaque TLS preflight failure must remain a closed TLS result");
  assert.equal(restore.restoreTlsPreflightFailureCode({ code: "UNABLE_TO_VERIFY_LEAF_SIGNATURE", message: "password=synthetic-canary" }), "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID", "an allowlisted TLS code preserves trust-specific remediation without provider detail");
  assert.equal(restore.restorePostTransportConnectionFailureCode(new Error("password=synthetic-canary")), "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE", "a separate successful probe cannot establish an internal stage of the driver connection");
  assert.equal(restore.restoreTransportFailureCode({ code: "ETIMEDOUT", message: "password=synthetic-canary" }), "KANBIEN_CORE_PERSISTENCE_RESTORE_CONNECTION_UNAVAILABLE", "allowlisted transport machine codes preserve the established closed category");
  assert.equal(restore.restoreQueryFailureCode(new Error("password=synthetic-canary")), "KANBIEN_CORE_PERSISTENCE_RESTORE_QUERY_UNAVAILABLE", "an opaque query failure must remain closed but distinguish the failed boundary");
  assert.equal(restore.restoreConnectionFailureCode({ code: "28P01", message: "password=synthetic-canary" }), "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED", "an allowlisted connection error must preserve its safe classification");
  assert.equal(restore.restoreQueryFailureCode({ code: "42P01", message: "password=synthetic-canary" }), "KANBIEN_CORE_PERSISTENCE_RESTORE_CONTENT_UNAVAILABLE", "an allowlisted query error must preserve its safe classification");
}

async function restoreTransportProbeRegression() {
  const server = createServer((socket) => socket.destroy());
  await new Promise((resolve, reject) => server.listen(0, "127.0.0.1", (error) => error === undefined ? resolve(undefined) : reject(error)));
  const address = server.address();
  assert.equal(typeof address, "object", "fixture transport listener must expose a bound port");
  if (typeof address !== "object" || address === null) throw new Error("transport-listener-unavailable");
  try {
    await restore.probePostgreSqlTransport("127.0.0.1", address.port, 100);
  } finally {
    await new Promise((resolve, reject) => server.close((error) => error === undefined ? resolve(undefined) : reject(error)));
  }
  // Once the listener has gone away, the same local port is a deterministic
  // closed-path fixture. An open-but-idle listener is *not* a transport
  // failure—it correctly proves TCP reachability and leaves PostgreSQL/TLS to
  // the next bounded phase.
  await assert.rejects(() => restore.probePostgreSqlTransport("127.0.0.1", address.port, 100), "a closed private port must reject before the verifier constructs a PostgreSQL pool");
}

async function rejectedBeforePool(run, env, expectedDiagnostic, expectedCode) {
  const savedError = console.error, savedCode = process.exitCode;
  const errors = [];
  const signerCount = globalThis.signerOptions.length, tokenCount = globalThis.tokenRequests;
  console.error = (value) => errors.push(String(value));
  process.exitCode = undefined;
  try {
    await run(env);
    assert.equal(process.exitCode, 1, "invalid input must fail closed");
    assert.equal(globalThis.poolAttempts, 0, "invalid input must not construct a driver pool");
    assert.equal(globalThis.tokenRequests, tokenCount, "rejected configuration must not materialize a token");
    if (expectedDiagnostic?.code === "kanbien-core-server.iam-configuration-invalid" || expectedDiagnostic?.code === "kanbien-core-server.administrator-credentials-invalid") {
      assert.equal(globalThis.signerOptions.length, signerCount, "invalid IAM input must not create an IAM signer");
      assert.equal(globalThis.tokenRequests, tokenCount, "invalid IAM input must not request an IAM token");
    }
    rejectedCases += 1;
    const diagnostics = errors.join("\n");
    assert.match(diagnostics, /configuration-invalid|iam-authentication-invalid|credentials-invalid|CONFIGURATION_INVALID|tls-authority-unavailable|ADMINISTRATION_CONFIGURATION_INVALID|PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED/);
    assert.equal(diagnostics.includes("synthetic"), false, "diagnostics must not include credential values");
    const records = errors.map((line) => JSON.parse(line));
    const record = records.find((item) => item.diagnostic !== undefined) ?? records[0];
    if (run === server.runKanbienCoreServerPersistenceMain && record.diagnostic !== undefined) {
      assert.deepEqual(record.diagnostic_context, { capability: 'persistence', operation: 'startup', stage: 'startup' }, 'actual setting and sourcing failures retain the bound startup context');
    }
    if (expectedCode !== undefined) assert.equal(record.code ?? record.error?.code, expectedCode, "existing failure code must remain stable");
    if (expectedDiagnostic !== undefined) {
      assert.deepEqual(records.find((record) => record.diagnostic !== undefined)?.diagnostic, expectedDiagnostic, "exact safe detail must survive the entrypoint's existing failure envelope");
      for (const key of Object.values(config.persistenceConfigurationBindings)) {
        if (typeof env[key] === "string" && env[key].length > 10) assert.equal(diagnostics.includes(env[key]), false, "input values must not enter diagnostics");
      }
    }
  } finally { console.error = savedError; process.exitCode = savedCode; }
}

async function administratorCredentialRegression() {
  const outer = (reason) => [{ setting: "administrator.credentials", reason }];
  const field = (name, reason) => [{ setting: `administrator.${name}`, reason }];
  const cases = [
    [undefined, outer("missing")], [null, outer("wrong-type")], [42, outer("wrong-type")], [{}, outer("wrong-type")],
    ["", outer("blank")], [" \n\t", outer("blank")], ['{"synthetic-private-json":', outer("invalid-json")],
    ['"synthetic-private-json"', outer("wrong-shape")], ["null", outer("wrong-shape")], ["[]", outer("wrong-shape")], ["true", outer("wrong-shape")], ["42", outer("wrong-shape")],
    ["{}", [...field("username", "missing"), ...field("password", "missing")]],
  ];
  for (const [name, variants] of Object.entries({
    username: [[undefined, "missing"], [null, "wrong-type"], [[], "wrong-type"], [{}, "wrong-type"], [42, "wrong-type"], ["", "blank"], [" \t", "blank"], [" synthetic_user", "surrounding-whitespace"], ["synthetic_user\n", "surrounding-whitespace"], ["synthetic-user", "invalid-format"], ["_".repeat(64), "invalid-format"]],
    password: [[undefined, "missing"], [null, "wrong-type"], [[], "wrong-type"], [{}, "wrong-type"], [42, "wrong-type"], ["", "empty"], ["synthetic-private\u0000password", "forbidden-character"]],
  })) for (const [value, reason] of variants) cases.push([JSON.stringify({ username: "synthetic_admin", password: "synthetic-private-password", [name]: value }), field(name, reason)]);
  cases.push([JSON.stringify({ username: "synthetic-admin!", password: "synthetic-private\u0000password" }), [...field("username", "invalid-format"), ...field("password", "forbidden-character")]]);
  for (const [value, issues] of cases) {
    const expected = config.persistenceCredentialsResult(value);
    assert.equal(expected.ok, false);
    assert.equal(expected.error.diagnostic.code, "kanbien-core-server.administrator-credentials-invalid");
    assert.deepEqual(expected.error.diagnostic.detail.issues, issues);
    assert.equal(config.persistenceCredentials(value), undefined, "compatibility parser delegates to the same rejection");
    const serialized = JSON.stringify(expected.error.diagnostic);
    for (const canary of ["synthetic", "PERSISTENCE_ADMINISTRATOR_CREDENTIALS", "SyntaxError", "JSON.parse"]) assert.equal(serialized.includes(canary), false);
    for (const operation of [undefined, "bootstrap-identities", "grant-runtime-application-access", "confirm-runtime-iam-access", "revoke-runtime", "restore-runtime", "prove-effective-privilege", "observe-migration-state"]) {
      await rejectedBeforePool(administration.runKanbienCoreServerPersistenceAdministration,
        { ...valid, PERSISTENCE_ADMINISTRATOR_CREDENTIALS: value, PERSISTENCE_ADMINISTRATION_OPERATION: operation }, expected.error.diagnostic, "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID");
    }
  }
  const signers = globalThis.signerOptions.length, tokens = globalThis.tokenRequests;
  for (const username of ["_", "_".repeat(63), "core_administrator"]) for (const password of [" ", "\t\n", " synthetic password ", "päss😀", "x".repeat(10000)]) {
    const value = ` \n${JSON.stringify({ username, password, extra: { ignored: "synthetic-private" } })}\t `;
    const expected = { username, password };
    assert.deepEqual(config.persistenceCredentialsResult(value), { ok: true, value: expected });
    assert.deepEqual(config.persistenceCredentials(value), expected, "valid compatibility result preserves exact contents and ignores extra fields");
    await assert.rejects(() => administration.runKanbienCoreServerPersistenceAdministration({ ...valid, PERSISTENCE_ADMINISTRATOR_CREDENTIALS: value }), /database-access-before-validation/, "valid credentials must reach the original connection boundary");
    assert.equal(globalThis.poolAttempts, 1);
    assert.equal(globalThis.lastPoolOptions.user, username, "the driver receives the original username");
    assert.equal(globalThis.lastPoolOptions.password, password, "the driver receives the exact password without trimming or rewriting");
    globalThis.poolAttempts = 0;
  }
  assert.equal(globalThis.signerOptions.length, signers, "administrator-only valid credentials do not construct IAM signers");
  assert.equal(globalThis.tokenRequests, tokens, "credential parsing never requests tokens");
}

async function administrationConfigurationRegression() {
  const run = administration.runKanbienCoreServerPersistenceAdministration;
  const administrator = "core_administrator";
  const relation = (relationship) => ({ relationship, rule: "must-differ" });
  const pairNames = ["administrator-migration-separation", "administrator-runtime-separation", "migration-runtime-separation"];
  async function expect(env, detail, suffix) {
    const expected = { schema: "core/diagnostic-record/v1", code: `kanbien-core-server.administration-configuration-invalid.${suffix}`, definitionVersion: 1, detail };
    const checked = config.persistenceAdministrationConfigurationResult(env, administrator);
    assert.equal(checked.ok, false);
    assert.deepEqual(checked.error.diagnostic, expected);
    const signers = globalThis.signerOptions.length;
    await rejectedBeforePool(run, env, expected, "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID");
    assert.equal(globalThis.signerOptions.length, signers, "rejected administration preflight must not construct a signer");
    for (const canary of ["synthetic", administrator, "core_runtime", "core_schema_migration", "PERSISTENCE_"]) assert.equal(JSON.stringify(expected).includes(canary), false);
  }
  for (const [setting, key] of [["migration.username", "PERSISTENCE_MIGRATION_DATABASE_USERNAME"], ["runtime.username", "PERSISTENCE_RUNTIME_DATABASE_USERNAME"], ["administration.operation", "PERSISTENCE_ADMINISTRATION_OPERATION"]]) {
    const cases = [[null, "wrong-type"], [42, "wrong-type"], [{ secret: "synthetic" }, "wrong-type"], ["", "blank"], [" \t", "blank"], [" synthetic", "surrounding-whitespace"], ["synthetic ", "surrounding-whitespace"], ["synthetic!", "invalid-format"], ["_".repeat(64), "invalid-format"]];
    if (setting !== "administration.operation") cases.unshift([undefined, "missing"]);
    for (const [value, reason] of cases) await expect({ ...valid, [key]: value }, { issues: [{ setting, reason }] }, "fields");
  }
  for (const [overrides, pair] of [
    [{ PERSISTENCE_MIGRATION_DATABASE_USERNAME: administrator }, pairNames[0]],
    [{ PERSISTENCE_RUNTIME_DATABASE_USERNAME: administrator }, pairNames[1]],
    [{ PERSISTENCE_RUNTIME_DATABASE_USERNAME: valid.PERSISTENCE_MIGRATION_DATABASE_USERNAME }, pairNames[2]],
  ]) await expect({ ...valid, ...overrides }, { relationshipIssues: [relation(pair)] }, "relationships");
  await expect({ ...valid, PERSISTENCE_RUNTIME_DATABASE_USERNAME: administrator, PERSISTENCE_MIGRATION_DATABASE_USERNAME: administrator },
    { relationshipIssues: pairNames.map(relation) }, "relationships");
  await expect({ ...valid, PERSISTENCE_RUNTIME_DATABASE_USERNAME: administrator, PERSISTENCE_MIGRATION_DATABASE_USERNAME: "synthetic!", PERSISTENCE_ADMINISTRATION_OPERATION: "synthetic!" }, {
    issues: [{ setting: "migration.username", reason: "invalid-format" }, { setting: "administration.operation", reason: "invalid-format" }],
    relationshipIssues: [relation(pairNames[1])],
  }, "fields-and-relationships");
  await expect({ ...valid, PERSISTENCE_RUNTIME_DATABASE_USERNAME: "synthetic!", PERSISTENCE_MIGRATION_DATABASE_USERNAME: "synthetic!", PERSISTENCE_ADMINISTRATION_OPERATION: "synthetic!" }, {
    issues: [{ setting: "migration.username", reason: "invalid-format" }, { setting: "runtime.username", reason: "invalid-format" }, { setting: "administration.operation", reason: "invalid-format" }],
  }, "fields");
  await expect({ ...valid, PERSISTENCE_RUNTIME_DATABASE_USERNAME: undefined, PERSISTENCE_MIGRATION_DATABASE_USERNAME: undefined }, {
    issues: [{ setting: "migration.username", reason: "missing" }, { setting: "runtime.username", reason: "missing" }],
  }, "fields");
  for (const operation of [undefined, ...config.persistenceAdministrationOperations]) {
    const checked = config.persistenceAdministrationConfigurationResult({ ...valid, PERSISTENCE_ADMINISTRATION_OPERATION: operation }, administrator);
    assert.deepEqual(checked, { ok: true, value: { migration: { username: valid.PERSISTENCE_MIGRATION_DATABASE_USERNAME }, runtime: { username: valid.PERSISTENCE_RUNTIME_DATABASE_USERNAME }, operation: operation ?? "bootstrap-identities" } });
  }
  for (const key of ["PERSISTENCE_MIGRATION_DATABASE_USERNAME", "PERSISTENCE_RUNTIME_DATABASE_USERNAME"]) for (const username of ["_", "_".repeat(63)]) {
    assert.equal(config.persistenceAdministrationConfigurationResult({ ...valid, [key]: username }, administrator).ok, true);
    await assert.rejects(() => run({ ...valid, [key]: username }), /database-access-before-validation/);
    assert.equal(globalThis.poolAttempts, 1);
    globalThis.poolAttempts = 0;
  }
  // Keep the old single-primary precedence; do not repurpose TLS companions.
  const prove = { ...valid, PERSISTENCE_ADMINISTRATION_OPERATION: "prove-effective-privilege", PERSISTENCE_POSTGRES_IAM_REGION: undefined };
  await expect({ ...prove, PERSISTENCE_MIGRATION_DATABASE_USERNAME: "synthetic!" }, { issues: [{ setting: "migration.username", reason: "invalid-format" }] }, "fields");
  await expect({ ...prove, PERSISTENCE_RUNTIME_DATABASE_USERNAME: administrator }, { relationshipIssues: [relation(pairNames[1])] }, "relationships");
  certificateText = "synthetic-not-a-certificate";
  try {
    const certificateFailure = config.persistenceCertificateAuthorityResult(valid).error.diagnostic;
    await rejectedBeforePool(run, { ...prove, PERSISTENCE_MIGRATION_DATABASE_USERNAME: "synthetic!" }, certificateFailure, "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID");
    await rejectedBeforePool(run, { ...valid, PERSISTENCE_ADMINISTRATION_OPERATION: "synthetic!" }, certificateFailure, "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID");
    const badRuntime = { ...prove, PERSISTENCE_RUNTIME_DATABASE_USERNAME: "synthetic!", PERSISTENCE_MIGRATION_DATABASE_USERNAME: "synthetic!" };
    const iamFailure = iamAuthentication.persistenceIamAuthenticationResult(badRuntime, config.persistenceConfiguration(valid, "server"), "PERSISTENCE_RUNTIME_DATABASE_USERNAME").error.diagnostic;
    await rejectedBeforePool(run, badRuntime, iamFailure, "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID");
  } finally { certificateText = certificate; }
}

async function iamConfigurationRegression() {
  const configuration = config.persistenceConfiguration(valid, "server");
  const callers = [
    [server.runKanbienCoreServerPersistenceMain, "PERSISTENCE_RUNTIME_DATABASE_USERNAME", {}, "runtime-iam-authentication-invalid"],
    [migration.runKanbienCoreServerPersistenceMigration, "PERSISTENCE_MIGRATION_DATABASE_USERNAME", {}, "PERSISTENCE_MIGRATION_CONFIGURATION_INVALID"],
    [restore.runKanbienCoreServerPersistenceRestoreVerifier, "PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME", {}, "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID"],
    [restore.runKanbienCoreServerPersistenceRestoreVerifier, "PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME", { PERSISTENCE_RESTORE_DIAGNOSTIC_MODE: "connection" }, "PERSISTENCE_RESTORE_VERIFICATION_CONFIGURATION_INVALID"],
    [administration.runKanbienCoreServerPersistenceAdministration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME", { PERSISTENCE_ADMINISTRATION_OPERATION: "prove-effective-privilege" }, "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID"],
  ];
  const cases = [[undefined, "missing"], ["", "blank"], [" \t", "blank"], [" leading-canary", "surrounding-whitespace"],
    ["trailing-canary ", "surrounding-whitespace"], [42, "wrong-type"], [null, "wrong-type"], [{ canary: "synthetic-private" }, "wrong-type"], ["synthetic-private!", "invalid-format"]];
  for (const [run, usernameKey, overrides, existingCode] of callers) {
    for (const [setting, source] of [["authentication.username", usernameKey], ["authentication.region", "PERSISTENCE_POSTGRES_IAM_REGION"]]) {
      for (const [value, reason] of cases) {
        const env = { ...valid, ...overrides, [source]: value };
        const expected = iamAuthentication.persistenceIamAuthenticationResult(env, configuration, usernameKey);
        assert.equal(expected.ok, false);
        assert.equal(expected.error.diagnostic.code, "kanbien-core-server.iam-configuration-invalid");
        assert.deepEqual(expected.error.diagnostic.detail.issues, [{ setting, reason }]);
        const code = run === administration.runKanbienCoreServerPersistenceAdministration && setting === "authentication.region"
          ? "PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED" : existingCode;
        await rejectedBeforePool(run, env, expected.error.diagnostic, code);
        assert.equal(iamAuthentication.persistenceIamAuthentication(env, configuration, usernameKey), undefined, "compatibility reader retains failure shape");
      }
    }
    const env = { ...valid, ...overrides, [usernameKey]: "synthetic-private!", PERSISTENCE_POSTGRES_IAM_REGION: undefined };
    const expected = iamAuthentication.persistenceIamAuthenticationResult(env, configuration, usernameKey);
    assert.equal(expected.ok, false);
    assert.deepEqual(expected.error.diagnostic.detail.issues, [
      { setting: "authentication.username", reason: "invalid-format" }, { setting: "authentication.region", reason: "missing" },
    ]);
    await rejectedBeforePool(run, env, expected.error.diagnostic, existingCode);
    const serialized = JSON.stringify(expected.error.diagnostic);
    assert.equal(serialized.includes("synthetic-private"), false);
    assert.equal(serialized.includes(usernameKey), false, "binding keys stay in target composition, not diagnostic values");
  }
  // These operations never authenticate as the runtime user. Missing region
  // must reach the original administrator-only pool boundary, not reject IAM.
  const signerCount = globalThis.signerOptions.length;
  await rejectedBeforePool(administration.runKanbienCoreServerPersistenceAdministration,
    { ...valid, PERSISTENCE_ADMINISTRATION_OPERATION: "prove-effective-privilege", PERSISTENCE_ADMINISTRATOR_CREDENTIALS: undefined, PERSISTENCE_POSTGRES_IAM_REGION: "synthetic-private!" },
    undefined, "PERSISTENCE_ADMINISTRATION_CONFIGURATION_INVALID");
  assert.equal(globalThis.signerOptions.length, signerCount, "unrelated invalid administration prerequisites keep their original priority before signer creation");
  for (const operation of [undefined, "bootstrap-identities", "grant-runtime-application-access", "confirm-runtime-iam-access", "revoke-runtime", "restore-runtime", "observe-migration-state"]) {
    await assert.rejects(() => administration.runKanbienCoreServerPersistenceAdministration({ ...valid, PERSISTENCE_POSTGRES_IAM_REGION: undefined, PERSISTENCE_ADMINISTRATION_OPERATION: operation }), /database-access-before-validation/);
    assert.equal(globalThis.poolAttempts, 1);
    globalThis.poolAttempts = 0;
    assert.equal(globalThis.signerOptions.length, signerCount, "administrator-only operations must not construct an IAM signer");
  }
}

async function roleCredentialRegression() {
  const absent = { exists: false, can_login: false, superuser: false, create_role: false, create_database: false, replication: false, bypass_rls: false, inherit: false };
  const bounded = { ...absent, exists: true, can_login: true };
  const statements = [];
  const pool = { query: async (statement) => {
    statements.push(statement);
    const text = statement.text;
    if (text.startsWith("SELECT EXISTS")) return { rows: [statements.filter((item) => item.text.startsWith("SELECT EXISTS")).length === 1 ? absent : bounded] };
    return { rows: [] };
  } };
  await roleCredential.ensureBoundedLoginRole(pool, { username: "core_runtime" });
  const ddl = statements.map((statement) => statement.text).join("\n");
  assert.equal(ddl.includes("PASSWORD"), false, "role identity DDL must not carry a credential or verifier");
  assert.equal(ddl.includes("SCRAM-SHA-256"), false, "a verifier is sensitive credential material too");
  const inheritedStatements = [];
  const inherited = { ...bounded, inherit: true };
  const inheritedPool = { query: async (statement) => {
    inheritedStatements.push(statement);
    if (statement.text.startsWith("SELECT EXISTS")) return { rows: [inheritedStatements.filter((item) => item.text.startsWith("SELECT EXISTS")).length === 1 ? inherited : bounded] };
    return { rows: [] };
  } };
  await roleCredential.ensureBoundedLoginRole(inheritedPool, { username: "core_runtime" });
  assert.equal(inheritedStatements.some((statement) => statement.text === 'ALTER ROLE "core_runtime" NOINHERIT'), true, "a non-elevated legacy role must converge to the bounded IAM identity profile");
  await assert.rejects(
    () => roleCredential.ensureBoundedLoginRole({ query: async () => ({ rows: [{ ...bounded, can_login: false }] }) }, { username: "core_runtime" }),
    /PERSISTENCE_ROLE_REACTIVATION_REQUIRES_EXPLICIT_RECOVERY/,
    "bootstrap must not undo an urgent NOLOGIN revocation",
  );
  const elevatedPool = { query: async () => ({ rows: [{ ...bounded, create_role: true }] }) };
  await assert.rejects(() => roleCredential.ensureBoundedLoginRole(elevatedPool, { username: "core_runtime" }), /PERSISTENCE_ROLE_PRIVILEGE_BOUNDARY_NOT_CONFIRMED/);
  const observed = [], source = Array.from({ length: 9 }, (_, ordinal) => ({ schema: "core/diagnostic-record/v1", code: "core.persistence.in-memory-boundary-failed", definitionVersion: 1,
    detail: { operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal } }));
  const native = Object.freeze(Object.assign(new Error("PRIVATE-role-canary"), { diagnosticRecord: source[0], relatedDiagnosticRecords: source.slice(1) }));
  const diagnostics = { onObservation(record, evidence) { observed.push({ record, evidence }); } };
  for (const [facts, options, field, condition] of [[undefined, {}, "row", "missing"], [{ ...bounded, exists: false }, {}, "exists", "falsy"], [{ ...bounded, inherit: true }, {}, "inherit", "truthy"], [{ ...bounded, can_login: false }, { requireLogin: true }, "can-login", "falsy"]]) {
    observed.length = 0;
    await assert.rejects(() => roleCredential.requireBoundedExistingRole({ query: async () => ({ rows: facts === undefined ? [] : [facts] }) }, { username: "core_runtime" }, options, diagnostics));
    const record = observed.find(({ record }) => record.code.endsWith("predicate-rejected")).record;
    assert.equal(record.detail.field, field); assert.equal(record.detail.condition, condition);
  }
  for (const [field, property] of [["exists", "exists"], ["can-login", "can_login"], ["superuser", "superuser"], ["create-role", "create_role"], ["create-database", "create_database"], ["replication", "replication"], ["bypass-rls", "bypass_rls"], ["inherit", "inherit"]]) {
    observed.length = 0;
    await assert.rejects(() => roleCredential.requireBoundedExistingRole({ query: async () => ({ rows: [{ ...bounded, [property]: "PRIVATE-role-canary" }] }) }, { username: "core_runtime" }, {}, diagnostics), /PERSISTENCE_ROLE_STATE_UNAVAILABLE/);
    assert.deepEqual(observed.find(({ record }) => record.code.endsWith("predicate-rejected")).record.detail, { task: "administration", operation: "role-facts", field, condition: "wrong-type", effect: "predicate-rejected" });
  }
  for (const [field, property] of [["superuser", "superuser"], ["create-role", "create_role"], ["create-database", "create_database"], ["replication", "replication"], ["bypass-rls", "bypass_rls"]]) {
    observed.length = 0;
    await assert.rejects(() => roleCredential.ensureBoundedLoginRole({ query: async () => ({ rows: [{ ...bounded, [property]: true }] }) }, { username: "core_runtime" }, diagnostics), /PERSISTENCE_ROLE_PRIVILEGE_BOUNDARY_NOT_CONFIRMED/);
    assert.equal(observed.find(({ record }) => record.code.endsWith("predicate-rejected")).record.detail.field, field);
  }
  observed.length = 0;
  let reads = 0;
  const facts = { ...bounded, get exists() { reads++; if (reads === 2) throw native; return true; } };
  await assert.rejects(() => roleCredential.requireBoundedExistingRole({ query: async () => ({ rows: [facts] }) }, { username: "core_runtime" }, {}, diagnostics), (error) => error === native);
  assert.equal(reads, 2); assert.deepEqual(observed[0].evidence, { diagnosticRecord: source[0], relatedDiagnosticRecords: source.slice(1) });
  assert.equal(observed[0].record.detail.field, "exists");
  observed.length = 0;
  await assert.rejects(() => roleCredential.ensureRdsIamAuthentication({ query: async () => ({ rows: [{ member: 1 }] }) }, { username: "core_runtime" }, diagnostics), /PERSISTENCE_RUNTIME_IAM_ACCESS_NOT_CONFIRMED/);
  assert.equal(observed[0].record.detail.condition, "not-true");
  observed.length = 0;
  await assert.rejects(() => roleCredential.ensureRdsIamAuthentication({ query: async () => ({ rows: [] }) }, { username: "PRIVATE-invalid-role" }, diagnostics), /PERSISTENCE_ROLE_IDENTIFIER_INVALID/);
  assert.equal(observed[0].record.detail.condition, "pattern");
  assert.equal(JSON.stringify(observed).includes("PRIVATE-"), false);
}

async function operationProducerRegression() {
  const connection = require(join(compiled, "platform/adapters/aws/persistence/postgresql/src/connection.js"));
  const originalPool = connection.createNodePostgreSqlConnectionPool, originalTokenPool = connection.createNodePostgreSqlTokenConnectionPool;
  const originalLog = console.log, originalError = console.error, originalExit = process.exitCode;
  const source = (base) => Array.from({ length: 9 }, (_, offset) => ({ schema: "core/diagnostic-record/v1", code: "core.persistence.in-memory-boundary-failed", definitionVersion: 1,
    detail: { operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal: base + offset } }));
  const first = source(0), second = source(20);
  const failure = (records) => Object.freeze(Object.assign(new Error("PRIVATE-administration-canary"), { diagnosticRecord: records[0], relatedDiagnosticRecords: records.slice(1) }));
  const body = failure(first), cleanup = failure(second), events = [], output = [];
  console.log = console.error = (value) => { events.push("output"); output.push(JSON.parse(value)); };
  const run = async (operation, pool, tokenPool) => {
    output.length = events.length = 0; process.exitCode = 73;
    connection.createNodePostgreSqlConnectionPool = () => pool;
    connection.createNodePostgreSqlTokenConnectionPool = () => tokenPool;
    return administration.runKanbienCoreServerPersistenceAdministration({ ...valid, PERSISTENCE_ADMINISTRATION_OPERATION: operation });
  };
  try {
    const statements = [];
    const pool = { async query(statement) { statements.push(statement.text); if (statement.text.startsWith("GRANT SELECT")) throw body; if (statement.text === "ROLLBACK") throw cleanup; return { rows: [] }; }, async end() { events.push("end"); } };
    await run("grant-runtime-application-access", pool);
    assert.deepEqual(events, ["output", "end"]); assert.equal(process.exitCode, 1);
    assert.equal(statements.at(-1), "ROLLBACK");
    assert.deepEqual([output[0].diagnostic, ...output[0].related_diagnostics], first);
    assert.deepEqual(output[0].source_bundles, [{ diagnostic: second[0], related_diagnostics: second.slice(1) }]);
    assert.deepEqual(output[0].observations.map(({ detail }) => detail.phase), ["grant-runtime", "rollback", "task-body"]);
    let released = 0, runtimeEnd = 0;
    const token = { async connect() { return { async query(statement) { if (statement.text.startsWith("INSERT")) throw body; return { rows: [] }; }, release() { released++; throw cleanup; } }; }, async end() { runtimeEnd++; } };
    await run("prove-effective-privilege", { async end() { events.push("end"); } }, token);
    assert.equal(released, 1); assert.equal(runtimeEnd, 0, "throwing release still prevents the original inner pool.end");
    assert.deepEqual(output[0].observations.map(({ detail }) => detail.phase), ["runtime-insert", "client-release", "task-body"]);
    assert.deepEqual([output[0].diagnostic, ...output[0].related_diagnostics], first);
    assert.deepEqual(output[0].source_bundles, [{ diagnostic: second[0], related_diagnostics: second.slice(1) }]);
    await assert.rejects(() => run("grant-runtime-application-access", { async query(statement) { if (statement.text.startsWith("GRANT SELECT")) throw body; return { rows: [] }; }, async end() { events.push("end"); throw cleanup; } }), (error) => error === cleanup);
    assert.deepEqual(events, ["output", "end", "output"]);
    assert.deepEqual([output[1].diagnostic, ...output[1].related_diagnostics], second);
    assert.deepEqual(output[1].observations.map(({ detail }) => detail.phase), ["pool-end"]);
    assert.equal(output[1].overflow, undefined, "late frame never replays earlier cumulative overflow");
    output.length = events.length = 0; process.exitCode = 73;
    connection.createNodePostgreSqlConnectionPool = () => { throw body; };
    await assert.rejects(() => administration.runKanbienCoreServerPersistenceAdministration(valid), (error) => error === body);
    assert.equal(process.exitCode, 73); assert.equal(output.length, 1);
    assert.deepEqual(output[0].observations[0].detail, { task: "administration", operation: "administration", phase: "pool-construction", condition: "threw", effect: "unknown" });
    assert.deepEqual([output[0].diagnostic, ...output[0].related_diagnostics], first);
    const native = Object.freeze(new Error("PRIVATE-native-canary"));
    output.length = 0;
    await assert.rejects(() => administration.runKanbienCoreServerPersistenceAdministration(Object.defineProperty({ ...valid }, "PERSISTENCE_POSTGRES_HOST", { get() { throw native; } })), (error) => error === native);
    assert.equal(output[0].observations[0].detail.phase, "configuration"); assert.equal(process.exitCode, 73);
    assert.equal(JSON.stringify(output).includes("PRIVATE-"), false);
    for (const [aggregate, visit, expected] of [[false, false, "predicate-rejected"], [false, true, "id-mismatch"], [true, true, undefined]]) {
      const statements = [], rows = { length: 2, every(callback) { assert.equal(this, rows); if (visit) callback({ migration_id: "PRIVATE-id-canary", checksum: "PRIVATE-checksum-canary" }, 999); return aggregate; } };
      await run("observe-migration-state", { async query(statement) { statements.push(statement.text); return { rows }; }, async end() {} });
      assert.equal(statements.length, 4); assert.equal(statements.at(-1), "ROLLBACK");
      if (expected === undefined) assert.deepEqual(output[0], { verdict: "accepted", code: "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED" });
      else {
        const record = output[0].observations.find(({ code }) => code.endsWith("predicate-rejected"));
        assert.equal(record.detail.condition, expected); assert.equal(record.detail.ordinal, visit ? 0 : undefined, "ordinal is actual visit, never custom supplied index999");
      }
      assert.equal(JSON.stringify(output).includes("PRIVATE-"), false);
    }
    let rollbacks = 0;
    await run("observe-migration-state", { async query(statement) { if (statement.text === "ROLLBACK") throw ++rollbacks === 1 ? body : cleanup; return { rows: [] }; }, async end() {} });
    assert.equal(rollbacks, 2, "failed first read-only rollback retains the original catch's retry");
    assert.deepEqual(output[0].source_bundles, [{ diagnostic: second[0], related_diagnostics: second.slice(1) }]);
  } finally { connection.createNodePostgreSqlConnectionPool = originalPool; connection.createNodePostgreSqlTokenConnectionPool = originalTokenPool; console.log = originalLog; console.error = originalError; process.exitCode = originalExit; }
}

async function migrationCleanupRegression() {
  const connection = require(join(compiled, "platform/adapters/aws/persistence/postgresql/src/connection.js"));
  const migrations = require(join(compiled, "platform/adapters/aws/persistence/postgresql/src/migrations.js"));
  const originalPool = connection.createNodePostgreSqlTokenConnectionPool, originalRunner = migrations.createPostgreSqlMigrationRunner;
  const originalLog = console.log, originalError = console.error, originalExit = process.exitCode;
  const source = (offset) => Array.from({ length: 9 }, (_, ordinal) => ({ schema: "core/diagnostic-record/v1", code: "core.persistence.in-memory-boundary-failed", definitionVersion: 1,
    detail: { operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal: offset + ordinal } }));
  const first = source(0), second = source(20);
  const failure = (records) => Object.freeze(Object.assign(new Error("PRIVATE-migration-cleanup-canary"), { diagnosticRecord: records[0], relatedDiagnosticRecords: records.slice(1) }));
  const body = failure(first), cleanup = failure(second), output = [], events = [];
  console.log = console.error = (line) => { events.push("output"); output.push(JSON.parse(line)); };
  const boundary = (operation, phase, at, condition, effect) => ({ schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1, detail: { operation, phase, boundary: at, condition, effect } });
  try {
    for (const bodyFails of [false, true]) for (const ending of ["none", "sync", "rejected"]) {
      output.length = events.length = 0; process.exitCode = 73;
      let ends = 0, applies = 0, queries = 0;
      const pool = { query() { queries++; throw new Error("Unexpected SQL"); }, end() { assert.equal(this, pool); events.push("end"); ends++; if (ending === "sync") throw cleanup; return ending === "rejected" ? Promise.reject(cleanup) : Promise.resolve(); } };
      connection.createNodePostgreSqlTokenConnectionPool = () => pool;
      migrations.createPostgreSqlMigrationRunner = (_configuration, options) => { assert.equal(options.pool, pool); return { async apply(manifest) {
        applies++; assert.equal(manifest.schemaPreprovisioned, true); assert.equal(manifest.migrations.length, 2);
        if (bodyFails) throw body; return { ok: true, value: [] };
      } }; };
      const run = () => migration.runKanbienCoreServerPersistenceMigration(valid);
      if (ending === "none") await run(); else await assert.rejects(run, (error) => error === cleanup);
      assert.equal(applies, 1); assert.equal(queries, 0); assert.equal(ends, 1); assert.equal(events.indexOf("end") > events.indexOf("output"), true);
      assert.deepEqual(output[0], bodyFails ? { verdict: "rejected", code: "PERSISTENCE_MIGRATION_NOT_CONFIRMED", stage: "migration" } : { verdict: "accepted", code: "PERSISTENCE_MIGRATION_APPLIED" });
      assert.equal(process.exitCode, bodyFails ? 1 : 73, "cleanup never adds a new exitCode disposition");
      const records = output.filter((value) => value.message === "platform.diagnostic.observed");
      assert.deepEqual(records.map((value) => value.fields.diagnostic), [
        ...(bodyFails ? [boundary("migration", "invocation", "body", "threw", "unknown"), ...first] : []),
        ...(ending === "none" ? [] : [boundary("connection-pool", ending === "sync" ? "invocation" : "completion", "end", ending === "sync" ? "threw" : "rejected", "not-assessed"), ...second]),
      ]);
      assert.equal(records.every((value) => value.fields.operation === "migration" && value.fields.stage === "migration"), true);
      assert.equal(JSON.stringify(output).includes("PRIVATE-"), false);
    }
    const serialization = Object.freeze(new Error("PRIVATE-serialization-canary"));
    let ends = 0;
    connection.createNodePostgreSqlTokenConnectionPool = () => ({ async end() { ends++; } });
    migrations.createPostgreSqlMigrationRunner = () => ({ async apply() { throw body; } });
    console.error = () => { throw serialization; }; process.exitCode = 73;
    await assert.rejects(() => migration.runKanbienCoreServerPersistenceMigration(valid), (error) => error === serialization);
    assert.equal(ends, 1); assert.equal(process.exitCode, 73, "failed original serialization keeps its original exitCode timing");
  } finally { connection.createNodePostgreSqlTokenConnectionPool = originalPool; migrations.createPostgreSqlMigrationRunner = originalRunner; console.log = originalLog; console.error = originalError; process.exitCode = originalExit; }
}

async function iamAuthenticationRegression() {
  const configuration = config.persistenceConfiguration(valid, "server");
  assert.ok(configuration);
  const initialSigners = globalThis.signerOptions.length, initialRequests = globalThis.tokenRequests;
  const local = iamAuthentication.persistenceIamAuthentication({ ...valid, NODE_ENV: "test", PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN: "synthetic-test-token" }, configuration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME");
  assert.equal(globalThis.signerOptions.length, initialSigners, "test-only qualification does not construct a real signer");
  assert.equal(await local.authenticationToken(), "synthetic-test-token", "The disposable route must be explicit and test-only.");
  const production = iamAuthentication.persistenceIamAuthentication({ ...valid, NODE_ENV: "production", PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN: "synthetic-test-token" }, configuration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME");
  assert.equal(production.username, valid.PERSISTENCE_RUNTIME_DATABASE_USERNAME);
  assert.deepEqual(globalThis.signerOptions.at(-1), { region: valid.PERSISTENCE_POSTGRES_IAM_REGION, hostname: valid.PERSISTENCE_POSTGRES_HOST, port: 5432, username: valid.PERSISTENCE_RUNTIME_DATABASE_USERNAME });
  assert.equal(globalThis.signerOptions.length, initialSigners + 1);
  assert.equal(globalThis.tokenRequests, initialRequests, "configuration must not request a token; driver consumption remains lazy");
  assert.notEqual(await production.authenticationToken(), "synthetic-test-token", "A local qualification token must never override the production signer.");
  assert.equal(globalThis.tokenRequests, initialRequests + 1);
  for (const [username, region] of [["_", "aa-x-0"], ["_".repeat(63), "eu-west-1"]]) {
    const accepted = iamAuthentication.persistenceIamAuthenticationResult({ ...valid, PERSISTENCE_RUNTIME_DATABASE_USERNAME: username, PERSISTENCE_POSTGRES_IAM_REGION: region }, configuration, "PERSISTENCE_RUNTIME_DATABASE_USERNAME");
    assert.equal(accepted.ok, true, "the migration preserves the previous lexical acceptance rules, not an inferred identity/region allowlist");
    assert.equal(accepted.value.username, username);
    assert.equal(globalThis.signerOptions.at(-1).region, region);
  }
  assert.equal(globalThis.tokenRequests, initialRequests + 1, "accepted configuration variants remain lazy");
}

function targetTemplateRegression() {
  const template = originalRead("infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml", "utf8");
  assert.equal(template.includes("PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN"), false, "The target realization must reject the local-token test escape by never declaring it.");
  assert.equal(template.includes("PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN_DELAY_MS"), false, "The target realization must reject the test-only IAM-token delay escape by never declaring it.");
  assert.equal(/Name:\s*NODE_ENV,\s*Value:\s*test/.test(template), false, "The target realization must never deploy a test runtime marker.");
  assert.equal(template.includes("PERSISTENCE_RUNTIME_CREDENTIALS"), false, "The deployed server must not receive the retired runtime password secret.");
  assert.equal(template.includes("PERSISTENCE_MIGRATION_CREDENTIALS"), false, "The deployed migration task must not receive the retired migration password secret.");
}

async function implementationSelectionRegression() {
  const composition = require(join(entrypoints, "kanbien-core-server-persistence-composition.js"));
  assert.equal(composition.selectPersistenceImplementation(undefined).value, composition.selectPersistenceImplementation("postgresql").value);
  assert.equal(Object.isFrozen(composition.selectPersistenceImplementation(undefined).value), true);
  for (const [selection, reason] of [[42, "wrong-type"], [" ", "blank"], [" postgresql ", "surrounding-whitespace"], ["synthetic-private-selection", "unsupported"]]) {
    let reads = 0;
    const env = new Proxy({ PERSISTENCE_IMPLEMENTATION: selection }, { get(target, key) {
      if (key !== "PERSISTENCE_IMPLEMENTATION") { reads++; throw new Error("must-not-read-unselected-configuration"); }
      return target[key];
    }, ownKeys() { reads++; throw new Error("must-not-snapshot-unselected-source"); } });
    for (const purpose of ["server", "migration", "restore", "administration"]) {
      const failure = config.persistenceConfigurationResult(env, purpose);
      assert.equal(failure.ok, false);
      assert.deepEqual(failure.error.diagnostic.detail, { phase: "implementation-selection", reason, effect: "not-started" });
      assert.equal(JSON.stringify(failure).includes("synthetic-private-selection"), false);
    }
    const priorError = console.error, exit = process.exitCode, output = [], pools = globalThis.poolAttempts;
    try { console.error = text => output.push(JSON.parse(text));
      await server.runKanbienCoreServerPersistenceMain(env);
      assert.equal(process.exitCode, 1); assert.equal(globalThis.poolAttempts, pools);
      assert.equal(output[0].diagnostic.code, "kanbien-core-server.persistence-implementation-invalid");
      assert.deepEqual(output[0].diagnostic_context, { capability: "persistence", operation: "startup", stage: "startup" });
    } finally { console.error = priorError; process.exitCode = exit; }
    assert.equal(reads, 0, "unsupported selection must stop before implementation-specific reads");
  }
  for (const purpose of ["server", "migration", "restore", "administration"]) {
    assert.deepEqual(config.persistenceConfigurationResult({ ...valid, PERSISTENCE_IMPLEMENTATION: "postgresql" }, purpose), config.persistenceConfigurationResult(valid, purpose));
  }
  // The actual main must use the constructor selected by composition.
  const filename = join(entrypoints, "kanbien-core-server-persistence.main.js"), local = createRequire(filename), fixture = { exports: {} };
  let poolCalls = 0, runtimeCalls = 0, closed = 0, selections = 0;
  const runtime = { close: async () => { closed++; }, readiness: async () => "ready", readinessObservation: async () => ({ readiness: "ready" }) };
  const selected = { ...composition.selectPersistenceImplementation(undefined).value,
    createPool() { poolCalls++; return { fixture: true }; },
    createRuntime(options) { assert.equal(options.pool.fixture, true); runtimeCalls++; return runtime; },
  };
  const observability = local("./kanbien-platform-observability");
  let received;
  new Function("require", "module", "exports", fs.readFileSync(filename, "utf8"))(
    name => name === "./kanbien-core-server-persistence-composition" ? { selectPersistenceImplementation() { selections++; return { ok: true, value: selected }; } }
      : name === "./kanbien-core-server-persistence-configuration" ? { ...config, persistenceCertificateAuthorityResult: () => ({ ok: true, value: "fixture-authority" }) }
      : name === "./kanbien-core-server-persistence-iam-authentication" ? { persistenceIamAuthenticationResult: () => ({ ok: true, value: {} }) }
      : name === "./kanbien-platform-observability" ? { ...observability, observabilityConfigurationFromTargetEnvironment: () => ({ ok: true, value: { options: {} } }),
          createTargetObservabilityRuntime: () => ({ ok: true, value: undefined }) }
      : name === "./kanbien-core-server-persistence.app" ? { ...local(name), createKanbienCoreServerPersistenceApp(_release, supplied) { received = supplied; return {}; } }
      : name === "@kanbien/platform-server/main" ? { startPlatformServerProcess: async () => ({ ok: false, error: { code: "FIXTURE_STOP" } }) } : local(name),
    fixture, fixture.exports,
  );
  const error = console.error, exit = process.exitCode;
  try { console.error = () => undefined; await fixture.exports.runKanbienCoreServerPersistenceMain(valid); }
  finally { console.error = error; process.exitCode = exit; }
  assert.equal(selections, 1); assert.equal(poolCalls, 1); assert.equal(runtimeCalls, 1); assert.equal(closed, 1);
  assert.equal(received, runtime, "the module must receive the selected constructor result");
}
