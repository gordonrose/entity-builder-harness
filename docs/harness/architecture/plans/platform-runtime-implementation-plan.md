<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.plan.platform-runtime-implementation
version: 2
status: active
layer: 01.harness
domain: architecture
disciplines:
- architecture
- sre
- agentic
kind: plan
purpose: Define the implementation plan for proving the Kanbien platform runtime shell with a dummy app before product application work begins.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.architecture.rules.layers.platform
  path: docs/harness/architecture/rules/layers/platform.yml
- id: harness.architecture.rules.layers.infra
  path: docs/harness/architecture/rules/layers/infra.yml
- id: aws.workflows.plan-aws-change
  path: .agentic/aws/workflows/plan-aws-change.md
-->
# Platform Runtime Implementation Plan

## Goal

Build a full platform runtime shell with a dummy app before real application
layer work begins.

The shell should prove that platform contracts, app mounting, server startup,
worker startup, health, config, observability, security hooks, lifecycle,
testing helpers, container packaging, and AWS production deployment readiness
can work together without depending on product app internals.

## Locked Direction

- Apps integrate with platform through an approved public mount module, normally
  `apps/<app>/app.mount.ts`.
- Platform composition roots may import app mount modules; ordinary platform
  modules must not import app internals.
- App internals remain app-owned. A future app may organize by service,
  feature, capability, domain, use case, workflow, route, job, health, or some
  later product pattern without requiring platform changes.
- Composed request and job contexts start in `platform/contracts`.
- Infra owns resource provisioning and deployment topology. Platform owns
  runtime lifecycle and clients. Apps own product meaning.
- Provider adapters use `platform/adapters/<provider>/<adapter-type>/<service-name>/`
  so the provider boundary, platform concern, and concrete service are explicit.
- External URL shape is not locked by the platform runtime plan. The runtime
  should support host-agnostic route registration and deployment-facing
  manifests. DNS choices such as `app.domain.com` belong to infra/environment
  planning once the production target is selected.

## Non-Goals

- Do not build real CRM, billing, onboarding, customer, or entity-builder
  product behavior.
- Do not decide final app internal structure.
- Do not let the dummy app become the application architecture template.
- Do not mutate AWS or production DNS from this plan.
- Do not add Terraform, CDK, Pulumi, IAM, networking, or cloud topology under
  `platform/**` or `apps/**`.

## Governance Precondition

`.agentic/product/workflows/platform-runtime-implementation.md` governs
platform runtime implementation slices. Use it before editing runtime code,
dummy-app code, platform testing helpers, or deployment-facing platform shell
manifests.

AWS deployment work already has planning and execution workflow coverage under
`.agentic/aws/`. AWS execution remains blocked until a target account/profile,
region, environment, service target, runtime family, rollback path, and exact
mutation are approved in the current chat.

## Target Runtime Shape

The first production-shaped shell should include these modules:

| Surface | Purpose | First proof |
| --- | --- | --- |
| `platform/contracts` | App mount, registries, request context, job context, feature flags, config, health, route and job contracts | Type tests and app mount contract tests |
| `platform/testing` | Fakes for app contract tests, fake registries, fake contexts, fake queues, fake health checks | Reusable tests for valid and invalid mounts |
| `platform/runtime` | Registry validation, context factories, lifecycle, resources, error mapping, shutdown primitives | Unit and integration tests |
| `platform/server` | HTTP entrypoint, app mounting composition root, middleware order, route adaptation, health routes | Local smoke server with dummy app |
| `platform/workers` | Worker entrypoint, app mounting composition root, job registry, retry/dead-letter mechanics, shutdown | Local worker smoke with dummy job |
| `platform/security` | Auth parsing hook, permission enforcement, CORS/rate-limit policy surfaces | Denied and allowed route tests |
| `platform/observability` | Structured logging, redaction, metrics/tracing hooks, request/job ids | Safe log and metric assertions |
| `platform/health` | `/livez`, `/readyz`, health aggregation, dependency readiness | Local and container health smoke |
| `platform/config` | Startup config loading, namespaced app config schemas, environment validation | Invalid config fails before listen |
| `platform/adapters` | Provider-specific runtime clients where needed, organized as provider/type/service | Adapter contract tests before cloud use |
| `infra/**` | Container image, IaC, environment values, deployment metadata, policy checks | Static, policy, image, and smoke checks |

## Dummy App Strategy

Use a deliberately boring smoke app to exercise the public contract:

- `apps/platform-smoke/app.mount.ts` registers one route, one permission, one
  health check, one config schema, one lifecycle hook, and one background job.
- `apps/platform-smoke/app.manifest.ts` publishes deployment-facing metadata
  needed by infra without importing app internals.
- Internal files are minimal and app-owned. They exist only to prove the mount
  boundary, not to establish the real application pattern.
- The dummy route should prove request context, auth policy, permission check,
  response shaping, safe error mapping, and logging.
- The dummy job should prove job context, payload validation, retry/dead-letter
  behavior, idempotency hook, metrics, and graceful shutdown.

If implementation governance is not ready when the smoke app begins, keep the
first dummy app as a test fixture under `platform/testing` and graduate it into
`apps/platform-smoke` only after app-layer write governance exists.

## Implementation Milestones

### 0. Commit The Boundary Decision

Record the app mount boundary decision before starting runtime implementation.
The implementation plan assumes ADR 0025 and ADR 0026 are accepted.

Acceptance:

- Current decision slice is committed.
- Session log records the context packet, decision, checks, and ADR
  disposition.
- Local RAG runtime freshness passes after generated source updates.

### 1. Add Platform Runtime Implementation Governance

Create a product/platform implementation workflow or checklist before runtime
code changes begin.

Status: implemented in
`.agentic/product/workflows/platform-runtime-implementation.md`.

Acceptance:

- The workflow names use cases, required gates, stop conditions, and output.
- It requires platform contract tests, type checks, boundary checks, and
  session-log evidence for each implementation slice.
- It states that AWS deploy execution uses `.agentic/aws/` workflows and is not
  authorized by product implementation approval.

### 2. Harden `platform/contracts`

Finish the app-facing contract surface before server and worker internals.

Acceptance:

- Contracts cover app identity, mount dependencies, route registration,
  permission declarations, job registration, health registration, app config
  schemas, lifecycle hooks, request context, job context, feature flag reader,
  and cancellation.
- Invalid identities, duplicate registrations, reserved paths, unknown
  permissions, and malformed route/job declarations are represented as stable
  errors.
- Existing `platform/contracts` type and runtime tests pass.

### 3. Build `platform/testing`

Add fakes and helper builders so apps can prove mount compatibility without
real external services.

Acceptance:

- Test helpers can mount a representative app and assert registered routes,
  permissions, jobs, health checks, config schemas, and lifecycle hooks.
- Negative tests cover duplicate routes, duplicate jobs, unknown permissions,
  reserved platform paths, invalid config, and unsafe health output.
- Helpers are test-only and do not become production runtime dependencies.

### 4. Build Runtime Registries And Lifecycle

Implement provider-neutral mechanics before choosing cloud resources.

Acceptance:

- Runtime registries validate apps before serving traffic or running workers.
- Request and job context factories compose shared facts without becoming app
  service locators.
- Resource lifecycle supports startup, readiness false on shutdown, request/job
  draining where applicable, app hooks, resource closing, telemetry flush, and
  deterministic exit.
- Unit and integration tests prove failure modes and shutdown ordering.

### 5. Build The Server Shell

Add the HTTP runtime entrypoint and app route adaptation.

Acceptance:

- `platform/server/main.ts` or an approved entrypoint performs deterministic
  startup: load config, create logger/resources, mount apps, validate
  registries, create server, install middleware, register health, register app
  routes, listen, and install shutdown handlers.
- `platform/server/mount.ts` is the only server-side app importer and imports
  only public `app.mount.ts` modules.
- Middleware order covers request id, logging, CORS/security headers, parsing,
  rate limiting, auth, context, authorization, validation, handler execution,
  error mapping, and response logging.
- Local smoke proves `/livez`, `/readyz`, and the dummy route.

### 6. Build The Worker Shell

Add the worker runtime entrypoint and app job adaptation.

Acceptance:

- `platform/workers/main.ts` or an approved entrypoint starts workers through
  platform-owned queue mechanics.
- `platform/workers/mount.ts` is the only worker-side app importer and imports
  only public `app.mount.ts` modules.
- Local runtime includes an in-memory or fake queue path for deterministic
  tests before provider adapters.
- Tests prove payload validation, retry/backoff, dead-letter behavior,
  idempotency hook, logs, metrics, health, and graceful shutdown.

### 7. Add Observability, Security, Config, And Health Hardening

Make the shell safe enough to expose in a controlled environment.

Acceptance:

- Logging normalizes errors, framework objects, headers, provider diagnostics,
  circular values, and oversized values into redacted bounded fields.
- Health separates liveness from readiness and never exposes secret values.
- Config validation fails before listen or worker polling.
- Security hooks have defensive defaults even if first auth providers are fakes.
- Metrics/tracing hooks record route, job, request id, correlation id, tenant
  where available, error class, latency, retry count, and health state without
  logging secrets.

### 8. Add Container And Infra Blueprint

Prepare the shell for repeatable deployment without putting provisioning in
platform.

Acceptance:

- Provider-neutral infra requirements name server, worker, health, logs,
  secrets, config, queues, storage, DNS, TLS, alarms, rollback, and cost limits.
- Deployable image definitions live under a governed infra image boundary such
  as `infra/03.product/platform-shell/image/Dockerfile`.
- The Dockerfile has a sibling README and effective ignore file.
- Image smoke proves startup and health endpoints.
- IaC or governed equivalent ownership is named before production readiness.

### 9. Select AWS Runtime Family

Choose the production AWS runtime only after current-state inspection and a
deployment plan.

Default planning candidate: ECS Fargate, because the shell has both server and
worker processes and will likely need ALB, health checks, task definitions,
service stability, and rollback behavior. This is not a deployment decision
until an AWS plan records `runtime_family`, account/profile, region,
environment, cluster/service or equivalent target, and rollback path.

Status: implemented as planning-only. The selected runtime family is
`ecs-fargate`, recorded in
`docs/aws/architecture/adrs/0001-select-ecs-fargate-for-platform-shell-planning.md`
and `infra/04.deploy/03.product/aws-runtime-family.decision.yml`.

This selection does not make ECS part of the app contract. Future runtime
families may be added through governed adapters such as
`platform/adapters/aws/runtime/lambda/` or deployment profiles. Apps declare
provider-neutral needs through public platform contracts and manifests.

Acceptance:

- Runtime family is one governed value such as `ecs-fargate`, `app-runner`,
  `lambda`, or `eks`.
- Target-specific checks match that runtime family.
- If ECS Fargate is selected, task, network, ingress, TLS, target group,
  health, scaling, rollback, alarms, and cost boundaries are named before
  mutation.
- If a different runtime is selected, ECS-specific assumptions stay out of the
  readiness proof.

### 10. Prove Deployment Readiness

Turn planning evidence into executable or externally auditable proof before
production exposure.

Acceptance:

- Source commit, image digest, build context, base image digest, SBOM/scan or
  accepted risk record, and workflow run identity are recorded.
- GitHub-to-AWS path has a concrete workflow or governed equivalent.
- AWS target identity, secret store, environment values, runtime config,
  health checks, rollback target, rollback authority, cost controls, and
  operational owner are recorded.
- Static validation, policy checks, generated output review, image smoke,
  local runtime smoke, AWS read-only inspection, deployment smoke, and rollback
  proof are present or recorded as blockers.
- Deployment smoke verifies platform entrypoints, `/livez`, `/readyz`, dummy
  route, dummy job/queue health where applicable, logs, metrics, DNS/routing,
  and safe status output.

### 11. Declare Application Layer Ready To Start

Only start real app work after the platform shell is proven enough that app
teams can build against contracts instead of guesses.

Entry criteria:

- Dummy app can mount locally and in the deployed shell.
- Server and worker entrypoints run with the same contract model.
- Platform contract tests protect the boundary.
- Infra consumes manifests or generated deployment metadata, not app internals.
- Production target has either passed deployment readiness or has explicit
  blocking gaps that do not affect local app development.
- The app URL/DNS pattern is either intentionally deferred or recorded as an
  infra/AWS decision.

## Validation Matrix

| Risk | Required proof |
| --- | --- |
| Platform leaks app internals | Dependency-direction checks and tests around composition roots |
| App mount contract drifts | `platform/contracts` type/runtime tests and `platform/testing` helpers |
| Server starts but policies are wrong | Integration tests with denied auth, unknown permission, invalid payload, and reserved paths |
| Worker happy path hides failure modes | Retry, dead-letter, idempotency, payload validation, and shutdown tests |
| Health exposes unsafe data | Health output snapshot/assertions with secret redaction tests |
| Logs become unsafe or huge | Logging normalization tests for rich, circular, provider, and oversized values |
| Infra imports app internals | Infra boundary checks and manifest-only deployment metadata |
| Image includes local or secret files | Container boundary validation and effective ignore checks |
| AWS target is ambiguous | AWS inspect/plan evidence naming profile/account, region, environment, target, runtime family |
| Production cannot roll back | Rollback target, authority, command/workflow, and post-rollback health proof |

## Stop Conditions

- Product/platform implementation begins while `.agentic/product` still lacks
  real implementation governance.
- Platform code imports app internals outside approved composition roots.
- Infra code imports app internals instead of manifests or generated metadata.
- AWS mutation is requested before account/profile, region, environment,
  runtime family, service target, intended mutation, health checks, and rollback
  are named.
- A URL or DNS convention is treated as locked without an infra/AWS decision.
- Deployment readiness is claimed from local tests alone.
- Secrets, tokens, credentials, private keys, or connection strings with values
  appear in source, logs, docs, fixtures, or generated packets.

## First Slice Recommendation

After committing this plan, start with milestone 1. The fastest useful next
change is a focused `platform-runtime-implementation` workflow/checklist that
unblocks code work while preserving the boundaries above.
