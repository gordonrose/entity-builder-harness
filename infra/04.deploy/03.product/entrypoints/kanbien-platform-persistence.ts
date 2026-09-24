// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-persistence
//   version: 3
//   status: active
//   layer: 04.deploy
//   domain: persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: code
//   purpose: Compose Kanbien staging DynamoDB persistence seams for harmless smoke acceptance, durable outbox relay, and duplicate-safe worker processing.
//   portability:
//     class: target-specific
//     targets:
//     - kanbien/staging
//   used_by:
//   - id: platform.server.image-build
//     path: platform/server/tsconfig.image.json

import type {
  PlatformSmokeWorkItem,
  PlatformSmokeWorkItemRepository,
} from "@kanbien/app-platform-smoke";
import type { TransactWriteItem } from "@aws-sdk/client-dynamodb";
import { type Logger, type LogRecord } from "@kanbien/core/logging";
import { type Metrics } from "@kanbien/core/monitoring";
import type { Queue } from "@kanbien/core/queues";
import type { Clock } from "@kanbien/core/shared";
import { ok, systemClock } from "@kanbien/core/shared";
import type { PlatformExecutionContext } from "@kanbien/platform-contracts";
import { createPlatformPersistenceTransitionObserver } from "@kanbien/platform-observability";
import {
  createDynamoDbPlatformPersistenceAtomicWriter,
  createDynamoDbPlatformOutboxStore,
  createDynamoDbPlatformProcessingStore,
  dynamoDbPersistenceConfiguration,
  stageDynamoDbTransactionWrite,
  type DynamoDbPersistenceCommandClient,
  type DynamoDbPersistenceConfiguration,
} from "@kanbien/platform-adapter-aws-persistence-dynamodb";
import {
  createPlatformOutboxRelay,
  type PlatformOutboxQueuePayload,
  type PlatformOutboxRelay,
  type PlatformPersistenceAtomicWriter,
  type PlatformPersistenceLeaseOwner,
  type PlatformPersistenceObserver,
  type PlatformProcessingStore,
} from "@kanbien/platform-persistence";
import { kanbienPlatformSmokeWorkItemDeliveryObservabilityProfile } from "@kanbien/product-kanbien-platform";

export interface KanbienPlatformSmokePersistence {
  readonly atomicWriter: PlatformPersistenceAtomicWriter;
  readonly repository: PlatformSmokeWorkItemRepository;
}

export interface KanbienPlatformSmokePersistenceOptions {
  readonly client: DynamoDbPersistenceCommandClient;
  readonly configuration: DynamoDbPersistenceConfiguration;
}

/** The target-owned composition inputs for one bounded durable outbox relay. */
export interface KanbienPlatformOutboxRelayOptions {
  readonly client: DynamoDbPersistenceCommandClient;
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly queue: Queue<PlatformOutboxQueuePayload>;
  readonly owner: PlatformPersistenceLeaseOwner;
  readonly leaseDurationMs: number;
  readonly clock: Clock;
  readonly observer?: PlatformPersistenceObserver;
}

/** The structural dependency consumed by the provider-neutral worker shell. */
export interface KanbienPlatformDurableWorkerProcessing {
  readonly processingStore: PlatformProcessingStore;
  readonly owner: PlatformPersistenceLeaseOwner;
  readonly leaseDurationMs: number;
  readonly observer?: PlatformPersistenceObserver;
}

/**
 * Build the one reviewed transition-observer policy used by the staging relay
 * and durable worker. The observer receives no record, payload, queue, or AWS
 * SDK data; it can emit only the product profile's approved operational facts.
 */
export function createKanbienPlatformPersistenceTransitionObserver(input: {
  readonly executionContext: PlatformExecutionContext;
  readonly metrics: Metrics;
}) {
  return createPlatformPersistenceTransitionObserver({
    profile: kanbienPlatformSmokeWorkItemDeliveryObservabilityProfile,
    executionContext: input.executionContext,
    logger: kanbienPlatformPersistenceConsoleLogger,
    metrics: input.metrics,
    clock: systemClock,
  });
}

/**
 * Keep the product row definition at the staging composition boundary. The
 * reusable DynamoDB adapter provides transaction mechanics but does not know
 * what a smoke work item means.
 */
export function createKanbienPlatformSmokePersistence(
  options: KanbienPlatformSmokePersistenceOptions,
): KanbienPlatformSmokePersistence {
  return {
    atomicWriter: createDynamoDbPlatformPersistenceAtomicWriter(options),
    repository: {
      async create({ workItem, transaction }) {
        const staged = stageDynamoDbTransactionWrite(
          transaction,
          platformSmokeWorkItemPut(options.configuration, workItem),
        );
        if (!staged.ok) return staged;
        return ok(workItem);
      },
    },
  };
}

/**
 * Select the DynamoDB outbox store and the already-selected Core queue port at
 * the staging composition boundary. Generic platform relay code stays unaware
 * of DynamoDB, SQS, table names, and target environment variables.
 */
export function createKanbienPlatformOutboxRelay(
  options: KanbienPlatformOutboxRelayOptions,
): PlatformOutboxRelay {
  return createPlatformOutboxRelay({
    outbox: createDynamoDbPlatformOutboxStore({
      client: options.client,
      configuration: options.configuration,
    }),
    queue: options.queue,
    owner: options.owner,
    leaseDurationMs: options.leaseDurationMs,
    clock: options.clock,
    ...(options.observer === undefined ? {} : { observer: options.observer }),
  });
}

/**
 * Select the one DynamoDB processing store that guards duplicate worker
 * effects. The caller passes it only to the generic durable-worker seam.
 */
export function createKanbienPlatformDurableWorkerProcessing(input: {
  readonly client: DynamoDbPersistenceCommandClient;
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly owner: PlatformPersistenceLeaseOwner;
  readonly leaseDurationMs: number;
  readonly observer?: PlatformPersistenceObserver;
}): KanbienPlatformDurableWorkerProcessing {
  return {
    processingStore: createDynamoDbPlatformProcessingStore({
      client: input.client,
      configuration: input.configuration,
    }),
    owner: input.owner,
    leaseDurationMs: input.leaseDurationMs,
    ...(input.observer === undefined ? {} : { observer: input.observer }),
  };
}

/** Reconstruct only non-secret DynamoDB adapter configuration from a target task environment. */
export function dynamoDbPersistenceConfigurationFromTargetEnvironment(
  env: Readonly<Record<string, string | undefined>>,
) {
  return dynamoDbPersistenceConfiguration({
    region: env["PLATFORM_PERSISTENCE_DYNAMODB_REGION"] ?? "",
    tableName: env["PLATFORM_PERSISTENCE_DYNAMODB_TABLE"] ?? "",
    outboxDueIndexName: env["PLATFORM_PERSISTENCE_DYNAMODB_OUTBOX_DUE_INDEX"] ?? "",
    lineageCauseIndexName: env["PLATFORM_PERSISTENCE_DYNAMODB_LINEAGE_CAUSE_INDEX"] ?? "",
  });
}

function platformSmokeWorkItemPut(
  configuration: DynamoDbPersistenceConfiguration,
  workItem: PlatformSmokeWorkItem,
): TransactWriteItem {
  return {
    Put: {
      TableName: configuration.tableName,
      Item: {
        PK: { S: "SMOKE-WORK-ITEM#" + workItem.id },
        SK: { S: "SMOKE-WORK-ITEM" },
        recordType: { S: "platform-smoke-work-item" },
        workItemId: { S: workItem.id },
        state: { S: workItem.state },
        revision: { N: String(workItem.revision) },
        acceptedAt: { S: workItem.acceptedAt },
      },
      ConditionExpression: "attribute_not_exists(#pk)",
      ExpressionAttributeNames: { "#pk": "PK" },
    },
  };
}

/** Keep target-entrypoint console output structurally compatible with Core's logger port. */
const kanbienPlatformPersistenceConsoleLogger: Logger = {
  write(record: LogRecord): void {
    const line = JSON.stringify(record);
    if (record.level === "error") {
      console.error(line);
      return;
    }
    console.log(line);
  },
};
