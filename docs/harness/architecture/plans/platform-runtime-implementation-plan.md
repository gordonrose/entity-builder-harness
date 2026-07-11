<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.plan.platform-runtime-implementation
version: 3
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
- Apps own their permission vocabulary. Platform validates and enforces
  declared permissions, products compose apps, and deployment target profiles
  map provider claims, groups, roles, scopes, or machine identities to those
  app-declared permissions.
- Products compose apps. The first product composition target is
  `products/kanbien-platform`, used to bundle platform-smoke first and later
  real Kanbien apps. `kanbien/staging` is an environment/deployment target for
  dev and integration proof, not the product itself.
- Composed request and job contexts start in `platform/contracts`.
- Infra owns resource provisioning and deployment topology. Platform owns
  runtime lifecycle and clients. Apps own product meaning.
- Provider adapters use `platform/adapters/<provider>/<adapter-type>/<service-name>/`
  so the provider boundary, platform concern, and concrete service are explicit.
- Deployment target selection is profile-driven by client and environment.
  Client, source repository, cloud provider, account/subscription, region,
  runtime family, adapter, and readiness proof live in deploy target profiles
  such as `infra/04.deploy/03.product/targets/<client>/<environment>/`.
- Internet-facing deployment requires a real authentication and authorization
  provider path. Platform security hooks and fake auth tests are not enough to
  expose the shell publicly.
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
| `platform/security` | Auth parsing hook, token/session validation contracts, permission enforcement, CORS/rate-limit policy surfaces | Denied and allowed route tests |
| `platform/observability` | Structured logging, redaction, metrics/tracing hooks, request/job ids | Safe log and metric assertions |
| `platform/health` | `/livez`, `/readyz`, health aggregation, dependency readiness | Local and container health smoke |
| `platform/config` | Startup config loading, namespaced app config schemas, environment validation | Invalid config fails before listen |
| `platform/adapters` | Provider-specific runtime clients where needed, organized as provider/type/service | Adapter contract tests before cloud use |
| `products/kanbien-platform` | First product composition target that names which apps form the Kanbien Platform | Product manifest validation and mount/smoke proof |
| `infra/**` | Container image, IaC, environment values, deployment metadata, policy checks | Static, policy, image, and smoke checks |

## Dummy App Strategy

Use a deliberately boring smoke app to exercise the public contract:

- `apps/platform-smoke/app.mount.ts` registers one route, one permission, one
  health check, one config schema, one lifecycle hook, and one background job.
- Real apps should define app-specific permissions near the app mount surface,
  such as `apps/<app>/app.permissions.ts`, then register those permissions
  through `app.mount.ts`.
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

## Product Composition Strategy

Use `products/kanbien-platform` as the first product composition target.

The Kanbien Platform product should answer which app modules are bundled into
the product. Its first app is `apps/platform-smoke`; later it may add real apps
such as entity-builder, admin, billing, onboarding, or other Kanbien-owned app
modules.

The product composition target should own product identity, app list, product
manifest metadata, app enablement, and any product-level role grouping that
references app-declared permissions.

It should not own environment-specific deployment values. AWS account, region,
runtime family, auth provider configuration, CORS origins, DNS, secrets, image
digests, and readiness blockers belong in deployment target profiles such as
`infra/04.deploy/03.product/targets/kanbien/staging`.

Do not call `kanbien/staging` the product. It is the first dev/integration
target for the Kanbien Platform product.

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

Status: implemented as a blocked readiness scaffold. The platform shell staging
manifest lives at
`infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml`, and the
read-only verifier is
`scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh`.

The manifest records what is proven locally today and what remains blocked
before AWS mutation for the Kanbien staging target: source identity,
GitHub-to-AWS identity, immutable image provenance, ECS task/service targets,
AWS account/region/network/ingress/secrets/logs/alarms, operations ownership,
deployment smoke, and rollback proof.

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

### 10a. Prove Internet-Facing Auth And Authorization Readiness

Do not expose the platform shell to the public internet until a real auth/authz
path is selected, implemented, tested, and represented in deployment readiness
evidence.

Current status: locally implemented and deployment-blocked. Cognito is selected
as the first provider path in
`docs/aws/architecture/adrs/0002-select-cognito-for-platform-shell-auth.md`.
`platform/security` validates Cognito-shaped access tokens through
provider-neutral JWT/JWKS interfaces, maps groups/scopes/claims to app-declared
permissions, derives non-global rate-limit keys, and validates target authz
maps against mounted app permissions. `platform/server` wires the auth hook
from config/environment values, denies authenticated app routes by default,
supports target-profile CORS allowlists, supports explicit `/livez` and
`/readyz` exposure policy, and proves protected-route `401`, `403`, and
success paths with local mounted-smoke tests. Public deployment remains blocked
until the Kanbien staging Cognito user pool/client, CORS origins, secret/config
source, product app permission source, and deployed protected dummy-route smoke
proof are recorded in the target profile.

This milestone uses AWS Cognito for the first Kanbien staging provider path.
Future targets may choose Auth0, Clerk, a custom OIDC provider, private
network, VPN, ALB auth, CloudFront signed access, or another governed identity
boundary through a new target-specific decision. Any replacement must still
prove who can reach protected routes.

Acceptance:

- The real authentication provider choice is recorded with the reason it fits
  the target client/environment. Status: Cognito selected for Kanbien staging
  in AWS ADR 0002.
- `platform/security` validates tokens or sessions through provider-neutral
  interfaces and does not expose raw provider clients as ordinary app-facing
  APIs. Status: implemented with JWT/JWKS verification and Cognito issuer/JWKS
  helpers.
- `platform/server/src/main.ts` wires a production auth hook from config,
  target profile, or provider adapter; unauthenticated app routes remain
  denied by default. Status: implemented with `PLATFORM_AUTH_PROVIDER=cognito`
  and Cognito/JWT environment inputs.
- Claims, roles, groups, scopes, or entitlements map deterministically into
  platform `Permission` values. Status: implemented for Cognito groups,
  scopes, and claims.
- Permission vocabularies are app-owned. Target-specific authz maps may grant
  only permissions declared by the apps included in the product target, and
  startup/deploy validation must fail on unknown permissions.
- The dummy app proves protected-route `401`, `403`, and success paths through
  local tests and deployment smoke expectations. Status: local mounted-smoke
  tests pass; deployed smoke remains a readiness blocker until a target exists.
- Public and private route classification is explicit. Health endpoint exposure
  is decided for `/livez` and `/readyz` instead of assumed.
- CORS allowlists come from deployment target profiles or equivalent
  environment config, not hardcoded platform defaults.
- Rate limiting is keyed by principal, token/session identity, trusted
  forwarded IP, or an approved fallback, not only one global in-memory bucket.
- Secrets and provider config are loaded from the target profile, environment,
  or secret store without committing secret values.
- The deployment readiness manifest records auth provider, protected exposure
  policy, CORS, rate-limit keying, secret/config source, and remaining auth
  blockers before any public deployment.
- Internet-facing readiness remains blocked until these proofs pass or an
  explicit target-specific private-exposure decision replaces public exposure.

### 11. Declare Application Layer Ready To Start

Only start real app work after the platform shell is proven enough that app
teams can build against contracts instead of guesses.

Entry criteria:

- Kanbien Platform has a product composition manifest or equivalent governed
  product target that lists the apps included in the shell proof.
- Dummy app can mount locally and in the deployed shell.
- Server and worker entrypoints run with the same contract model.
- Platform contract tests protect the boundary.
- Infra consumes manifests or generated deployment metadata, not app internals.
- Production target has either passed deployment readiness or has explicit
  blocking gaps that do not affect local app development.
- Internet-facing exposure is blocked until Milestone 10a auth/authz readiness
  is complete or a target-specific private-exposure decision is recorded.
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
| Public route exposure bypasses auth | Auth provider decision, token/session validation tests, permission mapping, protected dummy route smoke, and deployment readiness auth blockers |
| CORS or rate limits are unsafe for production | Target-profile CORS allowlist, principal/IP rate-limit keying proof, and explicit private/public exposure decision |

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
- Internet-facing deployment is claimed while real auth/authz provider choice,
  token/session validation, permission mapping, CORS allowlist, rate-limit
  keying, health exposure policy, or auth readiness blockers are unresolved.
- Secrets, tokens, credentials, private keys, or connection strings with values
  appear in source, logs, docs, fixtures, or generated packets.

## First Slice Recommendation

Current next slice: work through Milestone 10a as a planning and design slice
before public deployment work. Start by choosing the first auth/authz provider
path, then update `platform/security`, `platform/server`, the dummy app tests,
and the deployment readiness manifest in small governed commits.
