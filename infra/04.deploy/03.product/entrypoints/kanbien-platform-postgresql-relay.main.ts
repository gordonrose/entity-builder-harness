// One fixed relational smoke acceptance and relay. It writes one opaque work
// item only when the database is otherwise empty, sends one minimal envelope,
// records publication, and exits.

import { acceptPlatformSmokeWorkItem, platformSmokeWorkItemId } from "@kanbien/app-platform-smoke";
import { causationId, isoDateTimeFromDate } from "@kanbien/core/shared";
import { createAwsSdkPlatformSqsQueue } from "@kanbien/platform-adapter-aws-queue-sqs";
import { createPlatformOutboxRelay, platformPersistenceLeaseOwner } from "@kanbien/platform-persistence";
import { createPostgreSqlPlatformOutboxStore } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { createKanbienPlatformPostgreSqlSmokePersistence } from "./kanbien-platform-postgresql-persistence";
import {
  closePool,
  relationalTaskMode,
  verifyRelationalTaskPreflight,
  writePreflightOutcome,
  configurationFromEnvironment,
  connectionPool,
  secretFromEnvironment,
  writeOutcome,
} from "./kanbien-platform-postgresql-task";

const workItemValue = "postgresql-stage6-smoke-20260926-a";

async function main(): Promise<void> {
  let pool;
  let preflight = process.argv.slice(2).includes("--preflight");
  try {
    preflight = relationalTaskMode() === "preflight";
    const configuration = configurationFromEnvironment();
    const runtime = secretFromEnvironment("RELATIONAL_RUNTIME_SECRET_JSON");
    const queueUrl = requiredEnvironment("RELATIONAL_SMOKE_QUEUE_URL");
    pool = connectionPool(runtime, configuration.runtimeSecretArn, configuration.schema);
    if (preflight) {
      await verifyRelationalTaskPreflight(pool, "relay", runtime.username);
      writePreflightOutcome("relay", "passed");
      return;
    }
    const persistence = createKanbienPlatformPostgreSqlSmokePersistence({
      configuration: { ...configurationFromEnvironmentToAdapter(configuration, runtime), runtimeCredentialSecretReference: configuration.runtimeSecretArn },
      pool,
    });
    const identifier = platformSmokeWorkItemId(workItemValue);
    const cause = causationId("postgresql-stage6-cause-20260926-a");
    if (!identifier.ok) throw new Error("RELATIONAL_TASK_FIXED_IDENTIFIER_INVALID");
    const accepted = await acceptPlatformSmokeWorkItem({ id: identifier.value, acceptedAt: isoDateTimeFromDate(new Date()), causationId: cause }, persistence);
    if (!accepted.ok) throw new Error("RELATIONAL_TASK_ACCEPTANCE_FAILED");
    const owner = platformPersistenceLeaseOwner("kanbien-postgresql-relay-a");
    if (!owner.ok) throw new Error("RELATIONAL_TASK_OWNER_INVALID");
    const relay = createPlatformOutboxRelay({
      outbox: createPostgreSqlPlatformOutboxStore({ configuration: configurationFromEnvironmentToAdapter(configuration, runtime), pool }),
      queue: createAwsSdkPlatformSqsQueue({ queueUrl, region: "eu-west-1" }),
      owner: owner.value,
      leaseDurationMs: 90_000,
      clock: { now: () => new Date() },
    });
    const result = await relay.runOnce();
    if (!result.ok || result.value.status !== "published") throw new Error("RELATIONAL_TASK_RELAY_FAILED");
    writeOutcome("relay_completed", "succeeded");
  } catch {
    if (preflight) writePreflightOutcome("relay", "failed");
    else writeOutcome("relay_completed", "failed");
    process.exitCode = 1;
  } finally {
    await closePool(pool);
  }
}

function configurationFromEnvironmentToAdapter(
  configuration: ReturnType<typeof configurationFromEnvironment>,
  runtime: ReturnType<typeof secretFromEnvironment>,
) {
  return {
    host: runtime.host,
    port: runtime.port,
    database: configuration.database,
    schema: configuration.schema,
    runtimeCredentialSecretReference: configuration.runtimeSecretArn,
    maximumPoolSize: 2,
    connectionTimeoutMs: 10_000,
    idleTimeoutMs: 10_000,
    statementTimeoutMs: 15_000,
    tls: { mode: "verify-full" as const, certificateAuthoritySource: "injected" as const },
  };
}

function requiredEnvironment(name: string): string {
  const value = process.env[name];
  if (value === undefined || value.length === 0) throw new Error("RELATIONAL_TASK_QUEUE_CONFIGURATION_INVALID");
  return value;
}

void main();
