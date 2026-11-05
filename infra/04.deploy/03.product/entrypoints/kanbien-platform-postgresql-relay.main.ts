// One fixed relational smoke acceptance and relay. It writes one opaque work
// item only when the database is otherwise empty, sends one minimal envelope,
// records publication, and exits.
import { reportTargetConfigurationError, targetEnvironmentConfigurationRecord } from "./kanbien-platform-configuration-diagnostics";
import { reportKanbienPlatformDeliveryFailure, reportKanbienPlatformQueueDiagnostic, reportKanbienPlatformPersistenceDeliveryDiagnostic, targetDeliveryErrorSource, targetDeliveryDisposition, type KanbienPlatformDeliveryBoundaryDetail } from "./kanbien-platform-delivery-diagnostics";
import { createKanbienPlatformPersistenceTransitionObserver } from "./kanbien-platform-persistence";
import { noopMetrics } from "@kanbien/core/monitoring";

import { acceptPlatformSmokeWorkItem, platformSmokeWorkItemId } from "@kanbien/app-platform-smoke";
import { causationId, isoDateTimeFromDate } from "@kanbien/core/shared";
import { createAwsSdkPlatformSqsQueue } from "@kanbien/platform-adapter-aws-queue-sqs";
import { createPlatformOutboxRelay, platformPersistenceLeaseOwner } from "@kanbien/platform-persistence";
import { createPostgreSqlPlatformOutboxStore } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { createKanbienPlatformPostgreSqlSmokePersistence } from "./kanbien-platform-postgresql-persistence";
import { reportKanbienPlatformPostgreSqlDiagnostic } from "./kanbien-platform-postgresql-operation-diagnostics";
import {
  closePool,
  configurationFromEnvironment,
  connectionPool,
  secretFromEnvironment,
  writeOutcome,
} from "./kanbien-platform-postgresql-task";

const workItemValue = "postgresql-stage6-smoke-20260926-a";

async function main(): Promise<void> {
  let pool;
  let boundary: KanbienPlatformDeliveryBoundaryDetail["boundary"] | undefined;
  let preciseFailure: { readonly error: Error } | undefined;
  function fail(message: string, condition: KanbienPlatformDeliveryBoundaryDetail["condition"], source?: unknown, disposition?: KanbienPlatformDeliveryBoundaryDetail["disposition"]): never {
    const error = new Error(message);
    preciseFailure = { error };
    reportKanbienPlatformDeliveryFailure({ workload: "relational-relay", boundary: boundary ?? "run-once", condition, effect: "work-outcome-unknown",
      ...(disposition === undefined ? {} : { disposition }) }, source);
    throw error;
  }
  try {
    const configuration = configurationFromEnvironment();
    const runtime = secretFromEnvironment("RELATIONAL_RUNTIME_SECRET_JSON");
    const queueUrl = requiredEnvironment("RELATIONAL_SMOKE_QUEUE_URL");
    pool = connectionPool(runtime, configuration.runtimeSecretArn, configuration.schema);
    const persistence = createKanbienPlatformPostgreSqlSmokePersistence({
      configuration: { ...configurationFromEnvironmentToAdapter(configuration, runtime), runtimeCredentialSecretReference: configuration.runtimeSecretArn },
      pool,
    }, { onDiagnostic: reportKanbienPlatformPostgreSqlDiagnostic });
    const identifier = platformSmokeWorkItemId(workItemValue);
    const cause = causationId("postgresql-stage6-cause-20260926-a");
    boundary = "identity-check";
    if (!identifier.ok) fail("RELATIONAL_TASK_FIXED_IDENTIFIER_INVALID", "returned-failure", targetDeliveryErrorSource(identifier));
    boundary = "acceptance";
    const accepted = await acceptPlatformSmokeWorkItem({ id: identifier.value, acceptedAt: isoDateTimeFromDate(new Date()), causationId: cause }, persistence, {
      onDiagnostic: (record) => reportKanbienPlatformPersistenceDeliveryDiagnostic(record, "acceptance"),
    });
    if (!accepted.ok) fail("RELATIONAL_TASK_ACCEPTANCE_FAILED", "returned-failure", targetDeliveryErrorSource(accepted));
    boundary = "owner-validation";
    const owner = platformPersistenceLeaseOwner("kanbien-postgresql-relay-a");
    if (!owner.ok) fail("RELATIONAL_TASK_OWNER_INVALID", "invalid-owner", targetDeliveryErrorSource(owner));
    const observed = createKanbienPlatformPersistenceTransitionObserver({ executionContext: "worker", metrics: noopMetrics });
    const relay = createPlatformOutboxRelay({
      outbox: createPostgreSqlPlatformOutboxStore({ configuration: configurationFromEnvironmentToAdapter(configuration, runtime), pool,
        onDiagnostic: (record) => reportKanbienPlatformPersistenceDeliveryDiagnostic(record, "relay") }),
      queue: createAwsSdkPlatformSqsQueue({ queueUrl, region: "eu-west-1",
        onDiagnostic: (record, context) => reportKanbienPlatformQueueDiagnostic("relational-relay", record, context) }),
      owner: owner.value,
      leaseDurationMs: 90_000,
      clock: { now: () => new Date() },
      ...(observed.ok ? { observer: observed.value } : {}),
    });
    boundary = "run-once";
    const result = await relay.runOnce();
    if (!result.ok) fail("RELATIONAL_TASK_RELAY_FAILED", "returned-failure", targetDeliveryErrorSource(result));
    const disposition = result.value.status;
    if (disposition !== "published") fail("RELATIONAL_TASK_RELAY_FAILED", "unexpected-disposition", undefined, targetDeliveryDisposition(disposition));
    boundary = "summary";
    writeOutcome("relay_completed", "succeeded");
  } catch (error) {
    if (boundary !== undefined && (preciseFailure === undefined || preciseFailure.error !== error)) reportKanbienPlatformDeliveryFailure({ workload: "relational-relay", boundary, condition: "threw", effect: "work-outcome-unknown" }, error);
    reportTargetConfigurationError(error);
    writeOutcome("relay_completed", "failed");
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
  if (value === undefined || value.length === 0) throw Object.assign(new Error("RELATIONAL_TASK_QUEUE_CONFIGURATION_INVALID"), { diagnosticRecord: targetEnvironmentConfigurationRecord("RELATIONAL_SMOKE_QUEUE_URL", value === undefined ? "missing" : "empty") });
  return value;
}

void main();
