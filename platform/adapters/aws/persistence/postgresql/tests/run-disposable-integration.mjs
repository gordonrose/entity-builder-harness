import { randomBytes } from "node:crypto";
import { spawnSync } from "node:child_process";
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const docker = process.platform === "win32" ? "docker.exe" : "docker";
const name = `kanbien-postgresql-stage3-${randomBytes(8).toString("hex")}`;
const password = randomBytes(24).toString("base64url");
const fixtureDirectory = mkdtempSync(join(tmpdir(), "kanbien-postgresql-stage3-"));
const fixtureEnvironment = join(fixtureDirectory, "container.env");

if (!dockerAvailable()) {
  console.error("PostgreSQL disposable integration proof is blocked: the local Docker daemon is unavailable.");
  rmSync(fixtureDirectory, { recursive: true, force: true });
  process.exitCode = 75;
} else {
  let containerStarted = false;
  try {
    writeFileSync(fixtureEnvironment, `POSTGRES_PASSWORD=${password}\n`, { encoding: "utf8", mode: 0o600 });
    chmodSync(fixtureEnvironment, 0o600);
    const started = runDocker([
      "run", "--detach", "--rm", "--name", name,
      "--tmpfs", "/var/lib/postgresql/data:rw,noexec,nosuid,size=256m",
      "--env-file", fixtureEnvironment,
      "--env", "POSTGRES_DB=postgres",
      "--publish", "127.0.0.1::5432",
      "postgres:17.11-bookworm",
    ], 60_000);
    if (started.status !== 0) throw new Error("The disposable PostgreSQL container did not start.");
    containerStarted = true;
    const port = publishedPort();
    waitUntilReady();
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
      },
    );
    process.exitCode = result.status ?? 1;
  } catch {
    console.error("PostgreSQL disposable integration proof failed without exposing fixture details.");
    process.exitCode = 1;
  } finally {
    if (containerStarted) {
      runDocker(["rm", "--force", name], 15_000);
    }
    rmSync(fixtureDirectory, { recursive: true, force: true });
  }
}

function dockerAvailable() {
  const result = runDocker(["version", "--format", "{{.Server.Version}}"], 5_000);
  return result.status === 0 && result.stdout.trim().length > 0;
}

function publishedPort() {
  const result = runDocker(["port", name, "5432/tcp"], 10_000);
  if (result.status !== 0) throw new Error("The disposable PostgreSQL port was not available.");
  const address = result.stdout.trim().split(/\s+/)[0];
  const port = Number(address?.split(":").at(-1));
  if (!Number.isInteger(port) || port < 1 || port > 65_535) throw new Error("The disposable PostgreSQL port was invalid.");
  return port;
}

function waitUntilReady() {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const result = runDocker(["exec", name, "pg_isready", "--quiet", "--username", "postgres", "--dbname", "postgres"], 5_000);
    if (result.status === 0) return;
  }
  throw new Error("The disposable PostgreSQL engine did not become ready.");
}

function runDocker(args, timeout) {
  return spawnSync(docker, args, {
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
