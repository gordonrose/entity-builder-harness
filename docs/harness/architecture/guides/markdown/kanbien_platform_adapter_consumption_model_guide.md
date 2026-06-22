# Kanbien Platform Adapter Consumption Model

**A backwards-compatibility guide for consuming platform functionality from application layers**

**Architecture Decision Guide**  
**Version 1.0 - June 2026**

> **Decision:** Kanbien will use **Option B: one package per adapter**, while keeping application feature code dependent only on stable contracts from `packages/core`. Adapter packages expose predictable factory functions. Platform profile packages compose adapters into stable app-facing platform objects.

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
  - [The rule](#the-rule)
- [2. The Core Decision](#2-the-core-decision)
- [3. Why Predictable Consumption Matters](#3-why-predictable-consumption-matters)
  - [The stable shape](#the-stable-shape)
- [4. The Three-Level Consumption Model](#4-the-three-level-consumption-model)
  - [Level 1: Feature code](#level-1-feature-code)
  - [Level 2: App bootstrap](#level-2-app-bootstrap)
  - [Level 3: Platform profiles](#level-3-platform-profiles)
- [5. Recommended Option B Structure](#5-recommended-option-b-structure)
- [6. Standard Adapter Package Contract](#6-standard-adapter-package-contract)
  - [Required exports](#required-exports)
  - [Example: S3 file storage adapter](#example-s3-file-storage-adapter)
  - [Factory returns the core interface](#factory-returns-the-core-interface)
- [7. Platform Profiles](#7-platform-profiles)
  - [Why profiles are necessary](#why-profiles-are-necessary)
  - [Example profile interface](#example-profile-interface)
  - [Example AWS standard profile](#example-aws-standard-profile)
  - [App bootstrap consumes the profile](#app-bootstrap-consumes-the-profile)
- [8. Backwards Compatibility Strategy](#8-backwards-compatibility-strategy)
  - [1. Stable core interfaces](#1-stable-core-interfaces)
  - [2. Standard adapter factory names](#2-standard-adapter-factory-names)
  - [3. Standard config pattern](#3-standard-config-pattern)
  - [4. Stable platform profile contracts](#4-stable-platform-profile-contracts)
  - [5. Versioned adapter packages](#5-versioned-adapter-packages)
  - [6. Deprecation policy](#6-deprecation-policy)
- [9. Provider Compatibility and Capability Interfaces](#9-provider-compatibility-and-capability-interfaces)
  - [Bad universal interface](#bad-universal-interface)
  - [Better capability interfaces](#better-capability-interfaces)
- [10. Consumption Rules](#10-consumption-rules)
  - [Rule 1: No platform imports in feature code](#rule-1-no-platform-imports-in-feature-code)
  - [Rule 2: No vendor SDK imports outside platform adapters](#rule-2-no-vendor-sdk-imports-outside-platform-adapters)
  - [Rule 3: Core must not depend on platform](#rule-3-core-must-not-depend-on-platform)
  - [Rule 4: Bootstrap is the provider boundary](#rule-4-bootstrap-is-the-provider-boundary)
  - [Rule 5: Platform/shared must stay boring](#rule-5-platformshared-must-stay-boring)
- [11. Final Kanbien Folder Structure](#11-final-kanbien-folder-structure)
- [12. What Lives Where](#12-what-lives-where)
- [13. Implementation Checklist](#13-implementation-checklist)
- [14. The Simple Answer](#14-the-simple-answer)

---

# 1. Executive Summary

Yes: for backwards compatibility, every platform functionality layer should have a predictable and stable way of being consumed by application layers.

The important nuance is that applications should consume stable Kanbien contracts, not vendor-specific implementation details. The stable contract is not an AWS SDK client, an Azure SDK client, or a RabbitMQ connection. The stable contract is a Kanbien concept such as:

```txt
FileStorage
Queue
EventBus
NotificationService
AuditService
ConfigProvider
Logger
Metrics
```

> The application should say: **I need a FileStorage.**  
> The bootstrap layer should say: **In this deployment, FileStorage is implemented by S3.**

## The rule

```txt
Feature/application logic consumes packages/core interfaces.
App bootstrap wires those interfaces to platform profiles.
Platform profiles compose individual adapter packages.
Platform adapters expose predictable factory functions and config contracts.
```

This gives Kanbien backwards compatibility because the app logic remains stable even if the platform implementation changes.

---

# 2. The Core Decision

Kanbien should formalize this as an architecture decision.

```txt
ADR: Platform Adapter Consumption Model

Decision:
  Each platform adapter package must implement one or more packages/core contracts
  and expose a predictable factory-based API.

  Application feature code must depend only on packages/core contracts.

  Application bootstrap may depend on platform profile packages.

  Platform profile packages compose individual adapter packages into stable
  app-facing platform objects.

Consequences:
  Provider implementations can evolve independently.
  Apps avoid direct vendor coupling.
  Backwards compatibility is managed at the core contract and profile boundary.
  One-package-per-adapter remains scalable without making app bootstrapping chaotic.
```

This is the difference between a scalable modular platform and a pile of provider-specific imports scattered through product code.

---

# 3. Why Predictable Consumption Matters

Option B gives Kanbien one package per adapter. That is powerful for future scalability, but it introduces a new risk: inconsistent adapter APIs.

Without a predictable convention, every adapter can develop its own shape:

```ts
// Bad: every adapter has its own style
const files = new S3StorageClient(...);
const queue = SqsAdapter.connect(...);
const events = makeEventBridge(...);
const notifications = await SesProvider.initialize(...);
```

That makes bootstrap code fragile, confusing, and hard to migrate. Kanbien should avoid that by requiring every adapter to follow the same consumption model.

## The stable shape

```txt
createX(config): CoreInterface
XConfig
xConfigSchema
adapterMetadata
optional health checks
optional lifecycle hooks
```

The goal is not to hide every provider difference. The goal is to make the way of consuming providers predictable.

---

# 4. The Three-Level Consumption Model

Kanbien should use three consumption levels. This keeps feature code clean while still allowing deployment-specific choices.

## Level 1: Feature code

Feature code consumes only core contracts.

```ts
import type { EventBus } from "@kanbien/core/events";
import type { AuditService } from "@kanbien/core/audit";

export function createUserService(deps: {
  eventBus: EventBus;
  audit: AuditService;
}) {
  return {
    async createUser(input: CreateUserInput) {
      // product logic only
    },
  };
}
```

Feature code should not import AWS, Azure, OSS, or platform adapter packages.

## Level 2: App bootstrap

App bootstrap is allowed to consume platform profiles. This is the composition boundary where provider choice is made.

```ts
// apps/api/src/bootstrap/platform.ts

import { createAwsStandardPlatform } from "@kanbien/platform-profile-aws-standard";

const platform = createAwsStandardPlatform(config.platform);
```

Good places for platform imports:

- `apps/api/src/bootstrap/platform.ts`
- `apps/worker/src/bootstrap/platform.ts`
- `apps/admin/src/bootstrap/platform.ts`

Bad places for platform imports:

- `apps/api/src/features/users/create-user.ts`
- `apps/api/src/features/billing/change-plan.ts`
- `apps/api/src/features/documents/upload-document.ts`

## Level 3: Platform profiles

Platform profiles consume individual adapter packages and assemble a stable app-facing platform object.

```ts
import { createS3FileStorage } from "@kanbien/platform-aws-files-s3";
import { createSqsQueue } from "@kanbien/platform-aws-queues-sqs";
import { createEventBridgeEventBus } from "@kanbien/platform-aws-events-eventbridge";
```

This is where Option B pays off. You can replace or upgrade one adapter without rewriting product code.

---

# 5. Recommended Option B Structure

Kanbien has chosen Option B: one package per adapter. The structure should be provider-first, capability-second.

```txt
platform/
  shared/

  local/
    files-local/
    queues-in-memory/
    events-in-memory/
    notifications-console/
    authn-fake/
    authz-allow-all/
    logging-stdout/
    monitoring-noop/

  aws/
    files-s3/
    queues-sqs/
    events-eventbridge/
    async-jobs-sqs/
    notifications-ses/
    authn-cognito/
    authz-verified-permissions/
    config-appconfig/
    config-secrets-manager/
    logging-cloudwatch/
    monitoring-cloudwatch/
    security-kms/
    audit-postgres/
    analytics-firehose/
    reporting-s3/

  azure/
    files-blob/
    queues-service-bus/
    events-event-grid/
    notifications-communication-services/
    authn-entra-external-id/
    config-app-configuration/
    security-key-vault/

  oss/
    files-minio/
    queues-rabbitmq/
    events-nats/
    authn-keycloak/
    authz-openfga/
    config-unleash/
    security-vault/
    monitoring-prometheus/
    logging-loki/

  profiles/
    local-dev/
    aws-standard/
    aws-enterprise/
    azure-standard/
    oss-local/
```

The app should usually import a profile package, not each individual adapter package. Profiles keep Option B manageable.

---

# 6. Standard Adapter Package Contract

Every adapter package should expose a predictable public API. The exact implementation can vary, but the public shape should remain consistent.

## Required exports

| Export | Purpose |
|---|---|
| `createX(config)` | Factory function that returns the relevant `packages/core` interface. |
| `XConfig` | Explicit configuration type for the adapter. |
| `xConfigSchema` | Runtime validation schema for adapter configuration. |
| `adapterMetadata` | Provider, capability, implementation, and package identity. |
| Health check | Optional function to verify the adapter can reach its backing service. |
| Lifecycle hooks | Optional `start` / `stop` / `dispose` hooks for adapters that maintain connections. |

## Example: S3 file storage adapter

```ts
// platform/aws/files-s3/src/index.ts

export {
  createS3FileStorage,
  type S3FileStorageConfig,
  s3FileStorageConfigSchema,
} from "./s3-file-storage";

export {
  createS3SignedUrlService,
  type S3SignedUrlServiceConfig,
} from "./s3-signed-url-service";

export {
  checkS3FileStorageHealth,
} from "./health";
```

## Factory returns the core interface

```ts
import type { FileStorage } from "@kanbien/core/files";

export interface S3FileStorageConfig {
  region: string;
  bucketName: string;
}

export function createS3FileStorage(
  config: S3FileStorageConfig
): FileStorage {
  return new S3FileStorage(config);
}
```

The app never needs to know about the underlying S3 client. It only receives a `FileStorage`.

---

# 7. Platform Profiles

With one package per adapter, Kanbien should introduce platform profiles. A profile is a deployment recipe that composes many adapters into a stable platform object.

## Why profiles are necessary

Without profiles, every app has to manually wire 10-20 individual adapter packages. That becomes repetitive and inconsistent. Profiles make the app's provider choice explicit while keeping bootstrap simple.

```txt
platform/profiles/aws-standard/
  package.json
  README.md
  src/
    index.ts
    config.ts
    platform.ts
```

## Example profile interface

```ts
import type {
  FileStorage,
  Queue,
  EventBus,
  NotificationService,
  Metrics,
  Logger,
} from "@kanbien/core";

export interface KanbienPlatform {
  files: FileStorage;
  queue: Queue;
  eventBus: EventBus;
  notifications: NotificationService;
  metrics: Metrics;
  logger: Logger;
}
```

## Example AWS standard profile

```ts
import { createS3FileStorage } from "@kanbien/platform-aws-files-s3";
import { createSqsQueue } from "@kanbien/platform-aws-queues-sqs";
import { createEventBridgeEventBus } from "@kanbien/platform-aws-events-eventbridge";
import { createSesNotificationService } from "@kanbien/platform-aws-notifications-ses";
import { createCloudWatchMetrics } from "@kanbien/platform-aws-monitoring-cloudwatch";
import { createStdoutJsonLogger } from "@kanbien/platform-local-logging-stdout";

export interface AwsStandardPlatformConfig {
  region: string;
  filesBucketName: string;
  queueUrl: string;
  eventBusName: string;
  emailFromAddress: string;
}

export function createAwsStandardPlatform(
  config: AwsStandardPlatformConfig
): KanbienPlatform {
  const logger = createStdoutJsonLogger();

  return {
    logger,
    files: createS3FileStorage({
      region: config.region,
      bucketName: config.filesBucketName,
    }),
    queue: createSqsQueue({
      region: config.region,
      queueUrl: config.queueUrl,
    }),
    eventBus: createEventBridgeEventBus({
      region: config.region,
      eventBusName: config.eventBusName,
    }),
    notifications: createSesNotificationService({
      region: config.region,
      fromAddress: config.emailFromAddress,
    }),
    metrics: createCloudWatchMetrics({
      region: config.region,
    }),
  };
}
```

## App bootstrap consumes the profile

```ts
import { createAwsStandardPlatform } from "@kanbien/platform-profile-aws-standard";
import { createAppServices } from "../services";

const platform = createAwsStandardPlatform(config.platform);

export const services = createAppServices({
  files: platform.files,
  queue: platform.queue,
  eventBus: platform.eventBus,
  notifications: platform.notifications,
  metrics: platform.metrics,
  logger: platform.logger,
});
```

---

# 8. Backwards Compatibility Strategy

Backwards compatibility should be managed at two boundaries:

```txt
packages/core contracts
platform profile contracts
```

## 1. Stable core interfaces

Core interfaces should change slowly and deliberately. Prefer additive changes over breaking changes.

```ts
export interface FileStorage {
  put(input: PutFileInput): Promise<StoredFile>;
  get(id: string): Promise<FileObject>;
  delete(id: string): Promise<void>;
}
```

If a new capability is needed, avoid bloating the existing interface with vendor-specific methods. Create a smaller capability interface.

```ts
export interface SignedUrlService {
  createDownloadUrl(input: CreateDownloadUrlInput): Promise<SignedUrl>;
}

export interface MultipartUploadService {
  begin(input: BeginMultipartUploadInput): Promise<MultipartUpload>;
  uploadPart(input: UploadPartInput): Promise<void>;
  complete(input: CompleteMultipartUploadInput): Promise<StoredFile>;
}
```

## 2. Standard adapter factory names

```txt
createS3FileStorage
createAzureBlobFileStorage
createMinioFileStorage

createSqsQueue
createAzureServiceBusQueue
createRabbitMqQueue

createEventBridgeEventBus
createEventGridEventBus
createNatsEventBus
```

Avoid inconsistent names like:

```txt
initS3
connectQueue
buildEventBridge
makeNotifications
newAwsFiles
```

## 3. Standard config pattern

```ts
export interface SqsQueueConfig {
  region: string;
  queueUrl: string;
  visibilityTimeoutSeconds?: number;
  maxReceiveCount?: number;
}

export const sqsQueueConfigSchema = z.object({
  region: z.string().min(1),
  queueUrl: z.string().url(),
  visibilityTimeoutSeconds: z.number().int().positive().optional(),
  maxReceiveCount: z.number().int().positive().optional(),
});
```

Validate configuration at startup. Platform failures should be explicit and early, not discovered after the first production request.

## 4. Stable platform profile contracts

A public API app, a worker app, and a frontend app should not all receive one giant platform object. Define the right platform surface for each app type.

```ts
export interface ApiPlatform {
  logger: Logger;
  metrics: Metrics;
  authenticator: Authenticator;
  authorizer: Authorizer;
  audit: AuditService;
  eventBus: EventBus;
  files: FileStorage;
  notifications: NotificationService;
}

export interface WorkerPlatform {
  logger: Logger;
  metrics: Metrics;
  queue: Queue;
  jobs: JobScheduler;
  eventBus: EventBus;
  notifications: NotificationService;
  audit: AuditService;
}
```

## 5. Versioned adapter packages

With Option B, each adapter package can version independently.

```txt
@kanbien/platform-aws-files-s3@1.4.0
@kanbien/platform-aws-queues-sqs@1.2.0
@kanbien/platform-aws-events-eventbridge@2.0.0
```

Use semantic versioning:

| Version type | Meaning |
|---|---|
| Patch | Bug fixes, no API change. |
| Minor | Backwards-compatible additions. |
| Major | Breaking changes. |

## 6. Deprecation policy

```txt
1. Add the new method or config option.
2. Mark the old method or config option deprecated.
3. Support both for a defined period.
4. Provide migration notes.
5. Remove the old surface in the next major version.
```

Example:

```ts
export interface S3FileStorageConfig {
  region: string;

  /**
   * @deprecated Use bucketName instead.
   */
  bucket?: string;

  bucketName?: string;
}
```

Then internally:

```ts
const bucketName = config.bucketName ?? config.bucket;

if (!bucketName) {
  throw new Error("bucketName is required");
}
```

---

# 9. Provider Compatibility and Capability Interfaces

Kanbien should not pretend every provider is identical. SQS, Azure Service Bus, RabbitMQ, NATS, and Kafka differ in:

```txt
Ordering
Retries
Visibility timeouts
Dead-lettering
Delivery guarantees
Message size
Fanout
Consumer groups
```

The right answer is to define Kanbien capability interfaces around what the product actually needs.

## Bad universal interface

```ts
interface UniversalStorage {
  put(): Promise<void>;
  get(): Promise<void>;
  createS3PresignedPost(): Promise<void>;
  createAzureSasToken(): Promise<void>;
}
```

This leaks provider-specific concepts into the universal contract.

## Better capability interfaces

```ts
interface FileStorage {
  put(input: PutFileInput): Promise<StoredFile>;
  get(id: string): Promise<FileObject>;
  delete(id: string): Promise<void>;
}

interface SignedUrlService {
  createDownloadUrl(input: CreateDownloadUrlInput): Promise<SignedUrl>;
}

interface MultipartUploadService {
  begin(input: BeginMultipartUploadInput): Promise<MultipartUpload>;
  uploadPart(input: UploadPartInput): Promise<void>;
  complete(input: CompleteMultipartUploadInput): Promise<StoredFile>;
}
```

Then providers implement the capabilities they support.

```txt
S3 adapter:
  FileStorage
  SignedUrlService
  MultipartUploadService

Local file adapter:
  FileStorage
  maybe SignedUrlService
  probably not MultipartUploadService
```

This makes compatibility explicit.

---

# 10. Consumption Rules

These rules keep Kanbien's architecture clean as the platform grows.

## Rule 1: No platform imports in feature code

```ts
// Bad
import { createS3FileStorage } from "@kanbien/platform-aws-files-s3";

// Good
import type { FileStorage } from "@kanbien/core/files";
```

## Rule 2: No vendor SDK imports outside platform adapters

```ts
// Bad: apps/api/src/features/documents/upload.ts
import { S3Client } from "@aws-sdk/client-s3";

// Good: platform/aws/files-s3/src/s3-file-storage.ts
import { S3Client } from "@aws-sdk/client-s3";
```

## Rule 3: Core must not depend on platform

```txt
packages/core
  may define FileStorage, Queue, EventBus, AuditService

platform/aws/files-s3
  may implement FileStorage using S3

packages/core
  must not import @kanbien/platform-aws-files-s3
  must not import @aws-sdk/client-s3
```

## Rule 4: Bootstrap is the provider boundary

The app bootstrap can say:

```txt
This deployment uses AWS.
```

Product logic should only say:

```txt
I need an EventBus.
I need FileStorage.
I need an AuditService.
```

## Rule 5: Platform/shared must stay boring

`platform/shared` is for provider-neutral implementation helpers such as:

```txt
retry
serialization
idempotency
adapter errors
observability helpers
```

It should not define Kanbien domain meaning.

---

# 11. Final Kanbien Folder Structure

The recommended final structure combines `packages/core` contracts, one package per adapter, and profile packages for simple application consumption.

```txt
kanbien/
  packages/
    core/
      src/
        authn/
        authz/
        files/
        queues/
        events/
        audit/
        notifications/
        logging/
        monitoring/
        config/
        tenancy/
        persistence/
        security/
        analytics/
        reporting/
        async-jobs/
        i18n/
        localization/
        runtime/
          api-platform.ts
          worker-platform.ts

  platform/
    shared/
      retry/
      serialization/
      observability/
      idempotency/
      errors/

    local/
      files-local/
      queues-in-memory/
      events-in-memory/
      notifications-console/
      authn-fake/
      authz-fake/
      logging-stdout/
      monitoring-noop/

    aws/
      files-s3/
      queues-sqs/
      events-eventbridge/
      async-jobs-sqs/
      notifications-ses/
      authn-cognito/
      authz-verified-permissions/
      config-appconfig/
      config-secrets-manager/
      logging-cloudwatch/
      monitoring-cloudwatch/
      security-kms/
      audit-postgres/
      analytics-firehose/
      reporting-s3/

    azure/
      files-blob/
      queues-service-bus/
      events-event-grid/
      notifications-communication-services/
      authn-entra-external-id/
      config-app-configuration/
      security-key-vault/

    oss/
      files-minio/
      queues-rabbitmq/
      events-nats/
      authn-keycloak/
      authz-openfga/
      config-unleash/
      security-vault/
      monitoring-prometheus/
      logging-loki/

    profiles/
      local-dev/
      aws-standard/
      aws-enterprise/
      azure-standard/
      oss-local/
```

---

# 12. What Lives Where

| Layer | Responsibility | Examples |
|---|---|---|
| `packages/core` | Stable Kanbien contracts and concepts | `FileStorage`, `Queue`, `EventBus`, `TenantContext`, `AuditService` |
| `platform/shared` | Provider-neutral implementation utilities | Retry, serialization, idempotency, observability helpers |
| `platform/aws/*` | AWS-specific adapter packages | `files-s3`, `queues-sqs`, `events-eventbridge` |
| `platform/azure/*` | Azure-specific adapter packages | `files-blob`, `queues-service-bus`, `events-event-grid` |
| `platform/oss/*` | Open-source adapter packages | `files-minio`, `queues-rabbitmq`, `events-nats` |
| `platform/profiles/*` | Deployment recipes that compose adapters | `aws-standard`, `local-dev`, `oss-local` |
| `apps/*/bootstrap` | Provider selection and app wiring | `createAwsStandardPlatform(config)` |
| `apps/*/features` | Product and feature logic | Uses core contracts only |

---

# 13. Implementation Checklist

Use this checklist when creating each new platform adapter package.

- Does the adapter implement a `packages/core` interface?
- Does it avoid exposing provider SDK clients as the main app-facing API?
- Does it export a predictable `createX(config)` factory?
- Does it export an explicit `XConfig` type?
- Does it validate configuration at startup?
- Does it include `adapterMetadata`?
- Does it include a health check if the dependency is remote or stateful?
- Does it preserve correlation IDs, tenant IDs, and relevant metadata?
- Does it map provider-specific errors into Kanbien adapter errors?
- Does it document retry, timeout, idempotency, and dead-letter behaviour where relevant?
- Does it have unit tests against the core contract?
- Does it have integration tests against the real service or emulator where practical?
- Is it consumed by a platform profile rather than scattered across app feature code?

---

# 14. The Simple Answer

Each platform functionality layer should have a predictable consumption model.

```txt
Core interface:
  packages/core/files/FileStorage

Adapter package:
  @kanbien/platform-aws-files-s3
  createS3FileStorage(config): FileStorage

Profile package:
  @kanbien/platform-profile-aws-standard
  createAwsStandardPlatform(config): ApiPlatform / WorkerPlatform

Application feature code:
  consumes FileStorage, EventBus, Queue, AuditService, etc.

Application bootstrap:
  consumes the selected platform profile.
```

This gives Kanbien backwards compatibility, clean provider separation, and future scalability without making day-to-day application development painful.
