<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.source-material.platform-infra-capability-layering-v1
  version: 1
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  - sre
  kind: source-material
  purpose: Record the repo-wide capability layering split across core, platform runtime, platform adapters, infra blueprints, infra providers, and environments.
  portability:
    class: required
    targets:
    - llm-workbench
    - entity-builder
    - design-system-builder
  used_by:
  - id: harness.architecture.rules.concerns.platform-infra-capability-layering
    path: docs/harness/architecture/rules/concerns/platform-infra-capability-layering.yml
-->
# Platform and Infra Capability Layering v1

## Purpose

This source material records the repo-wide placement rule for platform-level
capabilities that need both runtime code and provisioned infrastructure.

The goal is to keep one concept, such as queues, storage, observability, or
identity, split into clear ownership bands:

- `packages/core` names provider-neutral contracts and stable vocabulary.
- `platform/runtime` owns provider-neutral runtime behavior and orchestration.
- `platform/adapters` owns provider-specific runtime translation.
- `infra/blueprints` or `infra/contracts` owns provider-neutral resource
  requirements.
- `infra/providers` owns provider-specific resource definitions.
- `infra/environments` owns target-specific values and deployment choices.
- `apps` own product meaning, product workflows, and business handlers.

## Decision

Platform-level functionality should use the same contract/runtime/adapter split
consistently across the repo.

`packages/core` should define stable public contracts that apps can depend on
and platform can implement. Core should not choose AWS, databases, brokers,
runtime hosts, SDK clients, infrastructure resources, or deployment topology.

`platform/runtime` should implement provider-neutral mechanics: request and job
contexts, registries, worker loops, retry decisions, idempotency checks,
observability hooks, graceful shutdown, resource lifecycle, and common runtime
policies that do not require a specific provider SDK.

`platform/adapters` should translate provider-neutral runtime contracts into a
specific provider or library. AWS SQS, EventBridge, S3, CloudWatch, Cognito,
Postgres, Redis, OpenTelemetry, and similar integrations belong here when they
are runtime code. Adapters should expose predictable factories and return core
or platform runtime contracts rather than raw provider clients as the primary
app-facing API.

Platform adapters should use the path shape:

```text
platform/adapters/<provider>/<adapter-type>/<service-name>/
```

Examples include:

- `platform/adapters/aws/runtime/ecs-fargate/`
- `platform/adapters/aws/runtime/lambda/`
- `platform/adapters/aws/queue/sqs/`
- `platform/adapters/aws/storage/s3/`
- `platform/adapters/aws/secrets/secrets-manager/`
- `platform/adapters/aws/observability/cloudwatch/`

The provider segment names the external provider boundary, the adapter type
names the platform concern, and the service name names the concrete service.
Apps should declare provider-neutral needs through platform contracts and app
manifests; platform/deploy composition chooses adapters and deployment
profiles.

`infra/blueprints` or `infra/contracts` should describe provider-neutral
resource requirements: queues need a queue, a dead-letter path, encryption,
retention, alarms, and IAM-like access boundaries; storage needs buckets or
tables, encryption, lifecycle policy, backup, and access boundaries. These
blueprints are deployment requirements, not runtime clients.

`infra/providers` should translate provider-neutral infrastructure blueprints
into concrete provider resources such as AWS SQS queues, DLQs, KMS keys,
CloudWatch alarms, IAM policies, ECS workers, and autoscaling rules.

`infra/environments` should hold environment-specific values and deployment
choices such as dev/staging/prod target names, retention days, queue sizes,
alarm thresholds, regions, account ids, and provider profile selections.

Apps should own product decisions: when to enqueue work, which business handler
owns the work, what a product event means, which resource requires permission,
and which product outcome should be audited.

## Queue Example

For queues, the split should look like this:

- `packages/core/queues` defines `QueueMessage`, `Queue`, `QueueHandler`,
  queue error vocabulary, send options, delivery metadata, retry/dead-letter
  metadata shapes, and test helpers.
- `apps` decide when a product action should enqueue work and implement the
  product-owned handler, such as sending a welcome email, generating a report,
  or syncing an external integration.
- `platform/runtime/queues` owns worker loops, handler registration,
  idempotency enforcement, retry decisions, backoff, dead-letter handling,
  payload validation, metrics, logs, health checks, and graceful shutdown.
- `platform/adapters/aws/queue/sqs` translates the runtime queue contract to AWS
  SQS concepts such as queue URL, receipt handle, message attributes, delay,
  visibility timeout, receive/delete semantics, and provider errors.
- `infra/blueprints/queues` describes required queue resources, dead-letter
  resources, encryption, retention, access boundaries, alarms, and worker
  deployment needs without naming AWS-only code.
- `infra/providers/aws/queues` provisions SQS queues, DLQs, KMS keys,
  CloudWatch alarms, IAM permissions, worker service wiring, and autoscaling.
- `infra/environments` supplies concrete target values such as retention days,
  max receives, visibility timeout, alarm thresholds, and worker concurrency.

## Acceptance Guidance

When adding a new platform-level capability, the implementation plan should
name which layer owns each part of the capability before code is written.

If a capability only needs a contract, `packages/core` may be enough for the
current slice. If runtime behavior is added, platform runtime and adapter
placement should be explicit. If external resources are needed, infra blueprint
and provider ownership should be explicit.

Code review should reject changes that collapse these bands together, such as:

- core importing an AWS SDK or exposing provider-specific fields as the main
  contract;
- platform runtime defining Terraform, CDK, Pulumi, Kubernetes, IAM, or cloud
  resource topology;
- infra modules creating runtime clients or owning application handlers;
- apps importing provider adapters outside an approved bootstrap or
  composition-root boundary;
- provider-specific infrastructure values being hidden inside generic runtime
  code.

## RAG Implication

When agents ask where queue, storage, observability, identity, configuration,
or other platform-level capability code should live, the RAG/rulebook layer
should retrieve this source material alongside the relevant core, platform,
infra, and adapter-consumption rules.

When a code change adds provider-neutral contracts, runtime mechanics,
provider-specific translation, or infrastructure resources, the RAG evidence
chain should make the owning layer clear rather than relying on chat history.
