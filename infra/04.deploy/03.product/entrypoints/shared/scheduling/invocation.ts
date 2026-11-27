// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: infra.04-deploy.03-product.entrypoint.shared-scheduling-invocation
//   version: 1
//   status: draft
//   created_on: "2026-11-27"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.scheduling
//   disciplines: [architecture, security, sre]
//   kind: code
//   purpose: Own checked scheduler invocation resources and sanitize failures before the Lambda runtime boundary.
//   portability: { class: internal, targets: [kanbien-core-platform, entity-smoke] }
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-core-server-persistence-scheduling-dispatch-handler
//     path: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-scheduling-dispatch.handler.ts
//   - id: infra.04-deploy.03-product.entrypoint.kanbien-entity-smoke-scheduling-worker-handler
//     path: infra/04.deploy/03.product/entrypoints/kanbien-entity-smoke-scheduling-worker.handler.ts

import { GetQueueAttributesCommand, SQSClient } from "@aws-sdk/client-sqs";
import { createHash } from "node:crypto";
import { Resolver } from "node:dns/promises";
import { isIPv4 } from "node:net";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { systemClock, systemUuidGenerator, type Clock, type UuidGenerator } from "@kanbien/core/shared";
import type { Logger } from "@kanbien/core/logging";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformContractDiagnosticCatalog, type PlatformApp, type PlatformDiagnosticCatalog, type PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { platformConfigDiagnosticCatalog } from "@kanbien/platform-config";
import { platformHealthDiagnosticCatalog } from "@kanbien/platform-health";
import { platformRuntimeDiagnosticCatalog } from "@kanbien/platform-runtime";
import { platformWorkerDiagnosticCatalog } from "@kanbien/platform-workers";
import { platformPersistenceDiagnosticCatalog } from "@kanbien/platform-persistence";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import { createPlatformDiagnosticReporter, createPlatformSafeLogger, platformObservabilityDiagnosticCatalog,
  reportPlatformDiagnostic, reportPlatformErrorDiagnostic } from "@kanbien/platform-observability";
import { createNodePostgreSqlTokenConnectionPool, createPostgreSqlPlatformOutboxStore,
  createPostgreSqlPlatformProcessingStore, createPostgreSqlPlatformScheduleStore,
  type PostgreSqlConnectionPool } from "@kanbien/platform-adapter-aws-persistence-postgresql";
import { sqsDiagnosticCatalog, type PlatformSqsCommandClient } from "@kanbien/platform-adapter-aws-queue-sqs";
import { createPlatformLambdaContinuation, lambdaRuntimeDiagnosticCatalog, type PlatformLambdaContext } from "@kanbien/platform-adapter-aws-runtime-lambda";
import { persistenceConfigurationDiagnosticCatalog } from "../persistence/configuration";
import { schedulingConfiguration, type SchedulingConfiguration, type SchedulingPurpose, type SchedulingScopeConfiguration } from "./configuration";
import { schedulingInvocationRecord, schedulingPreflightRecord, schedulingTargetDiagnosticCatalog,
  type SchedulingInvocationDetail, type SchedulingPreflightDetail } from "./diagnostics";
import { createSchedulingComposition, schedulingRuntimeBudgets, type SchedulingAppResources, type SchedulingComposedRuntime } from "./composition";

export interface SchedulingTargetBinding extends SchedulingScopeConfiguration {
  readonly purpose: SchedulingPurpose;
  readonly appDiagnosticCatalogs: readonly PlatformDiagnosticCatalog[];
  readonly createApp: (resources: SchedulingAppResources) => PlatformApp;
}
export interface SchedulingInvocationDependencies {
  readonly env?: NodeJS.ProcessEnv;
  readonly clock?: Clock;
  readonly uuidGenerator?: UuidGenerator;
  readonly logger?: Logger;
  readonly readCertificate?: (path: string) => string;
  readonly createPool?: typeof createNodePostgreSqlTokenConnectionPool;
  readonly createClient?: (configuration: SchedulingConfiguration["queue"]) => PlatformSqsCommandClient & { destroy(): void };
  readonly resolveQueueAddresses?: (hostname: string) => Promise<readonly string[]>;
}
const builtinCatalogs = [coreDiagnosticCatalog, platformContractDiagnosticCatalog, platformConfigDiagnosticCatalog,
  platformHealthDiagnosticCatalog, platformRuntimeDiagnosticCatalog, platformWorkerDiagnosticCatalog, platformObservabilityDiagnosticCatalog];
const extraCatalogs = [platformPersistenceDiagnosticCatalog, platformSecurityDiagnosticCatalog, persistenceConfigurationDiagnosticCatalog,
  sqsDiagnosticCatalog, lambdaRuntimeDiagnosticCatalog, schedulingTargetDiagnosticCatalog];

/** Fresh invocation resources keep closures independent and make cleanup observable and finite. */
export function createSchedulingTargetHandler(binding: SchedulingTargetBinding, dependencies: SchedulingInvocationDependencies = {}) {
  return async (event: unknown, context: PlatformLambdaContext): Promise<unknown> => {
    let phase: SchedulingInvocationDetail["phase"] = "configuration";
    let reporter: PlatformDiagnosticReporter | undefined;
    let pool: PostgreSqlConnectionPool | undefined;
    let client: (PlatformSqsCommandClient & { destroy(): void }) | undefined;
    let runtime: SchedulingComposedRuntime | undefined;
    let poolClose: Promise<void> | undefined;
    let completed = false;
    let preflightCheck: SchedulingPreflightDetail["check"] | undefined;
    let preflightObservation: SchedulingPreflightDetail["observation"] = "dependency-threw";
    const requirePreflight = (condition: boolean) => {
      if (!condition) { preflightObservation = "predicate-rejected"; throw new Error("SCHEDULING_PREFLIGHT_REJECTED"); }
    };
    const closePool = (): Promise<void> => poolClose ??= Promise.resolve().then(() => pool?.end());
    const report = (error: unknown, at: SchedulingInvocationDetail["phase"], effect: SchedulingInvocationDetail["effect"]) => {
      try {
        if (reporter === undefined) return;
        const diagnosticContext = { capability: "scheduling", operation: binding.purpose,
          stage: at === "configuration" ? "configuration" : at === "shutdown" ? "shutdown" : "request" } as const;
        reportPlatformErrorDiagnostic(reporter, error, diagnosticContext);
        // Retained target configuration readers expose a selected `diagnostic` field.
        // Project only that own data field; never enumerate an exception or serialize its cause.
        const selected = typeof error === "object" && error !== null ? Object.getOwnPropertyDescriptor(error, "diagnostic") : undefined;
        if (selected && "value" in selected) reportPlatformDiagnostic(reporter, selected.value as DiagnosticRecord, diagnosticContext);
        reportPlatformDiagnostic(reporter, schedulingInvocationRecord({ operation: binding.purpose, phase: at, effect }), diagnosticContext);
      } catch { /* Evidence cannot change durable work or expose a provider exception. */ }
    };
    try {
      const clock = dependencies.clock ?? systemClock;
      const logger = createPlatformSafeLogger(dependencies.logger ?? { write(record) { console.log(JSON.stringify(record)); } });
      const catalogs = [...builtinCatalogs, ...extraCatalogs, ...binding.appDiagnosticCatalogs];
      try { reporter = createPlatformDiagnosticReporter({ catalogs, logger, clock }); }
      catch (error) {
        reporter = createPlatformDiagnosticReporter({ catalogs: [coreDiagnosticCatalog, platformContractDiagnosticCatalog, schedulingTargetDiagnosticCatalog], logger, clock });
        throw error;
      }
      const diagnosticDefinitions = catalogs.flatMap(catalog => catalog.definitions);
      const diagnostics = { diagnosticDefinitions, onDiagnostic: (record: DiagnosticRecord) => reportPlatformDiagnostic(reporter!, record,
        { capability: "scheduling", operation: binding.purpose, stage: "request" }) };
      const environment = dependencies.env ?? process.env;
      const configuration = schedulingConfiguration(environment, binding, binding.purpose, dependencies.readCertificate);
      const requestedKind = typeof event === "object" && event !== null ? Object.getOwnPropertyDescriptor(event, "kind") : undefined;
      const preflight = requestedKind !== undefined;
      const invocation = context as PlatformLambdaContext & { awsRequestId?: string; invokedFunctionArn?: string;
        clientContext?: { custom?: { scheduling_preflight_operation_id?: unknown; scheduling_proof_operation_id?: unknown } } };
      let sourceRevision: unknown;
      let operationId: unknown;
      if (preflight) {
        preflightCheck = "source-revision";
        sourceRevision = environment["PLATFORM_SOURCE_COMMIT_SHA"];
        preflightCheck = "operation-identity";
        operationId = invocation.clientContext?.custom?.scheduling_preflight_operation_id;
      } else {
        try { sourceRevision = environment["PLATFORM_SOURCE_COMMIT_SHA"]; }
        catch { /* Optional metadata cannot prevent normal execution. */ }
      }
      // Optional observation metadata must never create a new execution failure.
      // Production evidence requires the real numeric version and request ID;
      // events cannot supply either. Preflight retains its stricter predicates.
      let observationIdentity: { source_revision: string; request_id: string; function_arn: string } | undefined;
      try {
        const request = invocation.awsRequestId, arn = invocation.invokedFunctionArn;
        if (typeof sourceRevision === "string" && /^[a-f0-9]{40}$/.test(sourceRevision)
          && typeof request === "string" && /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/.test(request)
          && typeof arn === "string" && /^arn:aws:lambda:[a-z0-9-]+:[0-9]{12}:function:[A-Za-z0-9_-]+:[1-9][0-9]*$/.test(arn)) {
          observationIdentity = { source_revision: sourceRevision, request_id: request, function_arn: arn };
        }
      } catch { /* Missing evidence is not permission to replay business work. */ }
      // A reserved normal proof invocation can fail after changing durable work.
      // Its start marker correlates the original AWS request after a lost response;
      // it neither selects work nor authorizes an invocation or a retry.
      if (!preflight && binding.purpose === "dispatch" && observationIdentity !== undefined) {
        try {
          const proofOperation = invocation.clientContext?.custom?.scheduling_proof_operation_id;
          if (typeof proofOperation === "string" && /^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/.test(proofOperation)) {
            logger.write({ level: "info", message: "Scheduling proof invocation.", fields: { scheduling_invocation: {
              schema: "kanbien/scheduling-proof-invocation/v1", operation_id: proofOperation,
              ...observationIdentity, checked_at: clock.now().toISOString(),
            } } });
          }
        } catch { /* Optional evidence cannot prevent or repeat the normal dispatcher. */ }
      }
      if (preflight) {
        preflightCheck = "request-shape";
        requirePreflight(!Array.isArray(event) && Object.keys(event as object).length === 1
          && "value" in requestedKind && requestedKind.value === "scheduling-preflight/v1");
        preflightCheck = "source-revision";
        requirePreflight(typeof sourceRevision === "string" && /^[a-f0-9]{40}$/.test(sourceRevision));
        preflightCheck = "request-identity";
        requirePreflight(typeof invocation.awsRequestId === "string" && /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/.test(invocation.awsRequestId));
        preflightCheck = "function-identity";
        requirePreflight(typeof invocation.invokedFunctionArn === "string"
          && /^arn:aws:lambda:[a-z0-9-]+:[0-9]{12}:function:[A-Za-z0-9_-]+:[1-9][0-9]*$/.test(invocation.invokedFunctionArn));
        preflightCheck = "operation-identity";
        requirePreflight(typeof operationId === "string" && /^[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/.test(operationId));
        preflightCheck = "time-budget";
        // Connect + BEGIN/SELECT/ROLLBACK + DNS + SQS + cleanup fit this reserve.
        requirePreflight(createPlatformLambdaContinuation(context, 30_000)());
      }
      phase = "resources";
      if (preflight) preflightCheck = "database-connection";
      pool = (dependencies.createPool ?? createNodePostgreSqlTokenConnectionPool)(configuration.persistence, configuration.credentials, diagnostics);
      const openClient = () => dependencies.createClient === undefined ? new SQSClient({ region: configuration.queue.region, maxAttempts: 1,
        requestHandler: { connectionTimeout: schedulingRuntimeBudgets.queueConnectionTimeoutMs,
          requestTimeout: schedulingRuntimeBudgets.queueRequestTimeoutMs, throwOnRequestTimeout: true } }) as unknown as PlatformSqsCommandClient & { destroy(): void }
        : dependencies.createClient(configuration.queue);
      if (preflight) {
        preflightCheck = "database-connection";
        const connection = await pool.connect();
        let rolledBack = false;
        try {
          await connection.query({ text: "BEGIN READ ONLY" });
          preflightCheck = "database-identity";
          const tables = ["platform_schedule", "platform_outbox", ...(binding.purpose === "worker" ? ["platform_processing"] : [])];
          const selected = await connection.query<{ username: string; session_username: string; database: string; allowed: boolean }>({
            text: "SELECT current_user AS username, session_user AS session_username, current_database() AS database, " +
              "has_schema_privilege(current_user, $1, 'USAGE') AND NOT has_schema_privilege(current_user, $1, 'CREATE') " +
              "AND (SELECT bool_and(has_table_privilege(current_user, format('%I.%I', $1, name), 'SELECT')) FROM unnest($2::text[]) AS name) AS allowed",
            values: [configuration.persistence.schema, tables],
          });
          requirePreflight(selected.rows.length === 1 && selected.rows[0]?.database === configuration.persistence.database);
          preflightCheck = "database-user";
          requirePreflight(selected.rows[0]?.username === configuration.credentials.username);
          preflightCheck = "database-session";
          requirePreflight(selected.rows[0]?.session_username === configuration.credentials.username);
          preflightCheck = "database-privileges";
          requirePreflight(selected.rows[0]?.allowed === true);
          preflightCheck = "database-rollback";
          await connection.query({ text: "ROLLBACK" }); rolledBack = true;
        } finally {
          try { if (!rolledBack) await connection.query({ text: "ROLLBACK" }); }
          finally { connection.release(); }
        }
        let queue: { arn: string; address_count: number; address_sha256: string } | null = null;
        if (binding.purpose === "worker") {
          preflightCheck = "queue-dns";
          const hostname = new URL(configuration.queue.queueUrl).hostname;
          const addresses = await (dependencies.resolveQueueAddresses ?? (host => new Resolver({ timeout: 2_000, tries: 1 }).resolve4(host)))(hostname);
          requirePreflight(Array.isArray(addresses) && addresses.length > 0 && addresses.length <= 16 && addresses.every(address => typeof address === "string" && isIPv4(address)));
          const canonical = [...new Set(addresses)].sort();
          preflightCheck = "queue-identity";
          client = openClient();
          const observed = await client.send(new GetQueueAttributesCommand({ QueueUrl: configuration.queue.queueUrl, AttributeNames: ["QueueArn"] })) as { Attributes?: { QueueArn?: string } };
          requirePreflight(observed?.Attributes?.QueueArn === configuration.queue.queueArn);
          queue = { arn: configuration.queue.queueArn, address_count: canonical.length,
            address_sha256: createHash("sha256").update(JSON.stringify(canonical)).digest("hex") };
        }
        preflightCheck = "cleanup";
        await closePool();
        // A connection proof is unsuccessful if its cleanup failed; ordinary job
        // completion retains its existing durable-result cleanup semantics below.
        const closingClient = client; client = undefined; closingClient?.destroy();
        completed = true;
        const result = { schema: "kanbien/scheduling-runtime-preflight/v1", purpose: binding.purpose, operation_id: operationId,
          source_revision: sourceRevision, request_id: invocation.awsRequestId, function_arn: invocation.invokedFunctionArn,
          checked_at: clock.now().toISOString(), database: { name: configuration.persistence.database,
            schema: configuration.persistence.schema, username: configuration.credentials.username }, queue };
        // This selected bounded receipt enables original-invocation readback
        // after a lost response. Missing logs remain unknown, never permission to
        // resubmit an invocation. No event, address list or provider error is logged.
        logger.write({ level: "info", message: "Scheduling read-only preflight completed.", fields: { scheduling_preflight: result } });
        return result;
      }
      client = openClient();
      const stores = { configuration: configuration.persistence, pool, ...diagnostics };
      const resources: SchedulingAppResources = { pool, clock, close: closePool,
        outbox: createPostgreSqlPlatformOutboxStore(stores), schedules: createPostgreSqlPlatformScheduleStore(stores), ...diagnostics };
      phase = "composition";
      runtime = await createSchedulingComposition({ ...resources, configuration, client,
        processing: createPostgreSqlPlatformProcessingStore(stores), uuidGenerator: dependencies.uuidGenerator ?? systemUuidGenerator,
        reporter, logger, extraCatalogs, app: binding.createApp(resources), purpose: binding.purpose,
        ...(observationIdentity === undefined ? {} : { observationIdentity }) });
      phase = "execution";
      const result = await runtime.run(event, context);
      completed = true;
      return result;
    } catch (error) {
      if (preflightCheck !== undefined && reporter !== undefined) {
        try { reportPlatformDiagnostic(reporter, schedulingPreflightRecord({ operation: binding.purpose, check: preflightCheck,
          observation: preflightObservation }), { capability: "scheduling", operation: binding.purpose, stage: "request" }); }
        catch { /* Never expose a diagnostic delivery failure. */ }
      }
      report(error, phase, phase === "execution" ? "earlier-effects-possible" : "not-started");
      // The Lambda runtime prints thrown errors. No raw source error crosses this final boundary.
      throw new Error("SCHEDULING_INVOCATION_FAILED");
    } finally {
      const cleanup = async (action: () => unknown) => {
        try { await action(); }
        catch (error) { report(error, "shutdown", completed ? "completion-preserved" : "earlier-effects-possible"); }
      };
      if (runtime !== undefined) await cleanup(() => runtime!.close());
      if (pool !== undefined && poolClose === undefined) await cleanup(closePool);
      if (client !== undefined) await cleanup(() => client!.destroy());
    }
  };
}
