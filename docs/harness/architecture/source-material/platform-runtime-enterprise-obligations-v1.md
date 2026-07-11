<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.source-material.platform-runtime-enterprise-obligations-v1
  version: 7
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  - sre
  - security
  kind: source-material
  purpose: Record platform runtime shell surfaces and deferred platform and infra runtime obligations for enterprise-grade logging, event delivery, audit, and payload handling.
  portability:
    class: required
    targets:
    - llm-workbench
    - entity-builder
    - design-system-builder
  used_by:
  - id: harness.architecture.rules.layers.platform
    path: docs/harness/architecture/rules/layers/platform.yml
-->
# Platform Runtime Enterprise Obligations v1

## Purpose

This source material records platform and infra obligations that are
deliberately outside `packages/core` contract modules but must not be lost when
the platform runtime and provider adapters are implemented.

`packages/core` defines stable provider-neutral contracts. Platform must make
those contracts durable, observable, secure, and cost-controlled at runtime.
Infra must provision the external resources, retention topology, alarms, and
permissions that the platform adapters depend on.

## Scope

These obligations apply when implementing platform runtime modules, provider
adapters, worker runtimes, durable audit recorders, event publishers, outbox
relays, log exporters, SIEM exporters, and related infra resources.

They do not require `packages/core` to import cloud SDKs, database clients,
queue clients, observability clients, ORM models, or deployment resources.

## Platform Runtime Shell Surfaces

The platform runtime shell should be easy to explain from the source material,
not only from implementation files. These surfaces are the first mental model:

- `platform/contracts/**` is the app-facing contract layer. It defines the
  types and runtime-safe shapes apps use to plug into the platform, including
  app mounts, route registration, job registration, health registration,
  request context, job context, feature flags, config access, and lifecycle
  hooks. This comes before concrete server and worker internals because apps
  should depend on contracts, not framework objects or process entrypoints.
- `platform/testing/**` is the test-helper layer for proving app/platform
  compatibility without real infrastructure. It should provide fake
  registries, fake request and job contexts, fake loggers, fake queues, fake
  health checks, and mount-test helpers. This keeps the app mount boundary
  executable before real servers, workers, cloud queues, or databases exist.
- `platform/runtime/**` is the provider-neutral runtime mechanics layer. It
  owns registry validation, lifecycle orchestration, resource startup and
  shutdown, context factories, readiness state, error mapping, cancellation,
  and graceful shutdown sequencing. It should not own HTTP framework details,
  cloud SDK clients, or product app business decisions.
- `platform/server/**` is the HTTP/API process layer. It turns registered app
  routes into real HTTP routes and owns server startup, middleware order, API
  versioning, health endpoints, request logging, auth hooks, validation, error
  responses, and shutdown wiring. `platform/server/mount.ts` may import public
  app mount modules, but ordinary server internals should not import app
  services, features, repositories, or route-handler internals.
- `platform/workers/**` is the background job process layer. It turns
  registered app jobs into real worker behavior and owns job polling or
  receiving, payload validation, retry and backoff, dead-letter behavior,
  idempotency hooks, job logging and metrics, and graceful shutdown.
  `platform/workers/mount.ts` may import public app mount modules, but worker
  internals should not import app job-handler internals directly.
- `apps/platform-smoke/**` is a deliberately boring dummy app used to prove the
  platform shell works. It can register one route, one job, one health check,
  one config schema, and one lifecycle hook through `app.mount.ts`. It is not
  the real product app and should not become the final app architecture
  template.
- Apps own their permission vocabulary. A real app should define its
  app-specific permission names near the public mount surface, register them
  through `app.mount.ts`, and use those same permissions on routes and jobs.
  Platform validates and enforces those declarations; product or target-level
  authz mapping decides which provider groups, roles, scopes, claims, or
  machine identities receive them.
- `products/<product>/**` is the product composition layer. The first product
  composition target is `products/kanbien-platform`, used to bundle
  `apps/platform-smoke` first and later real Kanbien apps. Product composition
  is distinct from deployment targets: `kanbien/staging` is an environment used
  for dev and integration proof, not the product itself.
- Deployment-facing manifests and config are declarative facts that infra and
  deployment tooling can consume without inspecting app internals. Examples
  include app name, route base path, required environment variables, health
  endpoints, worker process names, queue requirements, container port, and
  deployment smoke-test targets. Infra should consume manifests or generated
  metadata rather than scanning arbitrary app source files.

In short: contracts define what apps can say to platform; testing proves that
contract with fakes; runtime owns shared mechanics; server owns HTTP process
behavior; workers own background process behavior; the smoke app proves the
mount boundary; manifests/config publish deployment facts without leaking app
internals. Apps define permission vocabulary; platform validates and enforces
permissions; products bundle apps; target profiles map real-world identities to
app-declared permissions. Product manifests answer which apps form a product;
deployment target profiles answer where and how that product runs.

## Runtime Surface Boundaries

This section gives the more granular file-level expectations for each platform
runtime slice. These are teaching boundaries first, and rule derivation should
turn only the stable enforcement points into compact structured rules.

### `platform/contracts/**`

Purpose: define the public app-facing contract surface that platform runtime
implements and apps mount against.

Typical files:

- `app.ts` for app identity, app mount, mount dependencies, and lifecycle hook
  contracts;
- `routes.ts` for route registration, route metadata, auth requirement,
  permission requirement, handler signatures, and response shape contracts;
- `jobs.ts` for job registration, payload contracts, delivery metadata, retry
  states, and job handler signatures;
- `health.ts` for health check registration, liveness/readiness vocabulary, and
  safe health output contracts;
- `context.ts` for composed request and job contexts;
- `config.ts` for app config schema registration and provider-neutral config
  access;
- `flags.ts` for provider-neutral feature flag reader contracts;
- `errors.ts` for stable platform/app contract error vocabulary.

Allowed:

- provider-neutral TypeScript types, interfaces, small validators, and stable
  error shapes;
- imports from public `packages/core` contracts where dependency direction
  stays acyclic;
- test helpers only when they are explicitly contract-level and do not pull in
  runtime providers.

Not allowed:

- raw HTTP framework objects such as Fastify, Express, Hono, request, reply, or
  server instances as the app integration surface;
- cloud SDK clients, database clients, queue provider clients, ORM models, or
  deployment topology;
- product app services, repositories, feature modules, route handlers, job
  handlers, business rules, or app-internal folder assumptions;
- environment loading, secret resolution, process signal handling, server
  startup, worker loops, or long-lived resource lifecycle.

### `platform/testing/**`

Purpose: provide deterministic fakes and assertions that prove app/platform
contract compatibility without real infrastructure.

Typical files:

- fake route, job, permission, health, config, lifecycle, and app registries;
- fake request and job contexts;
- fake logger, metrics, clock, feature flag reader, config reader, and abort
  signal helpers;
- mount-test harnesses that mount an app and inspect registered
  contributions;
- assertion helpers for duplicate registrations, reserved paths, unknown
  permissions, invalid config, unsafe health output, and shutdown ordering.

Allowed:

- in-memory fakes that preserve the same public contract shape apps will use in
  real runtime code;
- test-only builders and assertions for platform, app, and contract tests;
- fixtures that intentionally exercise invalid mounts and failure modes.

Not allowed:

- production runtime dependencies;
- real network, database, queue, cloud, or secret-manager calls by default;
- fakes that expose capabilities not present in the real contract;
- app-specific business test helpers that belong under the owning app or
  product package.

### `platform/runtime/**`

Purpose: implement provider-neutral runtime mechanics shared by server and
worker processes.

Typical files:

- `registry.ts` or registry modules for route, job, health, permission, config,
  and lifecycle registrations;
- `context-factory.ts` for request and job context construction;
- `lifecycle.ts`, `resources.ts`, `readiness.ts`, and `shutdown.ts` for startup,
  readiness, draining, resource cleanup, app hooks, telemetry flush, and exit
  sequencing;
- `errors.ts` for safe runtime error mapping;
- `cancellation.ts`, `clock.ts`, or `flags.ts` for runtime helpers that remain
  provider-neutral.

Allowed:

- provider-neutral orchestration, validation, lifecycle, registry, retry,
  readiness, and shutdown behavior;
- stable runtime helpers used by both HTTP and worker entrypoints;
- coordination with platform adapters through explicit provider-neutral
  contracts.

Not allowed:

- HTTP framework startup, concrete middleware registration, or route adapter
  details that belong in `platform/server/**`;
- queue polling clients, AWS SDK clients, database clients, or other provider
  SDK lifecycle unless they sit behind an approved adapter boundary;
- Terraform, CDK, Pulumi, IAM, networking, load balancer, DNS, or deployment
  topology;
- product workflow decisions, resource-specific authorization, app services,
  app repositories, or business handlers.

### `platform/server/**`

Purpose: run the HTTP/API process and translate registered app routes into real
HTTP routes.

Typical files:

- `main.ts` for the server process entrypoint;
- `mount.ts` for the server-side composition root that imports public app mount
  modules;
- `create-server.ts` for constructing the chosen HTTP framework instance;
- `middleware.ts` for middleware ordering;
- `register-routes.ts` for adapting route registrations to the framework;
- `health-routes.ts` for `/livez`, `/readyz`, and safe status endpoints;
- `errors.ts` or `responses.ts` for HTTP error and response mapping.

Allowed:

- concrete HTTP framework code;
- API versioning, route prefixing, request parsing, CORS, security headers,
  request logging, authentication hooks, context creation, authorization,
  validation, response shaping, error mapping, and server shutdown;
- app mount imports only in approved composition roots such as
  `platform/server/mount.ts`.

Not allowed:

- importing app services, repositories, feature modules, domain models, route
  handlers, or business rules from ordinary server internals;
- letting apps call `listen`, install global middleware, parse credentials,
  own CORS, own rate limits, install process signal handlers, or receive raw
  server instances;
- worker polling loops, retry/dead-letter mechanics, or queue provider
  semantics that belong in `platform/workers/**` or provider adapters;
- product-specific route meaning or resource authorization decisions.

### `platform/security/**`

Purpose: own provider-neutral security mechanics for the platform runtime while
keeping app code free of identity-provider and deployment-target details.

Typical files:

- `index.ts` or security modules for authentication result types, JWT/session
  validators, token parsing, authz mapping validation, CORS policy helpers,
  rate-limit key derivation, and standard security errors;
- provider-shaped helpers such as Cognito issuer/JWKS URI builders when they
  remain hidden behind provider-neutral interfaces;
- tests that prove missing credentials, invalid tokens, valid tokens,
  permission mapping, CORS allowlists, rate-limit keying, and unknown
  target-granted permissions.

Allowed:

- validating JWT signatures against JWKS, issuer, token use, expiry, and app
  client claims;
- mapping provider groups, scopes, claims, roles, or entitlements into
  app-declared `Permission` values;
- validating target authz maps against permissions declared by mounted apps;
- deriving non-secret rate-limit keys from principal identity, token/session
  hash, trusted forwarded IP, or an approved local fallback;
- deciding CORS allowlist behavior from target profile or equivalent
  environment config.

Not allowed:

- making provider groups, scopes, or claims the source of truth for what app
  permissions exist;
- exposing raw Cognito, Auth0, Clerk, OIDC, cloud SDK, or provider clients as
  ordinary app-facing APIs;
- committing token values, client secrets, private keys, refresh tokens,
  credentials, or connection strings in source, docs, tests, logs, fixtures, or
  generated packets;
- placing product-specific business authorization, resource ownership,
  approval workflow, quota, or feature-access decisions in platform security;
- letting apps parse JWTs, own global CORS policy, or choose platform-wide
  rate-limit behavior.

### `platform/workers/**`

Purpose: run background job processes and translate registered app jobs into
worker behavior.

Typical files:

- `main.ts` for the worker process entrypoint;
- `mount.ts` for the worker-side composition root that imports public app mount
  modules;
- `register-jobs.ts` for validating and adapting job registrations;
- `worker-loop.ts` for provider-neutral polling or receive loop mechanics;
- `retry-policy.ts`, `dead-letter.ts`, and `idempotency.ts` for runtime job
  policies;
- `job-context.ts` for job context creation where it is worker-specific;
- `health.ts` and `shutdown.ts` for worker readiness and draining.

Allowed:

- job registration validation, payload validation, retry/backoff decisions,
  dead-letter behavior, idempotency hooks, job logs, metrics, health, and
  graceful shutdown;
- fake or in-memory queue behavior for deterministic local tests;
- provider adapter integration through explicit queue contracts.

Not allowed:

- importing app job-handler internals outside approved app mount modules;
- product decisions about what work means or when work should be enqueued;
- concrete AWS SQS, EventBridge, Kafka, RabbitMQ, Redis, or cloud SDK semantics
  in provider-neutral worker runtime modules;
- infrastructure resources, queue provisioning, alarms, IAM permissions, or
  worker deployment topology.

### `platform/adapters/**`

Purpose: translate provider-neutral runtime contracts into specific providers
or libraries when the shell needs real external services.

Path convention:

- organize adapters by provider, adapter type, and service name:
  `platform/adapters/<provider>/<adapter-type>/<service-name>/`;
- examples include `platform/adapters/aws/runtime/ecs-fargate/`,
  `platform/adapters/aws/runtime/lambda/`,
  `platform/adapters/aws/queue/sqs/`,
  `platform/adapters/aws/storage/s3/`,
  `platform/adapters/aws/secrets/secrets-manager/`, and
  `platform/adapters/aws/observability/cloudwatch/`;
- the provider segment names the cloud, local, or vendor boundary; the adapter
  type names the platform concern; the service name names the concrete
  provider service being translated.

Typical files:

- adapter factories for queues, storage, databases, feature flags,
  observability, auth, or secrets;
- provider error mappers;
- provider config schemas;
- adapter lifecycle wrappers.

Allowed:

- provider SDK/client integration behind explicit platform contracts;
- provider error normalization into stable platform vocabulary;
- connection creation and closing when lifecycle is owned by platform runtime;
- adapter contract tests with fakes or provider-local test doubles.

Not allowed:

- exposing raw provider clients as the primary app-facing API;
- letting ordinary app feature code pick or import provider adapters directly;
- app business logic or product workflow decisions;
- infrastructure provisioning, IAM, networking, or cloud resource topology;
- secret values in source, tests, docs, fixtures, logs, or generated packets.

### `apps/platform-smoke/**`

Purpose: provide a deliberately boring app that proves the platform shell can
mount an app before real product application work begins.

Typical files:

- `app.mount.ts` to register one route, one job, one health check, one app
  config schema, one permission, and one lifecycle hook;
- `app.permissions.ts` or equivalent app-owned module for app-specific
  permission declarations used by routes and jobs;
- `app.manifest.ts` to publish deployment-facing metadata without importing
  app internals;
- tiny internal route, job, health, and config files if needed to prove the
  mount path.

Allowed:

- minimal smoke behavior that exercises request context, job context,
  permission metadata, health aggregation, config validation, logging, metrics,
  and lifecycle hooks;
- app-owned permission vocabulary that is registered through the public mount
  module and then validated by platform;
- intentionally simple app-owned internals used only by the public mount
  module;
- local and deployment smoke tests that prove the platform shell, not product
  behavior.

Not allowed:

- real CRM, billing, onboarding, customer, entity-builder, or other product
  behavior;
- becoming the required internal app structure for future apps;
- importing platform server or worker internals directly;
- secrets, real tenant/customer data, or production provider assumptions.

### `products/<product>/**`

Purpose: compose app modules into a named product without mixing in deployment
target values.

Typical files:

- `product.manifest.ts` for product identity, app list, app enablement, and
  product-level composition metadata;
- generated product metadata when deploy or smoke tooling needs a
  machine-readable projection;
- optional product role grouping that references permissions declared by apps
  included in the product target.

Allowed:

- product identity and display metadata;
- references to app public manifests, app mount modules, or generated app
  metadata;
- lists of apps included in the product, starting with `apps/platform-smoke`
  for the Kanbien Platform proof;
- product-level role groupings that reference app-declared permissions.

Not allowed:

- treating an environment such as `kanbien/staging` as the product;
- AWS account, region, runtime family, DNS, CORS origins, auth provider
  configuration, image digests, or readiness blockers;
- secret values, provider client secrets, tokens, private keys, or connection
  strings;
- imports from app services, repositories, route handlers, job handlers,
  business rules, or feature internals;
- defining permission vocabulary that belongs to apps.

### Deployment-Facing Manifests And Config

Purpose: give infra and deployment tooling stable facts without requiring them
to inspect app internals.

Typical files:

- `apps/*/app.manifest.ts` for app-owned deployment facts;
- `products/*/product.manifest.ts` for product-owned app composition facts;
- target-specific authz maps such as
  `infra/**/targets/<client>/<environment>/authz-map.yml` when a target needs
  to map provider groups, roles, scopes, claims, or machine identities to
  app-declared permissions;
- generated deployment metadata when the manifest needs a machine-readable
  projection;
- `infra/environments/**` for target-specific values;
- `infra/**/deploy-manifest.*` or equivalent deployment metadata once the
  infra layout is approved.

Allowed:

- app identity, route base path, health endpoint names, worker process names,
  required config keys, secret reference names, queue requirements, container
  ports, smoke-test targets, and deployment ownership metadata;
- non-secret authz mappings that grant only permissions declared by apps in the
  product target;
- non-secret references to secret stores or parameter names;
- declarative values that are stable enough for infra checks, image builds,
  smoke tests, and deployment readiness reports.

Not allowed:

- secret values, tokens, credentials, private keys, or connection strings with
  embedded credentials;
- imports from app services, repositories, route handlers, job handlers,
  business rules, or feature internals;
- hidden business logic that makes the manifest a second app implementation;
- target authz mappings that invent permissions not declared by app mounts;
- provider-specific group, role, scope, or claim names leaking into ordinary
  app route handlers;
- cloud resource creation, IAM, networking, DNS, load balancer, or deployment
  topology outside infra-owned files.

## App-Facing Contracts and Composed Context Placement

Before implementing concrete server or worker runtime modules, platform should
define the stable app-facing contract surface that apps will mount against.
That contract surface starts in `platform/contracts` unless another public
platform contract entry point is explicitly approved.

`platform/contracts` should define provider-neutral app registration and
mounting contracts for routes, jobs, health checks, config schemas, lifecycle
hooks, mount dependencies, feature-flag access, request context, and job
context. Apps should register intent and handlers through those contracts;
platform/server and platform/workers should translate the registrations into
HTTP routes, middleware, queue consumers, health aggregation, and process
lifecycle behavior.

Composed request and job contexts belong in the platform contract layer first.
They may combine core primitives such as correlation id, causation id,
timestamp, tenant context, principal, locale, config source, logger, metrics,
clock, queue message, delivery metadata, feature flags, and cancellation
signals. They must not be added to `packages/core/shared` while they depend on
authn, tenancy, i18n/localization, logging, monitoring, config, queues, or
runtime cancellation concepts. A composed context should move into
`packages/core` only after at least two independent consumers need the same
provider-neutral shape and the dependency direction can remain acyclic.

Feature flag access should start as a provider-neutral reader contract.
Platform adapters may bind that reader to environment, config, database, or
third-party flag providers later, but apps should not receive concrete flag
clients or provider SDKs through their mount dependencies.

## Logging Normalization

Platform observability code should normalize rich runtime values before they
reach a log sink. Core may define log record and redaction contracts, but
platform owns the runtime conversion from framework/provider objects into safe
plain fields.

Platform logging adapters should:

- convert `Error` values into bounded plain fields such as name, message, code,
  stack policy, and safe cause summary;
- convert dates and timestamps into ISO date-time strings;
- summarize request, response, header, cookie, and body objects without logging
  raw secrets, credentials, session tokens, or unnecessary personal data;
- normalize provider errors such as AWS SDK errors into safe fields such as
  provider, operation, status code, request id, retryable flag, and error code;
- reject, redact, or summarize non-plain values such as streams, buffers,
  sockets, class instances, maps, sets, promises, circular objects, and
  framework request objects;
- apply redaction before log export;
- enforce maximum field size, object depth, array length, and total record
  size;
- emit enough correlation, tenant, route, job, and runtime context for support
  without turning logs into audit storage.

Infra should provision log groups, log sinks, retention days, encryption,
access controls, metrics filters, alarms, and export destinations.

## Durable Outbox and Event Delivery

Platform event delivery should use an outbox-shaped path when a saved state
change must publish an event. Core may define event envelopes and publisher
ports, but platform owns concrete delivery behavior.

Platform event delivery should:

- record outbox messages in the same transaction as the business state change
  when event publication matters;
- publish outbox messages through a platform-owned worker or relay;
- mark messages published only after the broker accepts the publish;
- preserve event id, type, version, tenant id, correlation id, causation id
  where relevant, actor id where relevant, occurred timestamp, idempotency key,
  and payload schema version;
- handle retries, backoff, dead-letter queues, poison messages, replay,
  duplicate delivery, ordering expectations, and subscriber idempotency;
- translate provider-specific broker failures into stable publish or
  persistence vocabulary before app code sees them;
- emit metrics, logs, health/readiness signals, and operator diagnostics for
  backlog depth, publish latency, retry count, DLQ count, and stalled relays.

Infra should provision broker resources, topics, queues, DLQs, IAM
permissions, KMS keys, retention settings, alarms, dashboards, worker
deployments, and autoscaling rules.

## Audit Runtime, Retention, and Export

Platform audit code should make audit records durable accountability evidence.
Core may define audit event contracts, but platform owns durable recorder
implementations and export mechanics.

Platform audit runtime should:

- write audit records to durable storage with explicit actor, target, tenant,
  action, outcome, timestamp, correlation id, reason, and safe metadata;
- keep audit records separate from operational logs, analytics events, metrics,
  and event-bus messages;
- protect audit storage with access controls and record access to sensitive
  audit data where appropriate;
- define whether a failed audit write blocks the initiating action, retries
  asynchronously, or raises an operational incident;
- support retention policy, legal hold, privileged access review, export
  workflows, redaction jobs where legally required, and SIEM/security-tool
  integrations;
- avoid storing raw credentials, tokens, full request bodies, provider objects,
  large binary values, or unrelated personal data in audit metadata.

Infra should provision audit tables or stores, object storage where needed,
encryption keys, backup policy, lifecycle and retention rules, legal-hold
resources where available, SIEM export destinations, monitoring, and access
permissions.

## Payload and Metadata Size Budgets

Platform adapters should enforce explicit size budgets for cross-boundary
payloads and metadata. Core may require plain JSON-safe values, but platform
must make runtime cost and storage limits concrete.

Platform should define limits for:

- log record total size, field size, object depth, key count, and array length;
- event payload size, event metadata size, and broker-specific message limits;
- audit metadata size, key count, nesting depth, and export/storage limits;
- request body summaries and response body summaries used in diagnostics;
- retained prompt, transcript, file, or document excerpts where AI/runtime
  systems are involved.

When payloads exceed budget, platform should use a deliberate policy: reject,
truncate with an explicit marker, summarize, store a pointer to durable object
storage, or record a checksum/reference. Silent truncation is not acceptable
for audit, compliance, or event contracts.

Apps own product decisions about which facts are needed. Platform owns
consistent enforcement and diagnostics. Infra owns external quota, storage,
retention, and cost controls.

## Implementation Acceptance

A platform runtime slice should not be treated as production-ready until tests
or deployment checks prove the relevant obligations:

- logging normalization handles rich objects, circular values, secrets, and
  oversized fields safely;
- event delivery preserves transaction-to-publication consistency through an
  outbox or records the accepted consistency tradeoff;
- audit recording is durable, access-controlled, exportable where required,
  and governed by retention/legal-hold policy;
- payload and metadata limits are explicit and tested;
- infra plans name the actual log sinks, brokers, queues, DLQs, storage,
  encryption, backup, retention, alarms, dashboards, and permissions.

## RAG Implication

When agents implement platform or infra work touching logging, events, audit,
payload handling, or provider adapters, the RAG/rulebook layer should retrieve
this source material alongside the platform layer rules and the relevant
cross-cutting concern rules. If an implementation defers one of these
obligations, the deferral should be recorded as an explicit gap rather than
disappearing into chat history.
