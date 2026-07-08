<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.source-material.platform-runtime-enterprise-obligations-v1
  version: 2
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  - sre
  - security
  kind: source-material
  purpose: Record deferred platform and infra runtime obligations for enterprise-grade logging, event delivery, audit, and payload handling.
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
