// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.entity-smoke.verify-image
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Exercise actual packaged feature programs against restricted disposable PostgreSQL and independently restored fixture data.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   effects: [network, writes-files]
//   used_by:
//   - id: deploy.command.smoke-test-entity-smoke-image
//     path: scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/script.sh
import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync, readFileSync, lstatSync, realpathSync, rmSync, openSync, fsyncSync, closeSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, dirname, basename } from "node:path";
import { randomBytes } from "node:crypto";

let phase = "arguments", cleanupConfirmed = true, temporary, qualification, cleaned = false, effectsInvoked = false;
const owned = { containers: [], networks: [], volumes: [] }, stages = [];
const administratorPassword = "synthetic-entity-smoke-administrator";
const token = "entity-smoke-disposable-fixture";
// Match the read-only-observed core-platform engine, not an assumed older
// major. Any target engine change requires newly matched qualification.
const postgreSqlImage = "postgres:18.3-bookworm";
const postgreSqlData = "/var/lib/postgresql/18/docker";
const markers = [administratorPassword, token, "SCRAM-SHA-256$", "credential-row-provider-canary"];
function fail() { throw new Error("ENTITY_SMOKE_IMAGE_PROOF_NOT_CONFIRMED"); }
function safe(value) { if (markers.some(marker => String(value).includes(marker))) fail(); return value; }
function invoke(executable, args, { input, timeout = 90_000, allowFailure = false, checkOutput = true } = {}) {
  const observed = spawnSync(executable, args, { input, encoding: "utf8", timeout, maxBuffer: 8 * 1024 * 1024 });
  if (checkOutput) { safe(observed.stdout ?? ""); safe(observed.stderr ?? ""); }
  if (observed.error || observed.signal || observed.status === null || !allowFailure && observed.status !== 0) fail();
  return observed;
}
const docker = (args, options) => invoke("docker", args, options).stdout;
function cleanup() {
  if (cleaned) return;
  cleaned = true;
  try {
    if (effectsInvoked && (owned.containers.length || owned.networks.length || owned.volumes.length)) {
      const args = ["-B", "scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py", ...owned.containers.flatMap(name => ["--container", name]), ...owned.networks.flatMap(name => ["--network", name]), ...owned.volumes.flatMap(name => ["--volume", name])];
      const result = spawnSync("python3", args, { encoding: "utf8", timeout: 180_000 });
      cleanupConfirmed = !result.error && !result.signal && result.status === 0;
    }
    if (temporary && cleanupConfirmed) rmSync(temporary, { recursive: true });
  } catch { cleanupConfirmed = false; }
  if (!cleanupConfirmed) {
    process.exitCode = 1;
    console.error(JSON.stringify({ code: "ENTITY_SMOKE_DISPOSABLE_CLEANUP_NOT_CONFIRMED", verdict: "failed", ...(temporary === undefined ? {} : { resource_reservation_id: basename(temporary) }) }));
  }
}
for (const signal of ["SIGINT", "SIGTERM", "SIGHUP"]) process.once(signal, () => {
  process.exitCode = 1;
  console.error(JSON.stringify({ code: "ENTITY_SMOKE_IMAGE_PROOF_INTERRUPTED", verdict: "failed", phase }));
  cleanup(); process.exit(1);
});
function parsed(output) { try { return JSON.parse(output); } catch { return fail(); } }
function expected(output, code) {
  const records = output.trim().split("\n").map(line => { try { return JSON.parse(line); } catch { return undefined; } });
  const matches = records.filter(record => record?.verdict === "passed" && record?.code === code);
  if (matches.length !== 1) fail();
  return matches[0];
}
function expectedRejection(observed, diagnosticCode, detail) {
  if (observed.status !== 1) fail();
  const records = (observed.stdout + "\n" + observed.stderr).trim().split("\n").flatMap(line => {
    try { return [JSON.parse(line)]; } catch { return []; }
  });
  if (records.some(record => record.verdict === "passed")) fail();
  const rejected = records.filter(record => record.verdict === "failed" && record.code === "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED" && record.diagnostic?.code === diagnosticCode);
  if (rejected.length !== 1 || !Object.entries(detail).every(([key, value]) => rejected[0].diagnostic.detail?.[key] === value)) fail();
}
function mark(name) { stages.push(name); console.log(JSON.stringify({ schema: "deploy/entity-smoke-image-progress/v1", phase: name, verdict: "passed" })); }
try {
  const args = process.argv.slice(2);
  if (args.length === 2 && args[0] === "--cleanup-reservation") {
    phase = "reserved-cleanup";
    const path = resolve(args[1]), directory = dirname(path);
    if (basename(path) !== "resource-reservation.json" || dirname(directory) !== realpathSync(tmpdir()) || !/^entity-smoke-image-[A-Za-z0-9]{6}$/.test(basename(directory)) || realpathSync(directory) !== directory || lstatSync(path).isSymbolicLink() || lstatSync(path).uid !== process.getuid() || (lstatSync(path).mode & 0o777) !== 0o600) fail();
    const value = parsed(readFileSync(path, "utf8"));
    if (!value || Object.keys(value).sort().join() !== ["schema", "source_revision", "local_image_id", "containers", "networks", "volumes"].sort().join() || value.schema !== "deploy/entity-smoke-image-resources/v1" || !/^[a-f0-9]{40}$/.test(value.source_revision) || !/^sha256:[a-f0-9]{64}$/.test(value.local_image_id) || !Array.isArray(value.networks) || value.networks.length !== 1 || typeof value.networks[0] !== "string" || !/^entity-smoke-qualification-[a-f0-9]{24}$/.test(value.networks[0])) fail();
    const network = value.networks[0];
    if (JSON.stringify(value.containers) !== JSON.stringify([network + "-task", network + "-database", network + "-restored", network + "-server"]) || JSON.stringify(value.volumes) !== JSON.stringify([network + "-certs", network + "-source-data", network + "-restored-data"])) fail();
    temporary = directory;
    owned.containers.push(...value.containers); owned.networks.push(...value.networks); owned.volumes.push(...value.volumes);
    effectsInvoked = true;
    cleanup();
    if (!cleanupConfirmed) fail();
    console.log(JSON.stringify({ schema: "deploy/entity-smoke-image-cleanup/v1", verdict: "passed", qualification_evidence: false }));
    process.exit(0);
  }
  const tag = args.length === 0 ? "kanbien-entity-smoke:qualification" : args.length === 2 && args[0] === "--tag" ? args[1] : "";
  if (!/^kanbien-entity-smoke:[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$/.test(tag)) fail();
  phase = "source";
  const source = invoke("git", ["rev-parse", "HEAD"]).stdout.trim();
  if (!/^[a-f0-9]{40}$/.test(source) || invoke("git", ["status", "--porcelain", "--untracked-files=all", "--", ".", ":!commitLogs"]).stdout.trim()) fail();
  phase = "engine";
  docker(["info", "--format", "{{.OSType}}"], { timeout: 30_000 });
  const image = parsed(docker(["image", "inspect", tag]))[0];
  if (!image || image.Architecture !== "amd64" || image.Os !== "linux" || image.Config?.User !== "nonroot" || image.Config?.Labels?.["org.opencontainers.image.revision"] !== source || !/^sha256:[a-f0-9]{64}$/.test(image.Id)) fail();
  if (!Array.isArray(image.Config.Env) || image.Config.Env.some(value => typeof value !== "string" || value.startsWith("PERSISTENCE_") || value.startsWith("ENTITY_SMOKE_LOCAL_QUALIFICATION_TOKEN="))) fail();
  phase = "disposable-resources";
  const suffix = randomBytes(12).toString("hex"), network = "entity-smoke-qualification-" + suffix;
  const database = network + "-database", restored = network + "-restored", server = network + "-server", task = network + "-task", volume = network + "-certs";
  const label = "entity-smoke-" + suffix;
  temporary = mkdtempSync(join(tmpdir(), "entity-smoke-image-"));
  const files = name => join(temporary, name);
  owned.networks.push(network); owned.volumes.push(volume, network + "-source-data", network + "-restored-data");
  owned.containers.push(task, database, restored, server);
  // A retained reservation permits exact cleanup after abrupt host/process
  // loss too; it contains no certificate, credential or feature row values.
  const reservation = files("resource-reservation.json");
  writeFileSync(reservation, JSON.stringify({ schema: "deploy/entity-smoke-image-resources/v1", source_revision: source,
    local_image_id: image.Id, containers: owned.containers, networks: owned.networks, volumes: owned.volumes }) + "\n", { flag: "wx", mode: 0o600 });
  for (const path of [reservation, temporary]) {
    const descriptor = openSync(path, "r");
    try { fsyncSync(descriptor); } finally { closeSync(descriptor); }
  }
  invoke("openssl", ["req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", files("ca.key"), "-out", files("ca.crt"), "-subj", "/CN=entity-smoke-fixture-ca", "-days", "1"]);
  invoke("openssl", ["req", "-newkey", "rsa:2048", "-nodes", "-keyout", files("server.key"), "-out", files("server.csr"), "-subj", "/CN=postgres"]);
  writeFileSync(files("server.ext"), "subjectAltName=DNS:postgres,DNS:postgres-restored\n", { mode: 0o600 });
  invoke("openssl", ["x509", "-req", "-in", files("server.csr"), "-CA", files("ca.crt"), "-CAkey", files("ca.key"), "-CAcreateserial", "-out", files("server.crt"), "-days", "1", "-extfile", files("server.ext")]);
  // Register exact names before creation so uncertain effects are reconciled
  // by the existing cleanup owner, not mistaken for absence or relaunched.
  effectsInvoked = true;
  docker(["network", "create", "--internal", "--label", "scope=entity-smoke-qualification", network]);
  for (const name of owned.volumes) docker(["volume", "create", "--label", "scope=entity-smoke-qualification", name]);
  docker(["run", "--rm", "--name", task, "--user", "root", "-v", temporary + ":/source:ro", "-v", volume + ":/certs", postgreSqlImage, "bash", "-ec", "cp /source/server.crt /source/server.key /certs/; chown 999:999 /certs/server.crt /certs/server.key; chmod 600 /certs/server.key; chmod 644 /certs/server.crt"]);
  function psql(container, sql, { input, allowFailure = false } = {}) {
    return docker(["exec", "-i", container, "psql", "-X", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-U", "fixture_root", "-d", "entitysmoke", ...(sql ? ["-c", sql] : [])], { input, allowFailure });
  }
  async function startDatabase(name, alias) {
    const dataVolume = network + (name === database ? "-source-data" : "-restored-data");
    docker(["run", "--detach", "--rm", "--name", name, "--network", network, "--network-alias", alias, "-e", "POSTGRES_DB=entitysmoke", "-e", "POSTGRES_USER=fixture_root", "-e", "POSTGRES_PASSWORD=" + administratorPassword, "-v", volume + ":/certs:ro", "-v", dataVolume + ":/var/lib/postgresql", postgreSqlImage, "postgres", "-c", "ssl=on", "-c", "ssl_cert_file=/certs/server.crt", "-c", "ssl_key_file=/certs/server.key", "-c", "log_destination=stderr", "-c", "logging_collector=on", "-c", "log_directory=" + postgreSqlData + "/log", "-c", "log_filename=postgresql.log", "-c", "log_min_error_statement=error"]);
    for (let attempt = 0; attempt < 40; attempt++) {
      const ready = invoke("docker", ["exec", name, "pg_isready", "-U", "fixture_root", "-d", "entitysmoke"], { allowFailure: true });
      if (ready.status === 0) {
        if (psql(name, "SHOW server_version_num").trim() !== "180003") fail();
        return;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    fail();
  }
  await startDatabase(database, "postgres");
  // The administrator needs grant authority only on this disposable database
  // to give/revoke the migration owner's temporary schema-creation privilege.
  // It still has no superuser/CREATEDB/replication/bypass-RLS authority.
  psql(database, undefined, { input: "CREATE ROLE rds_iam NOLOGIN;\nCREATE ROLE core_administrator LOGIN CREATEROLE INHERIT;\nGRANT CREATE, CONNECT ON DATABASE entitysmoke TO core_administrator WITH GRANT OPTION;\nGRANT pg_signal_backend TO core_administrator;\nGRANT rds_iam TO core_administrator WITH ADMIN OPTION, INHERIT FALSE, SET TRUE;\n" });
  function password(container, username, value) { psql(container, "\\password " + username, { input: value + "\n" + value + "\n" }); }
  password(database, "core_administrator", administratorPassword);
  const environment = (values) => Object.entries(values).flatMap(([name, value]) => ["-e", name + "=" + value]);
  const base = ["--network", network, "-v", files("ca.crt") + ":/app/assets/rds-eu-west-1-bundle.crt:ro", ...environment({ NODE_ENV: "test", ENTITY_SMOKE_LOCAL_QUALIFICATION_TOKEN: token, PERSISTENCE_POSTGRES_HOST: "postgres", PERSISTENCE_POSTGRES_PORT: "5432", PERSISTENCE_POSTGRES_DATABASE: "entitysmoke", PERSISTENCE_POSTGRES_SCHEMA: "entity_smoke", PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/rds-eu-west-1-bundle.crt", PERSISTENCE_POSTGRES_IAM_REGION: "eu-west-1", PLATFORM_DEPLOYMENT_EXPOSURE: "private" })];
  const authentication = username => environment({ PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-ABCDEFGHIJKLMNOP/" + username });
  const admin = (operation, resultCode = operation === "preflight" ? "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED" : operation === "observe-migration-state" ? "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED" : "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED") => expected(docker(["run", "--rm", "--name", task, ...base, ...environment({ ENTITY_SMOKE_ADMINISTRATION_OPERATION: operation, PERSISTENCE_RUNTIME_DATABASE_USERNAME: "entity_smoke_runtime", PERSISTENCE_MIGRATION_DATABASE_USERNAME: "entity_smoke_migration", PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:fixture-admin", PERSISTENCE_ADMINISTRATOR_CREDENTIALS: JSON.stringify({ username: "core_administrator", password: administratorPassword }) }), tag, "artifacts/kanbien-entity-smoke-administration.main.js"]), resultCode);
  phase = "restricted-administration";
  admin("preflight");
  admin("bootstrap");
  password(database, "entity_smoke_runtime", token); password(database, "entity_smoke_migration", token);
  phase = "migration";
  admin("observe-migration-state", "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED");
  expected(docker(["run", "--rm", "--name", task, ...base, ...authentication("entity_smoke_migration"), ...environment({ PERSISTENCE_MIGRATION_DATABASE_USERNAME: "entity_smoke_migration", ENTITY_SMOKE_MIGRATION_OPERATION: "preflight" }), tag, "artifacts/kanbien-entity-smoke-migration.main.js"]), "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED");
  expected(docker(["run", "--rm", "--name", task, ...base, ...authentication("entity_smoke_migration"), ...environment({ PERSISTENCE_MIGRATION_DATABASE_USERNAME: "entity_smoke_migration", ENTITY_SMOKE_MIGRATION_OPERATION: "apply" }), tag, "artifacts/kanbien-entity-smoke-migration.main.js"]), "ENTITY_SMOKE_MIGRATION_APPLIED");
  const historyFacts = () => psql(database, "SELECT md5(string_agg(migration_id || checksum || tool_version || applied_at::text, ',' ORDER BY migration_id)) FROM entity_smoke.platform_migration_history");
  const originalHistory = historyFacts();
  expected(docker(["run", "--rm", "--name", task, ...base, ...authentication("entity_smoke_migration"), ...environment({ PERSISTENCE_MIGRATION_DATABASE_USERNAME: "entity_smoke_migration", ENTITY_SMOKE_MIGRATION_OPERATION: "apply" }), tag, "artifacts/kanbien-entity-smoke-migration.main.js"]), "ENTITY_SMOKE_MIGRATION_ALREADY_APPLIED");
  if (historyFacts() !== originalHistory) fail();
  admin("observe-migration-state"); admin("grant-runtime"); admin("observe-permissions");
  mark("restricted-administration-and-migration");
  const runtime = [...base, ...authentication("entity_smoke_runtime"), ...environment({ PERSISTENCE_RUNTIME_DATABASE_USERNAME: "entity_smoke_runtime" })];
  expected(docker(["run", "--rm", "--name", task, ...runtime, ...environment({ ENTITY_SMOKE_DATABASE_PROOF_OPERATION: "preflight", ENTITY_SMOKE_PROOF_LABEL: label }), tag, "artifacts/kanbien-entity-smoke-database-proof.main.js"]), "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED");
  phase = "effective-privileges";
  expected(docker(["run", "--rm", "--name", task, ...runtime, ...environment({ ENTITY_SMOKE_DATABASE_PROOF_OPERATION: "permissions", ENTITY_SMOKE_PROOF_LABEL: label }), tag, "artifacts/kanbien-entity-smoke-database-proof.main.js"]), "ENTITY_SMOKE_EFFECTIVE_PRIVILEGES_PROVEN");
  async function startServer() {
    if (!owned.containers.includes(server)) owned.containers.push(server);
    docker(["run", "--detach", "--rm", "--name", server, "--network-alias", "entity-smoke", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", ...runtime, ...environment({ PLATFORM_SOURCE_COMMIT_SHA: source }), tag]);
    // Only readiness GETs are retried; no business mutation is repeated.
    docker(["exec", server, "/nodejs/bin/node", "-e", "(async()=>{for(let i=0;i<80;i++){try{if((await fetch('http://127.0.0.1:3000/readyz',{signal:AbortSignal.timeout(2000)})).status===200)return}catch{}await new Promise(r=>setTimeout(r,250))}process.exitCode=1})()"], { timeout: 45_000 });
  }
  const verify = (operation, digest) => {
    const output = docker(["run", "--rm", "--name", task, "--network", network, ...environment({ NODE_ENV: "test", ENTITY_SMOKE_VERIFICATION_OPERATION: operation, ENTITY_SMOKE_VERIFICATION_URL: "http://entity-smoke:3000/", ENTITY_SMOKE_PROOF_LABEL: label, ENTITY_SMOKE_EXPECTED_SOURCE: source, ...(digest === undefined ? {} : { ENTITY_SMOKE_EXPECTED_DIGEST: digest }) }), tag, "artifacts/kanbien-entity-smoke-verifier.main.js"], { timeout: 180_000 });
    return output;
  };
  phase = "packaged-feature";
  await startServer();
  const created = expected(verify("create"), "ENTITY_SMOKE_RECORD_CREATED");
  if (!/^[a-f0-9]{64}$/.test(created.record_digest)) fail();
  expected(docker(["run", "--rm", "--name", task, ...runtime, ...environment({ ENTITY_SMOKE_DATABASE_PROOF_OPERATION: "collision", ENTITY_SMOKE_PROOF_LABEL: label, ENTITY_SMOKE_EXPECTED_DIGEST: created.record_digest }), tag, "artifacts/kanbien-entity-smoke-database-proof.main.js"]), "ENTITY_SMOKE_IDENTIFIER_COLLISION_PROVEN");
  expected(verify("read", created.record_digest), "ENTITY_SMOKE_RECORD_RETRIEVED");
  if (expected(verify("observe-create"), "ENTITY_SMOKE_RECORD_RECONCILED").record_digest !== created.record_digest) fail();
  expected(verify("lifecycle"), "ENTITY_SMOKE_LIFECYCLE_PROVEN");
  mark("effective-privileges-and-packaged-lifecycle");
  phase = "replacement";
  safe(docker(["logs", server])); docker(["rm", "--force", server]);
  await startServer();
  expected(verify("read", created.record_digest), "ENTITY_SMOKE_RECORD_RETRIEVED");
  phase = "access-recovery";
  admin("revoke-runtime"); expected(verify("unready"), "ENTITY_SMOKE_LIVE_NOT_READY");
  admin("restore-runtime"); safe(docker(["logs", server])); docker(["rm", "--force", server]);
  await startServer(); expected(verify("read", created.record_digest), "ENTITY_SMOKE_RECORD_RETRIEVED");
  mark("replacement-and-access-recovery");
  phase = "independent-fixture-restore";
  await startDatabase(restored, "postgres-restored");
  psql(restored, undefined, { input: "CREATE ROLE rds_iam NOLOGIN;\nCREATE ROLE entity_smoke_runtime LOGIN NOINHERIT;\nCREATE ROLE entity_smoke_migration LOGIN NOINHERIT;\nGRANT rds_iam TO entity_smoke_runtime;\nGRANT rds_iam TO entity_smoke_migration;\n" });
  password(restored, "entity_smoke_runtime", token); password(restored, "entity_smoke_migration", token);
  const dump = docker(["exec", database, "pg_dump", "--schema=entity_smoke", "-U", "fixture_root", "-d", "entitysmoke"]);
  psql(restored, undefined, { input: dump });
  expected(docker(["run", "--rm", "--name", task, ...runtime, ...environment({ PERSISTENCE_POSTGRES_HOST: "postgres-restored", ENTITY_SMOKE_DATABASE_PROOF_OPERATION: "preflight", ENTITY_SMOKE_PROOF_LABEL: label }), tag, "artifacts/kanbien-entity-smoke-database-proof.main.js"]), "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED");
  expected(docker(["run", "--rm", "--name", task, ...runtime, ...environment({ PERSISTENCE_POSTGRES_HOST: "postgres-restored", ENTITY_SMOKE_DATABASE_PROOF_OPERATION: "restore-read", ENTITY_SMOKE_PROOF_LABEL: label, ENTITY_SMOKE_EXPECTED_DIGEST: created.record_digest }), tag, "artifacts/kanbien-entity-smoke-database-proof.main.js"]), "ENTITY_SMOKE_RESTORED_RECORD_RETRIEVED");
  expected(verify("read", created.record_digest), "ENTITY_SMOKE_RECORD_RETRIEVED");
  mark("independent-postgresql-fixture-restore");
  phase = "migration-checksum-negative";
  // Corrupt only the independently restored disposable fixture after its read
  // proof. Never modify the source database/history to manufacture a failure.
  psql(restored, "UPDATE entity_smoke.platform_migration_history SET checksum = repeat('0', 64)");
  const checksumRejected = invoke("docker", ["run", "--rm", "--name", task, ...base, ...authentication("entity_smoke_migration"), ...environment({ PERSISTENCE_POSTGRES_HOST: "postgres-restored", PERSISTENCE_MIGRATION_DATABASE_USERNAME: "entity_smoke_migration", ENTITY_SMOKE_MIGRATION_OPERATION: "apply" }), tag, "artifacts/kanbien-entity-smoke-migration.main.js"], { allowFailure: true });
  expectedRejection(checksumRejected, "persistence.local-rejected", { operation: "migration", field: "checksum", condition: "checksum-mismatch", effect: "unknown" });
  if (psql(restored, "SELECT bool_and(checksum = repeat('0', 64)) FROM entity_smoke.platform_migration_history").trim().split("\n").map(line => line.trim()).filter(line => line === "t").length !== 1) fail();
  if (historyFacts() !== originalHistory) fail();
  expected(verify("read", created.record_digest), "ENTITY_SMOKE_RECORD_RETRIEVED");
  mark("checksum-rejection-preserves-source-history-and-record");
  phase = "safe-downstream-logs";
  safe(docker(["logs", server]));
  for (const container of [database, restored]) {
    const files = docker(["exec", container, "find", postgreSqlData + "/log", "-type", "f"]).trim().split("\n");
    if (files.length === 0 || files.some(path => path !== postgreSqlData + "/log/postgresql.log")) fail();
    for (const path of files) safe(docker(["exec", container, "cat", path]));
  }
  mark("safe-downstream-logs");
  qualification = { schema: "deploy/entity-smoke-image-qualification/v1", verdict: "passed", source_revision: source,
    local_image_id: image.Id, engine_version: "18.3", stages, evidence_class: "container-qualification", aws_observation: false, rds_iam_authentication_proven: false, rds_snapshot_restore_proven: false };
} catch {
  process.exitCode = 1;
  console.error(JSON.stringify({ schema: "deploy/entity-smoke-image-qualification/v1", verdict: "failed", code: "ENTITY_SMOKE_IMAGE_PROOF_NOT_CONFIRMED", phase, effect: temporary || owned.containers.length || owned.networks.length ? "disposable-effects-possible" : "not-started", ...(temporary === undefined ? {} : { resource_reservation_id: basename(temporary) }) }));
} finally { cleanup(); }
if (qualification && !process.exitCode && cleanupConfirmed) console.log(JSON.stringify(qualification));
