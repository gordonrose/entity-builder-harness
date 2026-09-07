<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.plan.platform-runtime-implementation
version: 19
status: active
layer: 03.product
domain: platform-runtime
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
- id: product.workflow.platform-runtime-implementation
  path: .agentic/03.product/workflows/platform-runtime-implementation.md
- id: infra.04-deploy.03-product.platform-shell.deploy-blueprint
  path: infra/04.deploy/03.product/platform-shell.deploy-blueprint.yml
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

This plan proves individual platform-shell slices. The authoritative
definition of what must be complete before a public production target is called
operationally ready is
`production-reference-target-baseline.md`. A local slice in this plan may be
implemented while its corresponding reference-target capability remains
incomplete.

The immediate scope remains the platform shell and `apps/platform-smoke` only.
It must not be expanded into a human-identity, tenant-membership,
identity-and-access, user-profile, or other business application merely because
those future consumers will reuse platform capabilities. The production
reference baseline records those requirements separately until the platform
proof is complete and product/application work is deliberately started.

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

`.agentic/03.product/workflows/platform-runtime-implementation.md` governs
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
| `platform/server` | HTTP process, bounded transport, middleware order, route adaptation, health routes | Local smoke server with dummy app |
| `platform/workers` | Worker entrypoint, app mounting composition root, job registry, retry/dead-letter mechanics, shutdown | Local worker smoke with dummy job |
| `platform/security` | Auth parsing hook, token/session validation contracts, permission enforcement, CORS/rate-limit policy surfaces | Denied and allowed route tests |
| `platform/observability` | Structured logging, redaction, metrics/tracing hooks, request/job ids | Safe log and metric assertions |
| `platform/health` | `/livez`, `/readyz`, health aggregation, dependency readiness | Local and container health smoke |
| `platform/config` | Startup config loading, namespaced app config schemas, environment validation | Invalid config fails before listen |
| `platform/adapters` | Provider-specific runtime clients where needed, organized as provider/type/service | Adapter contract tests before cloud use |
| `products/kanbien-platform` | First product composition target that names which apps form the Kanbien Platform | Product manifest validation and mount/smoke proof |
| `infra/**` | Container image, IaC, environment values, deployment metadata, policy checks | Static, policy, image, and smoke checks |

### Deferred Target Shapes

The first shell proves the HTTP server and provider-neutral worker mechanics.
Two additional process targets are intentionally deferred until a real product
or operational use case requires them:

| Future target | Purpose | Current status |
| --- | --- | --- |
| Scheduler | Trigger app-owned, time-based work such as a nightly cleanup, weekly report, or hourly integration sync. It should create a standard job delivery rather than embed business work in scheduling mechanics. | No scheduler contract, runtime, entrypoint, provider adapter, or cron resource exists yet. |
| Product/operator CLI | Run a deliberate, one-shot product or operator command with validated input, explicit authority, tenant scope where applicable, audit evidence, and predictable exit status. | No product CLI contract, entrypoint, or deploy target exists yet. Harness and development scripts are not product CLI targets. |

Neither target is required to start ordinary application-layer work. Do not add
empty packages merely to reserve their names. Introduce each only after its
first concrete use case and follow the deferred milestone below.

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
`.agentic/03.product/workflows/platform-runtime-implementation.md`.

Acceptance:

- The workflow names use cases, required gates, stop conditions, and output.
- It requires platform contract tests, type checks, boundary checks, and
  session-log evidence for each implementation slice.
- It states that AWS deploy execution uses `.agentic/aws/` workflows and is not
  authorized by product implementation approval.

### 2. Harden `platform/contracts`

Finish the app-facing contract surface before server and worker internals.

#### Contract source-organisation direction

The existing public contract source is intentionally a single package entry
point, but its implementation should be organised by responsibility before it
becomes harder to scan and safely change. This is a source-organisation plan,
not a new public API: consumers continue to import only from
`@kanbien/platform-contracts` through its deliberate `index.ts` barrel.

| Proposed source topic | Owns | May depend on |
| --- | --- | --- |
| `errors.ts` | Stable contract error vocabulary and error constructors. | Core shared JSON/value vocabulary only. |
| `identifiers.ts` | App, route, job, health, and API-version names plus their constructors. | Core brands/results and contract errors. |
| `flags.ts` | Feature-flag name, context, reader, and fixed test reader. | Core identity/context vocabulary and identifiers. |
| `contexts.ts` | Composed runtime, request, and job contexts. | Core contexts plus feature-flag and identifier contracts. |
| `routes.ts` | HTTP method, request/response, route handler/registration, and route auth, tenant, and resource-authorisation declarations. | Core auth/authz/validation plus identifiers and contexts. |
| `jobs.ts` | Job handler and job-registration declarations. | Core queue/validation plus identifiers and contexts. |
| `app.ts` | Permission, health, lifecycle, mount dependencies, app registry, app declaration, and app-definition helper. | Core ports plus route, job, flag, identifier, and error contracts. |
| `validation.ts` | Registration validators, reserved-route rules, and private validation helpers. | The declaration topics and error vocabulary; it must not own runtime execution. |
| `index.ts` | Deliberate public re-exports only. | The topic files only. |

Keep validation as a consumer of declarations rather than letting route, job, or
app declaration files import their own cross-registration validators. This
preserves a one-way shape: foundational vocabulary first, declarations next,
cross-declaration validation after, then one public barrel. Do not create
public topic subpath imports during this compatibility-preserving refactor.

Status: implemented for the current source surface. The public package export
remains `@kanbien/platform-contracts`; the package README owns the current
file-level responsibility map and verification route.

The topic map covers current app-to-runtime contracts only. It must not absorb
the broader architecture being planned elsewhere:

| Concern discussed in this learning session | Correct owner | Why it stays out of `platform/contracts` |
| --- | --- | --- |
| Portable audit events, authorization vocabulary, queue/event records, correlation, and causation | `packages/core` | These are reusable nouns and ports, not one platform's registration shape. |
| Security decisions, safe operational helpers, and the future durable audit/security/operational record pipelines | `platform/security`, `platform/observability`, and the deferred record-pipeline milestone | They are runtime mechanics and provider-wiring concerns, not app declaration types. |
| App/product capability purpose, policy references, LLM discovery descriptions, data classifications, and record-profile selection | Future app/product-harness capability declaration profile | They express product meaning and governed usage; LLM fields remain non-authoritative. |
| Tenant membership, role/group assignments, resource-policy rules, and business authorization decisions | App/product policy boundary | The platform receives a declared requirement and invokes approved authorization mechanics; it does not own live product policy. |
| Encryption provider, key material, residency implementation, retention resources, log/audit store, and SIEM selection | Deployment target profile, adapters, and infrastructure | They require target/provider choices and must not enter generic platform or app contracts. |

Acceptance:

- Contracts cover app identity, mount dependencies, route registration,
  permission declarations, job registration, health registration, app config
  schemas, lifecycle hooks, request context, job context, feature flag reader,
  and cancellation.
- Invalid identities, duplicate registrations, reserved paths, unknown
  permissions, and malformed route/job declarations are represented as stable
  errors.
- Existing `platform/contracts` type and runtime tests pass.
- The source split preserves the existing public barrel import, runtime
  behaviour, exported names, contract-test coverage, and dependency boundary;
  each topic file has a package README entry once it exists.

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

#### Runtime source-organisation follow-up

Status: implemented for the current provider-neutral surface. The runtime
implementation is organised into `errors.ts`, `registry.ts`, `contexts.ts`,
and `lifecycle.ts`, with `index.ts` retaining the existing
`@kanbien/platform-runtime` public barrel. The split makes four distinct
responsibilities visible without adding a target, provider, or product
capability:

- `errors.ts` owns stable runtime and mount failure vocabulary;
- `registry.ts` owns whole-catalogue validation, app-scoped registration, and
  app-mount orchestration;
- `contexts.ts` owns request/job runtime facts and safe dependency defaults;
  and
- `lifecycle.ts` owns ordered process start, readiness, drain, close, and
  telemetry-flush coordination.

The split preserves the public import, exported names, registration behaviour,
and lifecycle sequencing. Local topic files are an internal navigation aid,
not supported public subpath APIs. The package README and source README map
the responsibilities and dependency direction. Existing runtime type,
declaration-build, behavioural, and import-boundary checks remain the baseline;
server, worker, and smoke-app checks prove that public-barrel consumers remain
compatible.

Future work must keep this separation. Do not combine source reorganisation
with a new server transport, queue provider, lifecycle phase, global registry,
or product dependency-injection container without a separate governed slice.

Acceptance:

- Runtime registries validate apps before serving traffic or running workers.
- Each server or worker process builds and validates its own registry during
  startup, before it becomes ready; the platform does not mutate a live
  registry to apply a contract change.
- An incompatible registration prevents only the new process version from
  becoming ready. Deploy targets must retain healthy prior capacity and provide
  rollback according to their governed deployment strategy; those traffic and
  capacity controls belong to deployment/infra rather than the registry.
- Contract, identifier, route, permission, and queue-message migrations that
  can span old and new process versions use an explicit compatibility sequence:
  add compatible acceptance first, deploy consumers that can handle both
  versions, begin producing the new value, migrate callers or target mappings,
  and retire the old value only after evidence shows it is unused. Do not
  silently rewrite identifiers inside a live registry.
- Runtime and reusable test-helper coverage scope every app mount to its
  validated app ID. An app may register permission, route, job, and health
  names in its own `<app-id>.` namespace; a syntactically valid declaration in
  another app's namespace is rejected with
  `PLATFORM_CONTRACT_NAMESPACE_MISMATCH`; and cross-app duplicates remain
  rejected. The current repository migration directly replaces the smoke app's
  `smoke:read` with `platform-smoke.smoke:read`, without a legacy alias,
  because it has no deployed target mapping, durable grant corpus, or
  overlapping process version to support. A future live migration must use the
  explicit compatibility sequence above. These tests mount representative apps
  through the public contract without starting an HTTP server, worker, queue,
  or identity provider.
- Request and job context factories compose shared facts without becoming app
  service locators.
- Resource lifecycle supports startup, readiness false on shutdown, request/job
  draining where applicable, app hooks, resource closing, telemetry flush, and
  deterministic exit.
- Unit and integration tests prove failure modes and shutdown ordering.

### 5. Build The Server Shell

Add the HTTP runtime entrypoint and app route adaptation.

Status: implemented for the provider-neutral server shell. The generic server
receives a product-composed app list; it is not the place that imports a
particular product's app modules. The first target composition entrypoint is
`infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts`, which
selects `products/kanbien-platform` and its approved Cognito authentication
adapter. Generic `platform/server` remains unaware of either selection.

#### Target Composition Is A Complete Capability Inventory

A target composition entrypoint is an assembly and accountability point for
*all* target-selected capabilities, not an authentication-only file. It must
make each selected capability and its failure boundary traceable, whether the
selection is expressed as a TypeScript adapter, a target configuration value,
or an infrastructure-hosted facility.

For every target-relevant capability, record the following before a target is
called ready: the platform port or contract (where one exists), selected
provider or host-delivery mechanism, composition owner, provisioned
infrastructure, failure behaviour, and readiness evidence. The baseline
inventory includes authentication/authorisation, observability export and
record delivery, shared rate limiting, trusted client-address resolution,
queues and workers, persistence/storage, configuration and secret delivery,
feature flags, and durable audit/security records.

Not every integration should be forced into a TypeScript provider adapter. For
example, structured logs written to stdout may be collected by the container
host, and secrets may be injected by the deployment target. Those are still
explicit target choices with evidence and failure behaviour; a generic helper
or an ECS deployment must not be treated as proof that the capability has been
selected, secured, or operated.

Current state is intentionally incomplete and must remain visible:

| Capability | Current generic mechanism | Target-selected evidence | Readiness position |
| --- | --- | --- | --- |
| Authentication | platform security contracts and Cognito adapter | Kanbien target composition selects Cognito | selected for the current shell |
| Observability | safe structured records, logging, metric/trace seams | no external exporter/sink adapter selected | not a complete production observability path |
| Rate limiting | bounded in-memory limiter | no durable shared adapter or ingress address resolver | blocks public multi-replica readiness |
| Queue processing | provider-neutral worker/job mechanics | no queue provider selected | deferred target/adapter slice |
| Configuration and secrets | process configuration contracts | target host can inject values; no secrets-manager adapter selected | target-specific evidence still required |
| Durable audit/security records | normalised record contracts | no durable provider/sink selected | deferred target/adapter slice |

Do not create empty provider packages simply to make this table look complete.
Create a bounded adapter/target decision only when a capability has a chosen
provider, owner, acceptance criteria, and readiness proof.

Acceptance:

- `platform/server/main.ts` or an approved entrypoint performs deterministic
  startup: load config, create logger/resources, mount apps, validate
  registries, create server, install middleware, register health, register app
  routes, listen, and install shutdown handlers. A failed listen returns a
  stable startup failure and returns lifecycle state to shutdown rather than
  leaving a false-ready process behind.
- A product/deployment composition entrypoint is the only server-side importer
  of a particular product's approved public app modules and selected adapters.
  Generic `platform/server` accepts the composed list and must not import app
  internals, product modules, provider adapters, or target profiles.
- Middleware order covers request id, logging, CORS/security headers, parsing,
  rate limiting, auth, context, authorization, validation, handler execution,
  error mapping, and response logging.
- Local smoke proves `/livez`, `/readyz`, the dummy route, a real listener,
  malformed/oversized request handling, explicit method rejection, CORS
  preflight, request-ID ownership, and graceful listener draining.

### 5a. Harden The HTTP Transport Before Any Public Exposure

Status: implemented for the provider-neutral Node transport. This is a
separate concern from route policy: a request must first become a bounded,
well-formed, cancellable platform request before authentication or an app
handler consumes work.

The current transport has the following enforced baseline:

- It permits only declared platform methods (`GET`, `POST`, `PUT`, `PATCH`,
  `DELETE`, and explicit `OPTIONS`); an unknown method is never silently
  treated as `GET`.
- It gives every request a valid correlation/request ID, preserves a valid
  upstream ID, and prevents an app handler from replacing platform-owned
  request, CORS, or security headers.
- It performs rate-limit admission before body reading and JSON parsing, then
  applies a second authenticated-principal limit when a verified principal key
  is available.
- It bounds request body size, header size/count, header/request/handler time,
  concurrent work, and requests per socket. It accepts a non-empty body only
  for body-carrying methods with a JSON media type, and maps invalid JSON,
  unsupported media type, and over-limit input through the same safe error
  response/log/metric path. A handler that ignores cancellation after its
  timeout retains its concurrency slot until it settles, so a timeout cannot
  become a parallel-work bypass.
- It uses exact-origin CORS, emits `Vary: Origin` for an allowed origin, handles
  valid preflight explicitly, and has one response-header owner.
- It supplies a cancellation signal to the runtime context. Shutdown first
  makes readiness false and stops accepting new work, then drains existing
  requests for a bounded period before cancelling/closing the remainder.
- It uses only the Node socket peer address. It never trusts an unverified
  `X-Forwarded-For` or similar caller-controlled header.
- It bounds the local in-memory limiter's keyspace. It hashes bearer tokens
  before a token-derived key is used and does not log the token itself.

The following are explicit public-exposure gates, not TODOs hidden in generic
server code: a multi-replica/public target must select and inject a durable
shared rate-limit adapter, define a trusted-ingress client-address resolver,
set target-appropriate transport limits, and prove edge/WAF/ingress policy.
Those are deployment target and adapter decisions; choosing Redis, an AWS
service, a proxy trust list, or cloud resources without that approved target
slice would violate the platform boundary. The default in-memory limiter is
per-process and is not evidence that a target has a shared quota.

Acceptance:

- Listener-level tests prove the baseline controls above, rather than only
  passing already-normalised request objects to `shell.handle`.
- The generic package remains provider-neutral and cannot import app internals,
  provider SDKs, cloud infrastructure, or an identity adapter.
- Target readiness treats a shared rate-limit adapter and trusted ingress
  address policy as mandatory before an internet-facing deployment is marked
  ready.

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
  idempotency hook, logs, metrics, health, and graceful shutdown. They also
  prove that a retry preserves the originating correlation ID, identifies its
  own delivery attempt, and—when a retry fact is emitted—links to the one
  immediately preceding failed attempt rather than an unstructured list of
  parent identifiers.
- Before a job with repeatable external effects uses durable delivery, name its
  idempotency key, tenant/product scope, durable claim or record, concurrent
  worker behaviour, expiry/reconciliation policy, and the atomic boundary with
  the external effect. The current post-success in-memory hook is a test-shell
  baseline, not an exactly-once processing guarantee; a crash between an effect
  and its recorded key needs a product-specific reconciliation strategy.

### 6a. Defer Policy-Controlled Dead-Letter Remediation

Status: deliberately deferred. A future platform capability may inspect
dead-lettered messages and recommend or perform a tightly bounded remediation.
It is not part of the first worker shell and must not be treated as an
unrestricted autonomous agent.

The capability's first responsibility is diagnosis: normalize the failure into
safe operational evidence such as app id, job name, failure class, attempt
history, message id, correlation id, deployment version, and a redacted
payload summary. It can then consult an approved product- and target-specific
remediation policy. That policy, not a language model or the queue itself,
decides whether the allowed outcome is to leave the item quarantined, open or
enrich a human alert, propose a runbook action, replay one message, or perform
another narrowly specified response.

The later capability may use a bound agent for investigation and explanation,
but the agent must receive only the evidence and tools that its remediation
policy permits. It must not receive broad production credentials, raw secrets,
unbounded queue access, or authority to change application code, identity
policy, infrastructure, or tenant data.

Remediation actions have different risk levels:

- Read-only classification, evidence gathering, and a recommended human action
  may be automated when logs and payload summaries are redacted and retention
  rules are respected.
- A single-message replay may be automated only for a policy allowlisted job
  type with proven idempotency, an explicit retry/replay limit, a safe current
  schema/version check, tenant-safe context, audit recording, and a kill
  switch.
- Payload repair, schema transformation, access-policy changes, and any action
  involving financial, personal, or otherwise sensitive tenant data require a
  human approval path unless a later, explicitly approved policy says
  otherwise.
- A queue purge is consequential. "Clear this event type" must mean an
  explicitly selected, policy-allowlisted set of messages with a recorded
  reason and approval; it must never silently mean purging every message in a
  shared DLQ.

Ownership remains layered: `platform/workers` owns provider-neutral DLQ
inspection and remediation mechanics; queue adapters own provider translation;
apps own job meaning and idempotency guarantees; products and deployment target
profiles own the allowlists, approvers, retention/residency constraints,
on-call destinations, and environment-specific operational policy. The
remediation capability must use the same tenant and authorization boundaries as
the original job and must not use one tenant's evidence to diagnose another's.

Before implementation, record a dedicated design and a testable policy model
covering failure classifications, allowed actions, role/approval requirements,
least-privilege queue access, redaction, audit events, replay safeguards,
rate/concurrency limits, dry-run mode, stop/kill switch, alert routing,
operator runbooks, and incident escalation. Begin with a read-only reporter
and supervised recommendation path; add automated re-drive only after a
specific job class has the required idempotency and operational proof.

Acceptance for the eventual slice:

- A DLQ item can be classified without exposing its raw sensitive payload in
  logs, prompts, alerts, or dashboards.
- Each proposed or executed action has an explicit policy decision, an actor,
  evidence references, tenant scope, and immutable audit record.
- Unsupported, ambiguous, high-impact, or policy-denied cases remain
  quarantined and alert an appropriate human with a recommended next action.
- Automated replay is limited to explicitly allowlisted message classes and
  stops safely when limits, verification, or idempotency evidence fail.
- Tests prove that the capability cannot cross tenant scope, purge a shared
  queue by default, access secrets, or perform a mutation outside its bound
  policy and tool permissions.

### 6b. Defer Scheduler And Product/Operator CLI Targets

Status: deliberately deferred. The current platform does not yet contain a
scheduler runtime, a scheduler entrypoint, a product/operator CLI, or their
deployment targets. Existing harness and development scripts remain harness
tools; they must not be presented as product runtime commands.

The scheduler and CLI serve different arrival models:

| Target | Starts because | Normal outcome |
| --- | --- | --- |
| Scheduler | A time-based trigger becomes due. | It creates or triggers a registered app-owned job with observable delivery evidence. |
| Product/operator CLI | An authorised person or automation explicitly invokes a command. | It returns a clear success, failure, or dry-run exit status and audit record. |

For a future scheduler:

- Apps own the business schedule definition and its meaning; platform owns
  provider-neutral scheduling mechanics; infra owns the real cron, EventBridge,
  or equivalent trigger resource.
- A scheduled run should normally enter the same validated job, idempotency,
  retry, dead-letter, tenant, logging, metric, and shutdown path as other
  background work.
- Its design must state the schedule identifier, timezone, missed-run policy,
  duplicate/concurrency policy, idempotency key strategy, target tenant or
  tenant-selection rule, and operator observability.
- Decide through a later target design whether scheduling is a separate
  long-running service, a provider-triggered one-shot process, or another
  explicitly governed runtime shape. Do not run an undocumented scheduler loop
  inside the HTTP server process by default.

For a future product/operator CLI:

- Keep command semantics app- or product-owned. The platform may provide
  composition, config, logging, safety, and audit mechanics, but it must not
  become a bag of product administration commands.
- Require a public command contract with input validation, explicit
  interactive or machine authority, tenant scope where relevant, redacted
  output, safe exit codes, audit evidence, and dry-run or confirmation controls
  for consequential actions.
- Use a target-specific composition entrypoint to inject the selected adapters
  and product configuration. A CLI must not import provider SDK clients or
  app internals ad hoc.
- Treat a command that can replay messages, alter tenant data, manage users, or
  change security policy as a high-impact operation requiring least privilege,
  explicit approval/audit policy, and a dedicated design slice.

Before either target is implemented:

1. Record the first concrete app or operator use case and its ownership.
2. Confirm whether a stable core scheduler or command contract is required;
   use the owning core/product governance before changing shared contracts.
3. Define the provider-neutral platform port/runtime behaviour and narrow
   adapter boundary.
4. Define the target composition entrypoint, target-profile configuration,
   authentication/authority model, tenant/residency implications, logs,
   metrics, health where applicable, and shutdown/rollback behaviour.
5. Use the appropriate deployment/AWS workflow before adding real queue,
   cron, EventBridge, IAM, container-task, or other cloud resources.

Acceptance for the eventual scheduler or CLI slice:

- The target has one explicit entrypoint and does not run implicitly inside an
  unrelated server or worker process.
- App business meaning remains outside generic platform runtime code.
- The target proves authentication/authority, tenant isolation where relevant,
  input or schedule validation, idempotency where effects can repeat,
  redacted observability, and safe failure behaviour.
- Provider-specific clients and real deploy resources stay in the adapter and
  infrastructure layers, respectively.
- The deployment target records activation, health/observability needs,
  rollback or safe disablement, and an operator runbook before production use.

Non-goals for the current shell:

- No scheduler or CLI package placeholder.
- No cron, EventBridge, queue, IAM, or cloud-resource provisioning.
- No product administration commands or business schedules.
- No reuse of harness scripts as product runtime entrypoints.

### 7. Add Observability, Security, Config, And Health Hardening

Make the shell safe enough to expose in a controlled environment.

#### Platform security source-organisation follow-up

Status: implemented for the current provider-neutral surface. The single
platform-security source file is now organised into `errors.ts`,
`authentication.ts`, `jwt.ts`, `authorization.ts`, `headers.ts`, and
`rate-limiting.ts`, with `index.ts` preserving the existing
`@kanbien/platform-security` public export. Core security and platform
security are both now internally organised, but retain their distinct roles:
Core owns reusable security vocabulary; platform owns runtime mechanisms.

The split retained public exports and runtime behaviour, including generic
RS256/JWKS verification, claim-to-permission translation, CORS/security
headers, and rate limiting. The existing type, runtime, and provider-vocabulary
boundary checks form the behaviour baseline. Local README maps document the
responsibility and dependency direction. Internal header-parsing helpers may be
shared between platform-security topic files, but are deliberately absent from
the public barrel.

Future platform-security work must retain this separation. Do not mix a
structural source reorganisation with provider selection, app-specific policy,
or new security controls without a separate governed slice.

Acceptance:

- Logging normalizes errors, framework objects, headers, provider diagnostics,
  circular values, and oversized values into redacted bounded fields.
- Health separates liveness from readiness and never exposes secret values.
- Config validation fails before listen or worker polling.
- Security hooks have defensive defaults even if first auth providers are fakes.
- Observability hooks record route/job identifiers, bounded error class,
  latency, retry count, and health state without logging secrets. Correlation
  IDs and verified tenant context may be carried only in separately approved,
  access-controlled log, trace, security, or audit fields; they must never be
  general metric labels.

### 7a. Defer Security, Audit, And Operational Record Pipelines

Status: deliberately deferred. The first platform shell has useful contract and
helper building blocks, but it must not claim that it already produces or
durably stores all security, audit, and operational records. Build these as a
future, bounded vertical slice when a real product action or operating need
requires them.

#### Current implementation boundary

| Concern | What exists now | Known gap |
| --- | --- | --- |
| Security decisions | `platform/security` performs provider-neutral authentication, permission, CORS, and rate-limit decisions. | It has no named security-record model, record-emission path, or provider sink. A denial is a decision, not yet a security log. |
| Audit events | `packages/core/audit` supplies versioned `AuditEvent` and `AuditRecorder` contracts, including actor, target, tenant, outcome, and correlation facts. | There is no `platform/audit` durable recorder, audit adapter, protected audit store, retention policy, or audit-access control implementation. |
| Operational records | `platform/observability` supplies safe field normalisation plus log, metric, and trace-field helpers. | No concrete external logging, metrics, or tracing adapter is implemented in the current shell. |
| Diagnostics | `packages/core/diagnostics` supplies bounded failure and recovery vocabulary. | It is a Core contract, not a `platform/diagnostics` service, event stream, or record store. |

The record types must remain separate:

| Record type | Meaning | Semantic owner | Future runtime writing path |
| --- | --- | --- | --- |
| Security log | A safe record of a security-relevant control outcome, such as an authentication failure, rate limit, or permission denial. | `platform/security` decides which outcomes merit a signal. | `platform/observability` writes a redacted record through an approved observability or security-monitoring adapter. |
| Audit event | Durable accountability evidence of who did what, to which target, in which tenant/context, at what time, and with which outcome. | Apps/products decide which actions—such as `invoice.export`—are accountable; Core owns the portable event contract. | A future `platform/audit` implements `AuditRecorder`; an approved audit adapter persists the event to the chosen durable store. |
| Operational record | A safe diagnostic record, metric, or trace used to understand runtime health and behaviour. | `platform/observability`. | An approved observability adapter exports it to the selected logging, metric, and tracing services. |
| Diagnostic fact | A bounded classification such as `authorization` or `provider` timeout that may enrich another record. | `packages/core/diagnostics`. | It is attached safely to an appropriate record; it has no independent store. |

One request may create more than one record, linked by a correlation ID. For
example, a denied invoice export may produce a security log and, where policy
requires, an audit event; its latency and status also produce operational
telemetry. The records must not be treated as copies of one another.

#### Ownership and non-goals

- Core owns provider-neutral record vocabulary and ports. It must not select a
  log vendor, audit store, SIEM, retention schedule, or cloud SDK.
- Platform owns safe runtime decisions, redaction, and wiring. It must not hide
  a durable audit implementation inside ordinary logging or turn diagnostics
  into a fourth record store.
- Apps and products own product action meaning and choose which actions require
  audit evidence. They must not import provider SDKs or persist audit rows
  directly.
- Adapters translate approved providers at
  `platform/adapters/<provider>/<adapter-type>/<service-name>/`; a future audit
  adapter belongs under the `audit` adapter type, while log/metric/trace
  adapters belong under `observability`.
- Infrastructure owns provider resources, encryption, access controls,
  residency, retention, alerting, and backup or immutability controls as the
  selected provider requires.
- Do not add empty `platform/audit`, `platform/diagnostics`, security-event,
  or provider-adapter packages merely to reserve names.
- Do not store runtime audit records, raw operational telemetry, secrets, or
  scanner output in Git or `commitLogs`; session logs record change history and
  future assessment summaries, not runtime evidence stores.

#### Missing record-profile and sequencing rules

Security controls may continue to make provider-neutral decisions without an
observability provider. Before those decisions emit security records, however,
establish a minimum provider-neutral observability seam: composed logger,
metric, and trace hooks; correlation propagation; shared redaction and bounded
field normalisation; no-op or in-memory test sinks; and explicit safe behaviour
when the sink is unavailable. `platform/security` must not call a provider or
hide a direct security-log sink.

For each capability, define separately whether it needs an audit profile, an
operational-observability profile, a security-signal profile, or none of these.
The profiles may share only explicitly safe stable references, such as a
capability/action identifier, outcome, and correlation identifier. They must
not copy a durable audit payload into logs, metrics, or traces.

Correlation identifies records that belong to one logical request or workflow;
causation identifies the immediately preceding event or message that directly
led to a downstream record. A future slice must preserve correlation through
the request, queue, worker, audit, and observability boundaries, while adding a
causation link only for a true direct parent. Core events and queue messages
already name both values, but the current audit contract exposes correlation
only and the worker runtime does not yet propagate queue-message causation into
its job context. Do not imitate causation with unstructured audit metadata;
govern the required Core and platform contract change when a real consumer
needs it.

The future audit slice needs a fixed envelope and a versioned action-profile
registry. The envelope supplies the accountable anchors; each action profile
allowlists only its narrowly defined extra facts, including purpose,
classification, permitted values, length/cardinality bounds, and retention
justification. Unknown extra fields must be rejected before persistence rather
than accepted through an unbounded metadata map.

The first slice must also settle the following before treating the profile as
complete:

- An audit event has an explicit actor and target; a tenant is mandatory when
  the action belongs to a tenant, while tenantless system/global actions are
  deliberate rather than accidental omissions. Bulk actions must use a bounded
  parent target or scope reference, not a list of sensitive target values.
- If a worker or agent acts for a person, the eventual contract represents
  both the executing identity and the authorised initiating identity. A chat
  prompt, voice transcript, or model output is never proof of actor identity
  and must not be inserted as unstructured audit metadata.
- The current proposed taxonomy remains planning-only until a first consumer
  and shared Core/product governance adopt it: event types follow
  `<app>.<resource>.<verb>`; actor type, interaction channel, and execution
  context are separate dimensions. The initial Core audit outcomes remain
  `succeeded`, `denied`, or `failed`; a future operational record vocabulary
  may add distinct lifecycle outcomes such as `accepted`, `rejected`,
  `cancelled`, `timed_out`, and `retried` only through a versioned contract
  change. The controlled action vocabulary starts with resource lifecycle
  (`create`, `read`, `list`, `search`, `update`, `delete`, `archive`,
  `restore`), relationship/access (`assign`, `unassign`, `grant`, `revoke`),
  decision/state (`approve`, `reject`, `enable`, `disable`, `publish`,
  `unpublish`), data movement (`upload`, `download`, `import`, `export`),
  workflow (`submit`, `cancel`, `execute`, `schedule`, `retry`),
  identity/security (`authenticate`, `verify`, `reset`, `recover`, `rotate`),
  and generation (`generate`). A genuinely distinct action is a reviewed
  vocabulary change, never a feature-local free-form string. The
  product-harness plan—not this generic platform milestone—owns chat and voice
  interaction design.
- Metrics may use only reviewed low-cardinality dimensions, such as app,
  capability/route/job identifier, bounded outcome, bounded source,
  deployment version, dependency name, or tenant tier. Tenant, user,
  principal, resource, request, correlation, trace, session, token, raw path,
  URL, IP, and error-message identifiers must not become shared metric labels.
  The current Core metric-label guard already rejects several unsafe identity
  and request labels, but it does not yet prove every tenant-ID spelling is
  rejected; extend that guard and its tests before a metrics exporter is
  selected. Tenant-scoped investigation and usage reporting require a
  separately access-controlled audit, security, log-search, or usage-record
  path, not an unbounded global metric dimension.
- A correlation ID links the whole logical request or workflow; a future trace
  ID and parent/child span identifiers describe one timed execution path within
  it. Trace attributes follow the same redaction and bounded-field rules as
  logs. Sampling may retain failed and unusually slow traces plus a bounded
  successful sample, but audit events and required security evidence must
  never depend on trace sampling.
- Retention must be scheduled by record class, purpose, region, readers,
  expiry, and legal-hold needs. Where tamper-evidence is required, define the
  protected key or anchor owner, integrity-verification schedule, and alert or
  investigation response; do not adopt a blockchain or a provider merely by
  describing the property.

#### Preconditions for the future vertical slice

Before implementing any record pipeline:

1. Name the first concrete product or operating use case, its accountable
   actions, security signals, tenant scope, data classification, and owner.
2. Confirm whether the existing Core contracts are sufficient; govern any
   shared contract change separately and preserve audit schema versions.
3. Select the target provider only through a deployment target profile and
   record durability, append/tamper-resistance expectations, encryption,
   access control, residency, retention, legal-hold/export, alerting, and
   incident-response requirements appropriate to the risk.
4. Define the fixed envelope, action-profile registry, separate record
   profiles, and a small redacted field taxonomy. Prove they reject unknown
   fields, secrets, tokens, raw credentials, raw request bodies, unnecessary
   PII, and unbounded provider objects.
5. Compose the provider-neutral platform writer through an adapter, then let
   infra provision the corresponding resource. Do not choose the provider in
   app or generic platform code.
6. Prove permitted and denied paths, tenant isolation, correlation and direct
   causation where applicable, recorder failure behaviour, redaction, and
   retention/access assumptions before calling the slice complete.

Acceptance for the eventual vertical slice:

- Security-relevant decisions can emit a named, redacted signal without
  exposing secrets or sensitive payloads, through the shared observability seam
  with defined failure behaviour.
- Accountable actions produce versioned audit events with explicit actor,
  target, tenant/context, action, outcome, timestamp, and correlation facts;
  only the fixed envelope and action-profile-allowlisted fields persist.
- Audit records reach an access-controlled, append-oriented durable store with
  risk-appropriate tamper-resistance, retention, export, and residency proof.
- Where tamper-evidence is required, scheduled verification proves the audit
  integrity mechanism and routes failures to a named investigation or alert
  path.
- Operational logs, metrics, and traces remain separate from audit storage,
  use bounded/redacted fields, and can be correlated without duplicating
  sensitive data.
- Diagnostic facts can enrich records without becoming a separate unbounded
  telemetry channel.
- Provider selection and resource provisioning remain confined to adapter,
  target-profile, and infrastructure boundaries.
- Tests prove redaction, denial/approval outcomes, tenant isolation, recorder
  failure handling, unknown-field rejection, correlation/causation propagation,
  delegation representation where applicable, and safe behaviour when a
  provider is unavailable.

### 8. Add Container And Infra Blueprint

Prepare the shell for repeatable deployment without putting provisioning in
platform.

Acceptance:

- Provider-neutral infra requirements name server, worker, health, logs,
  secrets, config, queues, storage, DNS, TLS, alarms, rollback, and cost limits.
- The first product shell deployment project may expose server traffic first,
  but its project shape must reserve sibling server and worker process targets
  so a worker can be added later without renaming the product target.
- Deployable image definitions live under a governed infra image boundary such
  as `infra/03.product/platform-shell/image/Dockerfile`.
- The Dockerfile has a sibling README and effective ignore file.
- Image smoke proves startup and health endpoints.
- IaC or governed equivalent ownership is named before production readiness.

Current status (2026-09-06): the deployable JavaScript payload is proven to
start with generated package shims even when its TypeScript workspace links are
hidden. The target has a tested DynamoDB shared limiter, a target-owned
ALB-only client-address resolver, explicit transport limits, two statically
checked CloudFormation templates, and AWS template validation. The real local
container-engine smoke now passes with the intended read-only filesystem,
temporary `/tmp`, dropped Linux capabilities, and liveness/readiness checks.
No AWS resource has been created by this work.

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

Kanbien staging target-planning direction: build the initial platform shell
deployment project as server-first but worker-capable. The first public target
may deploy only the HTTP server behind the ALB, but the target profile should
reserve sibling names and configuration slots for a future worker ECS service,
task family, queue adapter, log group, alarms, and rollback proof. The worker
remains deferred until a real background workload or app-declared job requires
it.

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

The current target-specific implementation lives in
`infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/`. The
foundation template creates only new platform-shell resources and treats the
existing ALB, certificate, hosted zone, cluster, ECR repository, and Cognito
configuration as inputs. Its WAF rules are exact-host scoped because the ALB
is shared with legacy workloads. The service template accepts only an immutable
image digest and is intentionally the only stack GitHub may update after the
human-governed foundation exists.

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
`platform/security` provides provider-neutral JWT/JWKS verification,
claim-to-permission mapping, rate-limit keying, and mounted-app permission-map
validation. The Cognito adapter at
`platform/adapters/aws/auth/cognito/` owns Cognito issuer/JWKS construction,
access-token claim requirements, `cognito:groups` extraction, and
Cognito-named environment parsing. The target-specific Kanbien Platform
entrypoint composes that adapter into `platform/server`; generic
`platform/server` only accepts the resulting authentication hook, denies
authenticated app routes by default, and converts a complete authenticated
`PlatformAuthenticationResult` into the core `Principal` that
`platform/runtime` places on authenticated route `context.principal`. Public
and unauthenticated routes do not receive a principal. The platform now has an
opt-in provider-neutral tenant-context and resource-authorization seam:
routes without either declaration preserve the permission-only path, while a
route that declares a required tenant or resource decision fails closed if its
resolver or `Authorizer` is absent. Tenant/locale derivation and product-specific
profile, membership, and role enrichment remain separate app or identity-boundary
work. The Kanbien staging Cognito user pool/client, exact CORS origin,
non-secret task configuration, and product permission source are now recorded
in the target profile and mirrored by the service template. Public deployment
remains blocked on a reviewed foundation change set, deployment IAM-policy
update, official image provenance, and deployed protected dummy-route smoke
proof.

#### Cognito Operational Readiness Is Separate From The Adapter

The Cognito adapter proves the code-level identity boundary: issuer/JWKS
construction, access-token requirements, provider claim extraction, and
translation into provider-neutral platform facts. It is not a complete
operating model for an identity service.

The Kanbien staging target profile already records an initial provider, user
pool, confidential machine-to-machine app client, scope mapping, client-secret
storage location, and CORS intent. Its readiness manifest remains blocked.
Before internet-facing readiness, the target must also make the following
operational choices explicit and prove them:

- **Exposure and identity model:** the present target is machine-to-machine.
  A later human-user/tenant/group model is a distinct decision and must define
  its membership source, lifecycle, and resource-authorisation contribution;
  it is not supplied merely by Cognito group parsing.
- **Lifecycle and recovery:** owner, provisioning/change control across
  environments, app-client and secret injection, secret rotation, credential
  revocation/disablement, emergency access, and a recovery/rollback procedure.
- **Token and key behaviour:** allowed token use and audience/client binding,
  token lifetime and the consequence that a valid bearer token normally remains
  valid until expiry, clock-skew policy, JWKS cache refresh/rotation/failure
  behaviour, and an incident response for compromised credentials or keys.
- **Authorisation governance:** reviewed claim/group/scope-to-permission maps,
  least privilege, a controlled change path for grants, and an explicit
  separation between platform permission mapping and app-owned tenant,
  membership, region, clearance, or resource decisions.
- **Abuse and boundary controls:** shared rate limiting, trusted ingress client
  address resolution, CORS/exposure policy, IAM least privilege, network
  controls, and TLS/secret-at-rest controls.
- **Evidence and operation:** safe authentication/audit records without raw
  tokens, monitoring and alert ownership for authentication/JWKS failures or
  abuse, retention/access policy, deployed protected-route smoke, and rollback
  proof.

These are target-profile, readiness-manifest, infrastructure, and operating
runbook concerns. Do not enlarge the Cognito adapter into an unauditable
identity-management framework. The adapter supplies the verified facts; the
target governs whether those facts can be safely relied upon in production.

#### Boundary Correction Audit (2026-08-31)

The initial local implementation placed Cognito issuer/JWKS helpers,
access-token validation, and the `cognito:groups` claim in
`platform/security`, then made `platform/server/src/main.ts` select Cognito
and parse Cognito-named environment values. This crossed the provider-adapter
boundary.

The drift was not stopped because the `platform/security` boundary test did not
recognize Cognito, AWS, or identity-provider vocabulary; this plan and AWS ADR
0002 described Cognito as hidden behind `platform/security`; the
dependency-direction rule allowed platform modules to use provider clients too
broadly; and the root workspace pattern omitted nested
`platform/adapters/<provider>/<type>/<service>` packages, so a canonical
adapter would not have been checked by normal npm wiring. The corrected slice
adds explicit provider-identity checks, adapter workspace scripts, generic
security mapping, and target-composition-only provider selection.

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
  interfaces and does not name provider issuer patterns, claim names, or
  provider configuration. Status: implemented with generic JWT/JWKS
  verification and configured claim-value mapping.
- A provider adapter owns provider issuer/JWKS helpers, token claim
  requirements, provider claim extraction, and provider-named configuration.
  Status: implemented for Cognito at `platform/adapters/aws/auth/cognito/`.
- Generic `platform/server/src/main.ts` accepts an injected authentication hook
  and has no provider adapter dependency. A target profile's approved
  composition entrypoint selects and configures the provider adapter;
  unauthenticated app routes remain denied by default. Status: implemented in
  `infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts` for
  the Cognito-selected Kanbien staging target.
- Claims, roles, groups, scopes, or entitlements map deterministically into
  platform `Permission` values. Status: generic claim-value and equality
  mapping is implemented in `platform/security`; Cognito group and scope claim
  selection is implemented by the Cognito adapter.
- Authenticated route handlers receive a provider-neutral core `Principal` on
  `context.principal`, including id, type, subject, claims, and scopes; public
  and unauthenticated routes do not receive one. Routes may opt into an
  optional or required tenant context and an app-provided resource contribution.
  Generic platform binds the verified tenant and principal to the core
  `Authorizer`; product profile, membership, role, region, clearance, and
  residency decisions remain separate gaps.
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
- Rate limiting is keyed by principal, token/session identity, or a
  target-resolved trusted client address—not an unverified forwarded header.
  The generic process-local limiter is bounded but insufficient for a public
  multi-replica target; target readiness requires a shared adapter and an
  explicit ingress-address trust policy before public exposure.
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

Current status: local product composition is implemented and its compiled
deployment payload has been started with public-target configuration. The
container-engine smoke has now passed with Docker Desktop WSL integration
available; it proves the sealed local image can start with the intended runtime
restrictions and serve its health endpoints.
`apps/platform-smoke` registers the smoke route, app-owned
permission, config schema, health check, lifecycle hooks, and queue job through
`platform/contracts`. `products/kanbien-platform` composes that app through the
public app package and publishes the product manifest used by deployment
readiness. The local app check, product check, server check, image-build
entrypoint, direct product server entrypoint smoke, runtime-payload isolation
check, container boundary check, infrastructure static-policy check, and
deploy-readiness blocked-mode check, and actual container smoke have passed.
AWS deployment, deployed protected-route smoke, GitHub deployment-role policy
update, official image provenance, and rollback proof remain blocked in the
Kanbien staging target profile.

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
| CORS or rate limits are unsafe for production | Exact-origin CORS/preflight listener tests; target-profile shared rate-limit adapter, trusted-ingress client-address policy, target transport limits, and explicit private/public exposure decision |

## Stop Conditions

- Product/platform implementation begins while `.agentic/03.product` still lacks
  real implementation governance.
- Platform code imports app internals outside approved composition roots.
- Infra code imports app internals instead of manifests or generated metadata.
- AWS mutation is requested before account/profile, region, environment,
  runtime family, service target, intended mutation, health checks, and rollback
  are named.
- A URL or DNS convention is treated as locked without an infra/AWS decision.
- Deployment readiness is claimed from local tests alone.
- Internet-facing deployment is claimed while real auth/authz provider choice,
  token/session validation, permission mapping, CORS allowlist, shared
  rate-limit adapter, trusted-ingress client-address policy, transport limits,
  health exposure policy, or auth readiness blockers are unresolved.
- Secrets, tokens, credentials, private keys, or connection strings with values
  appear in source, logs, docs, fixtures, or generated packets.

## First Slice Recommendation

Current next slice: commit and merge the reviewed platform/deployment work,
then obtain a separate explicit AWS approval to update the GitHub deployment role
and create a reviewed foundation change set. The first AWS apply must remain
server-first and worker-capable: it may create only the HTTP server resources;
the future worker retains its explicit naming/configuration slot and activation
condition but no empty worker service is deployed.
