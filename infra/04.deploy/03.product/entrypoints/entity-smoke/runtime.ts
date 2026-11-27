// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.entity-smoke.runtime
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Compose the isolated app with Core identity, lifecycle and the selected PostgreSQL capability.
//   portability: {class: internal, targets: [kanbien-core-platform]}
//   used_by:
//   - id: deploy.plan.entity-smoke-core-platform
//     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md

import { createEntitySmokePersistenceApp, entitySmokeExpiredPurgeJobName, type TestEntityRetentionDelivery } from "@kanbien/app-entity-smoke";
import { systemClock, systemUuidGenerator, type Clock } from "@kanbien/core/shared";
import { recordLifecyclePolicy, recordRetentionPolicyReference } from "@kanbien/core/persistence";
import { createNodePostgreSqlTokenConnectionPool, createPostgreSqlPlatformScheduleStore, type PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { definePlatformApp, platformAppId, platformRouteName, platformObservabilityProfileName, platformCapabilityName } from "@kanbien/platform-contracts";
import { platformReleaseVerificationResponse, resolvePlatformReleaseIdentity } from "@kanbien/platform-server";
import { startPlatformServerProcess } from "@kanbien/platform-server/main";
import { entitySmokeDatabaseSettings } from "./configuration";
import { createEntitySmokePostgreSqlRuntime } from "./postgresql";
import { entitySmokeServerDiagnosticCatalogs, reportEntitySmokeFailure } from "./diagnostics";

export async function runEntitySmokeMain(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const settings = entitySmokeDatabaseSettings(env, "runtime");
  if (!settings.ok) { reportEntitySmokeFailure("startup", "not-started", settings.error); process.exitCode = 1; return; }
  const policy = entitySmokeLifecyclePolicy();
  const pool = createNodePostgreSqlTokenConnectionPool(settings.value.configuration, settings.value.credentials);
  const runtime = createEntitySmokePostgreSqlRuntime(pool, settings.value.configuration);
  const expiredPurgeReminder = { jobName: entitySmokeExpiredPurgeJobName,
    store: createPostgreSqlPlatformScheduleStore({ configuration: settings.value.configuration, pool }) };
  const app = createEntitySmokePersistenceApp({ ...runtime,
    services: { repository: runtime.repository, clock: systemClock, uuidGenerator: systemUuidGenerator, lifecyclePolicy: policy, expiredPurgeReminder,
      ...(runtime.deletionTransaction === undefined ? {} : { deletionTransaction: runtime.deletionTransaction }) } });
  try {
    const started = await startPlatformServerProcess({ apps: [app, releaseApp(env)], env, diagnosticCatalogs: entitySmokeServerDiagnosticCatalogs });
    if (started.ok) return;
    reportEntitySmokeFailure("startup", "not-started", started.error); process.exitCode = 1;
  } catch (cause) {
    reportEntitySmokeFailure("startup", "unknown", cause); process.exitCode = 1;
  }
  // Cleanup has its own failure boundary. A rejected close must not be
  // reclassified as startup failure or cause another pool-close attempt.
  try { await runtime.close(); } catch (closeCause) { reportEntitySmokeFailure("close", "not-assessed", closeCause); }
}

/** The shared scheduler supplies its selected stores and owns closing its pool. */
export function createEntitySmokeSchedulingApp(options: TestEntityRetentionDelivery & {
  readonly pool: PostgreSqlConnectionPool;
  readonly clock: Clock;
  readonly close: () => Promise<void>;
}) {
  const runtime = createEntitySmokePostgreSqlRuntime(options.pool);
  return createEntitySmokePersistenceApp({ readiness: runtime.readiness, close: options.close,
    retentionDelivery: { outbox: options.outbox, schedules: options.schedules },
    services: { repository: runtime.repository, clock: options.clock, uuidGenerator: systemUuidGenerator,
      lifecyclePolicy: entitySmokeLifecyclePolicy() } });
}

function entitySmokeLifecyclePolicy() {
  const reference = required(recordRetentionPolicyReference("entity-smoke.retention"));
  return required(recordLifecyclePolicy({ recoveryWindowMs: 60_000, retentionPolicy: reference, legalHoldCheckRequired: true }));
}

function releaseApp(env: NodeJS.ProcessEnv) {
  const profile = required(platformObservabilityProfileName("entity-smoke-target.release"));
  return definePlatformApp({ id: required(platformAppId("entity-smoke-target")), name: "Entity smoke release identity", mount(registry) {
    required(registry.registerObservabilityProfile({ name: profile, capability: required(platformCapabilityName("entity-smoke-target.release")), action: "verify",
      signals: ["operational_log"], errorClasses: ["test_entity_operation_failed"] }));
    required(registry.registerRoute({ name: required(platformRouteName("entity-smoke-target.release.verify")), method: "GET", path: "/internal/release-verification",
      auth: { kind: "public" }, observability: { kind: "profile", profile },
      handler: { handle: () => ({ status: 200, body: platformReleaseVerificationResponse(resolvePlatformReleaseIdentity(env["PLATFORM_SOURCE_COMMIT_SHA"])) }) } }));
  } });
}
function required<T>(result: { readonly ok: true; readonly value: T } | { readonly ok: false; readonly error: unknown }): T {
  if (!result.ok) throw result.error; return result.value;
}

