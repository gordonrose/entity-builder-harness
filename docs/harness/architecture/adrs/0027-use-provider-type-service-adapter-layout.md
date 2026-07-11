<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.adr.0027-use-provider-type-service-adapter-layout
  version: 1
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  - sre
  kind: adr
  purpose: Record the provider/type/service path convention for platform adapters.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: platform.adapters.readme
    path: platform/adapters/README.md
  - id: harness.architecture.rules.layers.platform
    path: docs/harness/architecture/rules/layers/platform.yml
  - id: harness.architecture.rules.concerns.platform-infra-capability-layering
    path: docs/harness/architecture/rules/concerns/platform-infra-capability-layering.yml
-->
# ADR 0027: Use Provider Type Service Adapter Layout

## Status

Accepted.

## Context

The platform runtime needs provider adapters over time, but apps must not be
written directly for a specific provider such as ECS, Lambda, SQS, or S3.

If all adapters live in a flat folder, the boundary becomes hard to scan once
the platform supports multiple providers and service categories. If the app
layer chooses provider implementations from ordinary feature code, provider
details leak into product internals and make app refactors depend on
infrastructure choices.

At the same time, the first production planning target is AWS ECS Fargate, and
future slices may add AWS Lambda, App Runner, SQS, S3, Secrets Manager,
CloudWatch, OpenTelemetry exporters, or local development adapters.

## Decision

Platform adapters are organized by provider, adapter type, and service name:

```text
platform/adapters/<provider>/<adapter-type>/<service-name>/
```

Examples:

```text
platform/adapters/aws/runtime/ecs-fargate/
platform/adapters/aws/runtime/lambda/
platform/adapters/aws/runtime/app-runner/
platform/adapters/aws/queue/sqs/
platform/adapters/aws/storage/s3/
platform/adapters/aws/secrets/secrets-manager/
platform/adapters/aws/observability/cloudwatch/
```

Apps declare provider-neutral needs through public platform contracts and app
manifests. Platform and deploy composition decide which adapters and deployment
profiles satisfy those needs.

Provider adapters may integrate provider SDK clients, provider error mapping,
configuration validation, and lifecycle behavior. They must return platform or
core contracts as their primary interface, not raw provider clients as the
ordinary app-facing API.

Infra still owns provider resources, networking, IAM, DNS, TLS, queues,
storage, secrets, alarms, and environment values. Platform adapters do not
provision cloud resources.

## Consequences

ECS Fargate can be selected as the first production planning runtime without
making ECS part of the app contract.

Future runtime families can be added through governed adapters and deployment
profiles without changing app mount contracts.

Reviewers can quickly tell whether an adapter is AWS-specific, what kind of
platform concern it serves, and which provider service it wraps.

Apps remain portable at the platform contract level. Provider-specific choices
are made by platform/deploy composition, not by ordinary app feature code.
