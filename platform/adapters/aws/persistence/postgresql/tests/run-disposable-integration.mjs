import { randomBytes, randomInt } from "node:crypto";
import { spawnSync } from "node:child_process";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const docker = process.platform === "win32" ? "docker.exe" : "docker";
const containerName = `kanbien-postgresql-stage3-${randomBytes(8).toString("hex")}`;
const password = randomBytes(24).toString("base64url");
const fixtureDirectory = mkdtempSync(join(tmpdir(), "kanbien-postgresql-stage3-"));
const fixtureEnvironment = join(fixtureDirectory, "fixture.env");

class FixtureError extends Error {
  constructor(category) {
    super(category);
    this.category = category;
  }
}

let cleanup = () => {};
try {
  writeFixtureEnvironment();
  console.log("PostgreSQL disposable fixture preparation started.");
  const fixture = dockerAvailable() ? startDockerFixture() : startLocalFixture();
  cleanup = fixture.cleanup;
  console.log("PostgreSQL disposable fixture is ready for semantic assertions.");
  runIntegration(fixture.port);
  console.log("PostgreSQL disposable integration proof passed.");
} catch (error) {
  const category = error instanceof FixtureError ? error.category : "fixture-unclassified-failure";
  console.error(`PostgreSQL disposable integration proof failed safely: ${category}.`);
  process.exitCode = 1;
} finally {
  try {
    cleanup();
    console.log("PostgreSQL disposable fixture engine cleanup passed.");
  } catch {
    console.error("PostgreSQL disposable integration cleanup failed without exposing fixture details.");
    process.exitCode = 1;
  }
  rmSync(fixtureDirectory, { recursive: true, force: true });
  console.log("PostgreSQL disposable fixture directory cleanup passed.");
}

function writeFixtureEnvironment() {
  writeFileSync(fixtureEnvironment, `POSTGRES_PASSWORD=${password}\n`, { encoding: "utf8", mode: 0o600 });
  chmodSync(fixtureEnvironment, 0o600);
}

function startDockerFixture() {
  let containerStarted = false;
  try {
    const started = runDocker([
      "run", "--detach", "--rm", "--name", containerName,
      "--tmpfs", "/var/lib/postgresql/data:rw,noexec,nosuid,size=256m",
      "--env-file", fixtureEnvironment,
      "--env", "POSTGRES_DB=postgres",
      "--publish", "127.0.0.1::5432",
      "postgres:17.11-bookworm",
    ], 60_000);
    if (started.status !== 0) throw new FixtureError("container-start-failed");
    containerStarted = true;
    const port = publishedDockerPort();
    waitForDockerReady();
    return {
      port,
      cleanup() {
        stopDockerFixture();
      },
    };
  } catch (error) {
    if (containerStarted) stopDockerFixture();
    throw error;
  }
}

function stopDockerFixture() {
  const stopped = runDocker(["rm", "--force", containerName], 15_000);
  if (stopped.status !== 0) throw new FixtureError("container-cleanup-failed");
}

function startLocalFixture() {
  const binaries = localPostgreSqlBinaries();
  if (binaries === undefined) throw new FixtureError("local-engine-unavailable");
  const dataDirectory = join(fixtureDirectory, "data");
  const socketDirectory = join(fixtureDirectory, "socket");
  const initializationPassword = join(fixtureDirectory, "initialization-password");
  mkdirSync(socketDirectory, { mode: 0o700 });
  chmodSync(socketDirectory, 0o700);
  writeFileSync(initializationPassword, password, { encoding: "utf8", mode: 0o600 });
  chmodSync(initializationPassword, 0o600);
  console.log("PostgreSQL disposable local engine initialization started.");
  const initialized = runCommand(binaries.initdb, [
    "--no-locale",
    "--encoding=UTF8",
    "--auth-host=scram-sha-256",
    "--auth-local=trust",
    "--username=postgres",
    "--pwfile", initializationPassword,
    "--pgdata", dataDirectory,
  ], 60_000);
  rmSync(initializationPassword, { force: true });
  if (initialized.status !== 0) throw new FixtureError("local-engine-initialization-failed");
  console.log("PostgreSQL disposable local engine initialization passed.");
  for (let attempt = 0; attempt < 8; attempt += 1) {
    const port = randomLoopbackPort();
    console.log("PostgreSQL disposable local engine startup attempt started.");
    const started = runCommand(binaries.pgCtl, [
      "--pgdata", dataDirectory,
      "--options", `-h 127.0.0.1 -p ${port} -k ${socketDirectory}`,
      "start",
    ], 10_000);
    if (started.status !== 0) {
      const category = localStartFailureCategory(started);
      if (category === "local-engine-port-collision") continue;
      throw new FixtureError(category);
    }
    console.log("PostgreSQL disposable local engine startup attempt passed.");
    if (!localEngineReady(binaries.pgIsReady, port)) {
      stopLocalEngine(binaries.pgCtl, dataDirectory, { allowAbsent: true });
      continue;
    }
    console.log("PostgreSQL disposable local engine readiness passed.");
    return {
      port,
      cleanup() {
        stopLocalEngine(binaries.pgCtl, dataDirectory);
      },
    };
  }
  throw new FixtureError("local-engine-start-failed");
}

function localPostgreSqlBinaries() {
  const root = "/usr/lib/postgresql";
  if (!existsSync(root)) return undefined;
  const versions = readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^\d+$/.test(entry.name))
    .map((entry) => Number(entry.name))
    .sort((left, right) => right - left);
  for (const version of versions) {
    const bin = join(root, String(version), "bin");
    const initdb = join(bin, "initdb");
    const pgCtl = join(bin, "pg_ctl");
    const pgIsReady = join(bin, "pg_isready");
    if ([initdb, pgCtl, pgIsReady].every((candidate) => existsSync(candidate) && statSync(candidate).isFile())) {
      return { initdb, pgCtl, pgIsReady };
    }
  }
  return undefined;
}

function randomLoopbackPort() {
  return randomInt(49_152, 65_535);
}

function localStartFailureCategory(result) {
  const errorText = `${result.stdout ?? ""}\n${result.stderr ?? ""}`;
  if (/address already in use|could not bind/i.test(errorText)) return "local-engine-port-collision";
  if (/could not create any tcp\/ip sockets|permission denied/i.test(errorText)) return "local-engine-loopback-bind-rejected";
  if (result.error !== undefined) return "local-engine-executable-failure";
  return "local-engine-start-failed";
}

function localEngineReady(pgIsReady, port) {
  for (let attempt = 0; attempt < 12; attempt += 1) {
    const result = runCommand(pgIsReady, ["--host", "127.0.0.1", "--port", String(port), "--username", "postgres", "--dbname", "postgres", "--timeout", "1"], 2_000);
    if (result.status === 0) return true;
  }
  return false;
}

function stopLocalEngine(pgCtl, dataDirectory, options = { allowAbsent: false }) {
  const stopped = runCommand(pgCtl, ["--pgdata", dataDirectory, "--wait", "--timeout", "5", "stop", "--mode", "immediate"], 10_000);
  if (stopped.status === 0) return;
  if (options.allowAbsent && /no server running/i.test(`${stopped.stdout ?? ""}\n${stopped.stderr ?? ""}`)) return;
  throw new FixtureError("local-engine-cleanup-failed");
}

function runIntegration(port) {
  const result = spawnSync(
    process.execPath,
    ["platform/adapters/aws/persistence/postgresql/tests/run-local-integration-tests.mjs"],
    {
      cwd: process.cwd(),
      stdio: "inherit",
      env: {
        ...localFixtureEnvironment(),
        POSTGRESQL_INTEGRATION_HOST: "127.0.0.1",
        POSTGRESQL_INTEGRATION_PORT: String(port),
        POSTGRESQL_INTEGRATION_DATABASE: "postgres",
        POSTGRESQL_INTEGRATION_PASSWORD_FILE: fixtureEnvironment,
      },
      timeout: 20_000,
    },
  );
  if (result.error?.code === "ETIMEDOUT") throw new FixtureError("integration-assertions-timed-out");
  if (result.status !== 0 || result.signal !== null || result.error !== undefined) {
    throw new FixtureError("integration-assertions-failed");
  }
}

function dockerAvailable() {
  const result = runDocker(["version", "--format", "{{.Server.Version}}"], 5_000);
  return result.status === 0 && result.stdout.trim().length > 0;
}

function publishedDockerPort() {
  const result = runDocker(["port", containerName, "5432/tcp"], 10_000);
  if (result.status !== 0) throw new FixtureError("container-port-unavailable");
  const address = result.stdout.trim().split(/\s+/)[0];
  const port = Number(address?.split(":").at(-1));
  if (!Number.isInteger(port) || port < 1 || port > 65_535) throw new FixtureError("container-port-invalid");
  return port;
}

function waitForDockerReady() {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const result = runDocker(["exec", containerName, "pg_isready", "--quiet", "--username", "postgres", "--dbname", "postgres"], 5_000);
    if (result.status === 0) return;
  }
  throw new FixtureError("container-readiness-failed");
}

function runDocker(args, timeout) {
  return runCommand(docker, args, timeout);
}

function runCommand(command, args, timeout) {
  return spawnSync(command, args, {
    cwd: process.cwd(),
    env: localFixtureEnvironment(),
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    timeout,
  });
}

function localFixtureEnvironment() {
  const environment = { ...process.env };
  for (const key of [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_PROFILE",
    "AWS_SHARED_CREDENTIALS_FILE",
    "AWS_CONFIG_FILE",
  ]) {
    delete environment[key];
  }
  return environment;
}
