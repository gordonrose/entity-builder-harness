<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.workflow.platform-runtime-implementation
version: 1
status: active
layer: 03.product
domain: platform-runtime
disciplines:
- architecture
- sre
- agentic
kind: workflow
purpose: Govern implementation slices for the platform runtime shell before real product app work begins.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.architecture.plan.platform-runtime-implementation
  path: docs/harness/architecture/plans/platform-runtime-implementation-plan.md
- id: harness.architecture.rules.layers.platform
  path: docs/harness/architecture/rules/layers/platform.yml
-->
# Platform Runtime Implementation Workflow

## Use When

Use this workflow for implementation slices that build or change the platform
runtime shell, including:

- `platform/contracts/**`
- `platform/testing/**`
- `platform/runtime/**`
- `platform/server/**`
- `platform/workers/**`
- `platform/security/**`
- `platform/observability/**`
- `platform/health/**`
- `platform/config/**`
- `apps/platform-smoke/**`
- deployment-facing target profiles, manifests, or config that prove the
  platform shell without mutating cloud state

This workflow governs local product/platform runtime code. AWS planning and
execution remain governed by `.agentic/aws/` workflows.

## Required Inputs

- The platform runtime implementation milestone being changed.
- The intended runtime surface and file scope.
- The app-facing contract or dummy-app behavior being proven.
- The local checks that prove the slice.
- Any deployment-facing metadata produced by the slice.

## Required First Move

Before editing runtime code:

1. Read `docs/harness/architecture/plans/platform-runtime-implementation-plan.md`.
2. Read ADR 0025, ADR 0026, ADR 0027, and ADR 0028.
3. Read the relevant platform rules under `docs/harness/architecture/rules/`.
4. State the implementation milestone and bounded file scope.
5. Stop if the slice requires AWS mutation, production DNS, secrets, account
   configuration, or real product app behavior.

## Boundary Rules

- Platform composition roots may import public app mount modules.
- Ordinary platform modules must not import app services, features,
  repositories, route handlers, job handlers, or other app internals.
- Apps may organize internals however they choose; platform only depends on
  approved public mount modules, manifests, generated metadata, or contracts.
- `platform/contracts/**` is the app-facing contract surface.
- `platform/runtime/**` owns provider-neutral runtime mechanics, not HTTP
  framework details, cloud SDK clients, or product business decisions.
- `platform/server/**` owns HTTP process behavior and route adaptation.
- `platform/workers/**` owns background job process behavior and job
  adaptation.
- `platform/adapters/**` owns provider-specific runtime translation and uses
  `platform/adapters/<provider>/<adapter-type>/<service-name>/`.
- Deployment target profiles under `infra/04.deploy/**/targets/<client>/<environment>/`
  own client, environment, source repo, cloud provider, account/subscription,
  region, runtime family, adapter, and readiness proof selection.
- `platform/testing/**` owns fakes and mount-test helpers; it must not become a
  production runtime dependency.
- `apps/platform-smoke/**` is a deliberately boring dummy app, not the final
  application architecture template.
- Infrastructure provisioning, cloud topology, DNS, IAM, Terraform, CDK,
  Pulumi, and production deployment mutation do not belong under `platform/**`
  or `apps/**`.
- Ordinary app feature code must not import deployment target profiles,
  provider adapters, cloud SDK clients, or account/environment manifests.

## Required Checks

Each implementation slice should run the narrowest checks that prove the
changed surface, plus any broader checks required by shared contracts.

Minimum expected checks by surface:

- `platform/contracts/**`: type checks, runtime tests, declaration build when
  applicable, and dependency-boundary checks.
- `platform/testing/**`: mount-helper tests and negative mount tests.
- `platform/runtime/**`: registry, lifecycle, context factory, error mapping,
  cancellation, and shutdown tests.
- `platform/server/**`: local server smoke, health routes, route adaptation,
  middleware order, auth/permission denial, and error response tests.
- `platform/workers/**`: local worker smoke, job payload validation, retry,
  dead-letter, idempotency, logging, metrics, and shutdown tests.
- `platform/adapters/**`: adapter contract tests for provider translation,
  provider error mapping, configuration validation, and lifecycle behavior.
- `apps/platform-smoke/**`: app mount contract tests proving one route, one
  job, one health check, one config schema, one lifecycle hook, and one
  manifest.
- Deployment-facing target profiles/manifests/config: schema or static
  validation, target profile validation, and local runtime smoke that consumes
  the metadata.

If the required check does not exist yet, add the smallest governed check or
record an explicit gap before treating the slice as complete.

## Stop Conditions

Stop before editing or executing if:

- The task would mutate AWS, DNS, secrets, GitHub deployment settings, or other
  production infrastructure.
- The slice needs a real product app feature rather than dummy app proof.
- Platform code would need to import app internals.
- App internal structure would become part of a platform contract.
- A check needed to prove the slice is missing and no gap has been recorded.
- Runtime behavior depends on an unapproved provider, account, region,
  environment, queue, database, or cloud service.
- Client, source repository, cloud provider, account/subscription, region,
  runtime family, or adapter selection is being hardcoded into platform or app
  feature code instead of a deploy target profile.
- The work would require changing shared `packages/core` contracts without
  using the owning core/product governance.

## Session Evidence

Record in the session log:

- milestone and files changed;
- boundary decision applied;
- checks run and results;
- any gaps or deferred production obligations;
- ADR impact, if the slice changes durable architecture;
- deployment impact, if the slice changes manifests or container/deploy
  metadata.

## Output

Close each slice with:

- changed surfaces;
- proof that the app mount boundary still holds;
- tests and checks run;
- remaining gaps;
- whether AWS/deploy work remains planning-only or needs a separate
  `.agentic/aws/` workflow.
