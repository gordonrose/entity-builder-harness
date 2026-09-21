<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.architecture.adr.0029-use-task-local-otel-collector-for-cloudwatch-metrics
version: 1
status: active
layer: 04.deploy
domain: infra.observability
disciplines:
- architecture
- security
- sre
kind: adr
purpose: Record the initial target metric-delivery boundary for Kanbien staging capability observability.
portability:
  class: source-only
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
- id: platform.adapter.aws.observability.cloudwatch
  path: platform/adapters/aws/observability/cloudwatch/
- id: product.plan.platform-runtime-implementation
  path: .agentic/03.product/plans/implementation/platform-runtime-implementation.md
-->
# ADR 0029: Use a Task-Local OpenTelemetry Collector for CloudWatch Metrics

## Status

Accepted for the initial Kanbien staging capability-metrics path. It is
selected but not yet deployed.

## Context

The platform server and worker already produce provider-neutral Core metric
points through an injected `Metrics` port. The first target needs to retain a
small number of reviewed counters and latency distributions without making
routes, jobs, application packages, or Core contracts depend on AWS.

Direct application calls to a CloudWatch API would couple the generic runtime
to AWS credentials and delivery semantics. It would also make it too easy for
an application configuration value to become arbitrary outbound telemetry.
Conversely, creating a broad generic metrics backend now would exceed the
small staging smoke target and blur provider and target ownership.

## Decision

The initial Kanbien staging metrics path is:

```text
provider-neutral Core Metrics port
  -> AWS OpenTelemetry metrics adapter
  -> task-local OTLP HTTP/protobuf collector at 127.0.0.1:4318
  -> AWS CloudWatch metric backend
```

The adapter is kept at:

```text
platform/adapters/aws/observability/cloudwatch/
```

It accepts only a reviewed target metric-series catalogue. Each series has one
Core name, kind, unit, OpenTelemetry instrument name, explicit label allowlist,
cardinality limit, and—where it is a distribution—explicit bucket boundaries.
The adapter allows only the task-local collector endpoint. It never reads a
remote delivery URL from app configuration.

The Kanbien staging target profile owns the selected series, provisional SLO
definitions, exporter interval and timeout, evidence lifecycle, and delivery
state. Target composition, CloudFormation, collector-image selection, IAM,
dashboards, SLO queries, and alarms remain deployment-owned. The first source
implementation is prepared locally, but is not an AWS deployment or delivery
claim.

## Consequences

- Application and generic platform runtime code retain the same provider-neutral
  `Metrics` dependency.
- A target can add or remove a reviewed series without changing Core names or
  introducing arbitrary metric creation.
- The local collector makes the application-to-collector hop private to its
  ECS task. The ECS task role, not a route or job, has the narrowly scoped
  `cloudwatch:PutMetricData` permission used by the collector's SigV4 export.
  ECS task-role credentials are shared by containers in one task, so this is a
  task boundary—not a separate per-container IAM boundary. The adapter's fixed
  loopback endpoint and reviewed task definition are the application-side
  controls; a future stronger separation would require a separate telemetry
  gateway/task.
- An exporter outage must remain best effort for a request or job, but target
  operations must surface it as missing coverage rather than a healthy SLO.
- The initial target must not claim a deployed SLO until collector delivery,
  queryable metric evidence, data lifecycle, access, synthetic coverage, and
  alert delivery have been proven.

## Non-Goals

This ADR does not authorize an AWS resource change, ECS task-definition update,
IAM policy application, collector deployment, dashboard, SLO alarm, trace
exporter, security-event pipeline, or audit-event pipeline. The repository may
prepare and validate corresponding source artifacts locally; applying them
still requires a reviewed CloudFormation change set and explicit approval.

This ADR does not select a universal metrics backend for every future target.
A different client, environment, provider, or workload may use another
target-specific adapter after its own governed decision.
