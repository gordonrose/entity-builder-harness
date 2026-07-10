<!-- agentic-artifact:
schema: agentic-artifact/v2
id: platform.adapters.readme
version: 1
status: active
layer: 03.product
domain: platform
disciplines:
- architecture
- sre
kind: guide
purpose: Define the platform adapter layout convention before provider adapters are implemented.
portability:
  class: internal
  targets: []
used_by:
- id: harness.architecture.adr.0027-use-provider-type-service-adapter-layout
  path: docs/harness/architecture/adrs/0027-use-provider-type-service-adapter-layout.md
-->
# Platform Adapters

`platform/adapters/**` is reserved for provider-specific runtime translation.

Adapters are organized by provider, adapter type, and service name:

```text
platform/adapters/<provider>/<adapter-type>/<service-name>/
```

Examples:

```text
platform/adapters/aws/runtime/ecs-fargate/
platform/adapters/aws/runtime/lambda/
platform/adapters/aws/queue/sqs/
platform/adapters/aws/storage/s3/
platform/adapters/aws/secrets/secrets-manager/
platform/adapters/aws/observability/cloudwatch/
```

Apps should not import provider adapters from ordinary app code. Apps declare
routes, jobs, health checks, config schemas, permissions, lifecycle hooks, and
deployment requirements through public platform contracts and app manifests.

Infra provisions provider resources. Platform adapters translate provider
services into platform contracts at approved runtime composition boundaries.
