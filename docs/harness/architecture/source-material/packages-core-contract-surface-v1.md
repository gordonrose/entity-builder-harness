<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.source-material.packages-core-contract-surface-v1
  version: 11
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  kind: source-material
  purpose: Record the approved initial packages/core contract surface for RAG/rulebook projection.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: harness.architecture.rules.layers.packages-core
    path: docs/harness/architecture/rules/layers/packages-core.yml
-->
# packages/core Contract Surface v1

## Decision

The initial `packages/core` slice may establish the package boundary and a
small set of contract-shaped capability modules before product apps and
platform adapters exist.

This is a bootstrap exception to the normal "extract after observed reuse"
rule. The exception is narrow: the slice may define stable names, types, ports,
and small pure primitives that future apps and platform packages will consume,
but it may not define provider implementations, app workflows, infrastructure,
runtime hosts, or cloud SDK integrations.

## Approved Capability Surface

The initial package surface may include these contract modules:

- `shared`: branded identifiers, result/error shapes, translation-ready message descriptors, request context, clocks.
- `config`: config source and schema contracts.
- `logging`: logger, log record, and redaction contracts.
- `monitoring`: health check, metric, signal definition, and label-safety contracts.
- `validation`: validation issue and validator contracts.
- `authn`: principal and authenticator contracts.
- `authz`: permission and authorizer contracts.
- `tenancy`: tenant identifiers and tenant-resolution contracts.
- `persistence`: repository, unit-of-work, transaction, and pagination contracts.
- `security`: defensive policy and secret/hash contracts.
- `audit`: audit event, audit event version, and recorder contracts.
- `events`: event envelope and event bus contracts.
- `queues`: queue message, queue message version, queue port, handler, delivery, retry/dead-letter metadata, and queue error contracts.

## Core Contract Evolution and Compatibility Policy

Core contracts are compatibility-sensitive even when they are not durable
payload schemas. Apps, platform runtime code, provider adapters, tests, and
future generated code may compile against exported core types, helper names,
stable error codes, message keys, metric names, config keys, permission
strings, event types, queue message types, and port interfaces.

Core contract changes should therefore be additive by default. Adding an
optional field, adding a new helper, adding a new stable error code, or adding
a new module is usually safer than renaming, removing, narrowing, or changing
the meaning of an existing export.

Non-additive changes require an explicit compatibility decision. A breaking
change must record what changed, why additive evolution was not enough, which
consumers are affected, how existing consumers migrate, and when any deprecated
surface may be removed. Renames and removals should normally keep an adapter,
alias, shim, or compatibility window before the old surface disappears.

Durable or asynchronous payloads need explicit schema/version facts because
they may outlive the deployment that created them. Events already carry event
schema versions. Queue messages, audit records, persistence snapshots, or other
serialized cross-runtime payloads should add schema/version contracts before
they become durable, replayable, retried, exported, or shared across deployed
versions.

Public TypeScript contracts need compatibility fixtures in addition to module
unit and type tests. Compatibility fixtures should model old public usages from
apps and platform code and should compile as part of the core check. Future
changes may update those fixtures only when the breaking change is intentional,
documented, and paired with migration guidance.

## Shared Primitive Boundary

The `shared` module should define the lowest-level provider-neutral primitives
that other core modules depend on. Shared branded identifiers, result/error
shapes, message descriptors, clocks, and request context values should stay
small, stable, and JSON-safe.

`ISODateTime` values should represent explicit ISO date-time strings with
timezone information. Date-only strings, localized prose dates, and implicit
local-time strings should not be accepted as core timestamp values. Locale or
region-specific display belongs in localization/presentation code, not in the
shared timestamp primitive.

Provider-neutral JSON-like contract values should stay plain and serializable.
Shared helpers should reject non-finite numeric values and non-plain runtime
objects when copying cross-boundary facts for claims, policy facts, event
payloads, or audit metadata.

## Config Contract Boundary

The `config` module should define provider-neutral contracts and pure helpers
for reading primitive runtime settings. It may define a `ConfigSource` port,
in-memory record-backed sources, required/optional lookup helpers, primitive
type readers, schemas, and config error shapes.

Record-backed config sources should snapshot their input values when created
so later mutation of the caller's object does not change the source contract.

Config errors should use validation issues and translation-ready descriptors so
apps can translate missing or invalid configuration messages at their own
presentation boundary.

The `config` module must not read directly from `process.env`, local files, AWS
SSM, Secrets Manager, databases, or deployment manifests. Those are platform,
infra, or runtime adapter concerns that should be translated into the core
`ConfigSource` contract.

## Logging Contract Boundary

The `logging` module should define provider-neutral operational log contracts:
log levels, log records, logger ports, redactors, redaction helpers, and no-op
or wrapping loggers that preserve the same public contracts.

Operational log messages may remain direct strings because they are intended
for developers and operators, not final localized user-facing copy. Sensitive
or secret fields should be redacted before records reach a concrete sink.

The `logging` module owns the common default sensitive-field vocabulary used by
provider-neutral redactors. When new common sensitive fields are discovered,
they should be maintained in this layer so apps and platform adapters inherit
the same default defensive behavior. App-specific, platform-specific, or
provider-specific sensitive fields should extend the default redaction contract
without moving concrete sink behavior into core.

The `logging` module must not write directly to console, CloudWatch,
OpenTelemetry, files, Datadog, or any other concrete runtime sink. Platform
adapters own those integrations and should consume the core logger contracts.

## Monitoring Contract Boundary

The `monitoring` module should define provider-neutral operational signal
contracts: monitored component references, health check names, health check
types, health statuses, health check results, metric names, metric kinds,
metric units, metric points, metrics ports, signal categories, signal intents,
signal ownership, low-cardinality metric labels, and small pure helpers for
tests.

Monitoring contracts should support liveness, readiness, dependency, and
capability probes. Health check results should identify the checked component,
the check type, the current status, the timestamp, optional duration, optional
translation-ready explanation, and optional plain serializable metadata.

Metrics should use stable names, explicit kinds, explicit units, finite numeric
values, timestamps, and safe labels. Metric labels should stay primitive,
bounded, and low-cardinality. They must not carry secrets, raw credentials,
tokens, emails, phone numbers, raw user ids, principal ids, request ids,
correlation ids, trace ids, session ids, IP addresses, raw URLs, raw paths,
provider objects, class instances, non-finite numeric values, or runtime-only
values.

Monitoring signal definitions should explain why a signal exists, who owns it,
which component it describes, and whether it is intended for health detection,
alerting, capacity planning, debugging, service-level-indicator use, or cost
control. Basic SLI vocabulary may live in core as signal intent and definition
metadata, but production SLO targets and alert thresholds belong outside core.

The `monitoring` module must not define CloudWatch, Datadog, Prometheus,
OpenTelemetry exporters, concrete health endpoints, dashboards, alert
thresholds, PagerDuty or incident routes, production SLO targets, runtime
wiring, cloud SDK clients, provider adapters, infrastructure alarms, or
product-specific uptime commitments. Apps own which product paths matter.
Platform owns signal emission, aggregation, runtime health wiring, and provider
adapters. Infra owns monitoring backends, alarms, dashboards, and notification
routes.

## Security Contract Boundary

The `security` module should define provider-neutral defensive contracts:
secret string markers, hash algorithm and hash value shapes, hasher ports,
data sensitivity labels, sensitive value kinds, security policy identifiers,
security policy violations, policy decisions, policy evaluators, and small
pure helpers for tests.

Security policy contracts in core name the result of a defensive policy check.
They may say that a policy allowed an operation or denied it with a stable,
translation-ready violation reason and plain serializable evidence. Core
security policy contracts should not implement a policy engine or decide
product security settings.

Security policy evidence should stay plain and serializable. It must not carry
secrets, raw credentials, tokens, provider objects, request objects, class
instances, non-finite numeric values, or runtime-only values.

The `security` module may classify sensitive values for defensive handling
across logs, audit, events, exports, provider diagnostics, and runtime
adapters. Classification labels are shared vocabulary; they are not a complete
data-governance engine.

The `security` module must not define product password rules, tenant-specific
security policies, MFA workflows, JWT or session parsing, API key checking,
rate-limit algorithms, secret storage, encryption providers, IAM policies, KMS
keys, middleware, or concrete hashing algorithms such as bcrypt or Argon2.
Apps own product-specific security policy. Platform owns runtime enforcement
and provider adapters. Infra owns cloud security resources and deployment
topology.

## Tenancy Contract Boundary

The `tenancy` module should define provider-neutral tenant identity and
isolation contracts: tenant identifiers, tenant context packets, resolver ports,
and small pure helpers for constructing those values.

Tenant context should carry enough stable information for apps, platform,
audit, authorization, logging, events, and persistence contracts to preserve
tenant isolation without depending on runtime providers.

The `tenancy` module must not decide how tenants are discovered from hostnames,
JWT claims, headers, database rows, AWS account mappings, product workflows, or
deployment topology. Apps and platform adapters own those inputs and should
translate them into the core tenant context contract.

## Authentication Contract Boundary

The `authn` module should define provider-neutral authentication contracts:
principal identifiers, principal types, principal records, authentication
results, authenticator ports, and small pure helpers for constructing those
values.

A principal represents the authenticated global actor identity. It must not be
treated as the tenant-specific user profile, tenant account, membership record,
role assignment, preference record, or onboarding state. The same human or
service may authenticate as one global principal and still have different
tenant profiles or memberships in different tenants.

Principal claims should be normalized into plain serializable values before
they enter the core principal contract. Raw provider objects, dates, sessions,
credentials, access tokens, refresh tokens, or other rich runtime values should
not be carried as principal claims.

When a principal carries a tenant id, that tenant id represents the current
tenant context for the request or job, not the actor's exhaustive tenant
membership list.

The `authn` module must not parse JWTs, verify sessions, check API keys, call
identity providers, make authorization decisions, or model tenant-specific
account workflows. Apps and platform adapters own those concerns and should
translate verified credentials into the core principal contract.

## Authorization Contract Boundary

The `authz` module should define provider-neutral authorization contracts:
permissions, resource references, lightweight relationship facts,
attribute/fact bags, authorization requests, authorization decisions,
authorizer ports, and small pure helpers for constructing those values.

Permission helpers should create non-empty `resource:action` strings without
whitespace or nested colon separators, so malformed permission vocabulary is
caught at the boundary.

Authorization requests should be able to ask role/permission, relationship to
resource, and attribute-based questions. They may include principal identity,
current tenant context, action/permission, resource reference, parent resource,
relationship facts, principal attributes, tenant attributes, resource
attributes, environment attributes, and additional plain facts.

Authorization decisions should be explicit allow/deny answers. Denials must
carry translation-ready reasons, and decisions may carry plain serializable
evidence for audit, debugging, and policy traceability.

The `authz` module must not authenticate credentials, define product-specific
roles, own relationship inheritance rules, implement ABAC policy language, read
team membership storage, or hardcode tenant-specific permission meanings. Apps
and product modules own those policies; platform adapters may bind the core
authorizer port to a policy engine or provider.

## Persistence Contract Boundary

The `persistence` module should define provider-neutral contracts for loading
and saving state: page requests, pages, optimistic concurrency tokens,
optional page total metadata, repository ports, save options, persistence error
meanings, unit-of-work boundaries, transaction hooks, and small in-memory
helpers for tests.

Total counts should be optional, because they can be expensive, approximate, or
unavailable in some storage backends. When a product use case includes total
records or total matching records, those counts should use the shared
non-negative integer page-total contract rather than ad hoc numeric fields.

Persistence contracts should use stable error vocabulary for common storage
failure categories such as conflict, duplicate, timeout, unavailable storage,
invalid page request, not found, and transaction failure. Platform adapters
should translate provider-specific database errors, lock failures, deadlocks,
timeouts, conditional-write failures, and network failures into those stable
core meanings.

Repository save contracts may support optimistic concurrency through an
expected concurrency token. This lets app code prevent stale writes from
overwriting newer state without requiring core to choose a locking strategy or
database implementation.

Unit-of-work and transaction contracts should define the boundary for grouped
storage work. After-commit hooks should be reserved for side effects that must
only run after a successful commit, such as publishing events or scheduling
post-commit work.

Transaction failures should surface through stable persistence vocabulary
rather than leaking raw database, runtime, or test-helper error shapes.

The `persistence` module must not define SQL, ORM models, database clients,
tables, indexes, shards, backups, object-storage clients, product-specific
repositories, or product workflow decisions. Platform owns concrete storage
adapters. Infra owns storage topology, backup resources, indexes, and scaling.
Apps and product modules own product-specific queries and workflow behavior.

## Events Contract Boundary

The `events` module should define provider-neutral contracts for facts that
happened and may be published across app, platform, worker, and broker
boundaries: event identifiers, event type names, event schema versions,
JSON-safe payload values, event envelopes, publish error meanings, publisher
or bus ports, handler ports, and small in-memory or no-op helpers for tests.

Event envelopes should carry stable metadata such as id, type, version,
occurred-at timestamp, optional tenant id, optional correlation id, and payload.
Payloads should stay plain and serializable so platform adapters can move them
through brokers, outboxes, logs, tests, and workers without provider-specific
objects.
Event payloads should reject non-finite numeric values and non-plain runtime
objects before they cross app/platform boundaries.

Event type names are portable domain facts. They should not be treated as
concrete broker topics, queue names, stream names, or subscription resources.
Platform adapters may translate event types into provider-specific routing
later.

Publishing failures should use stable error vocabulary rather than exposing
provider-specific broker errors directly to app code.

Events that depend on successful state changes should be published through a
post-commit path, such as a persistence `afterCommit` hook or an outbox relay,
so subscribers do not react to facts from rolled-back transactions.
In-memory event helpers should define whether recorded events mean attempted,
accepted, or successfully handled publish operations, and tests should preserve
that meaning.

The `events` module must not define product event catalogs, broker topics,
queue names, subscriber deployment, retries, dead-letter queues, ordering
guarantees, schema registries, cloud SDK clients, worker runtimes, or product
workflow decisions. Apps own product event meanings and emission decisions.
Platform owns concrete delivery adapters. Infra owns broker resources and
deployment topology.

## Queues Contract Boundary

The `queues` module should define provider-neutral contracts for retryable
background work that crosses app, platform, worker, and broker boundaries:
queue message identifiers, message type names, JSON-safe payload values,
message envelopes, send options, delivery metadata, retry and dead-letter
metadata shapes, queue error meanings, queue ports, handler ports, and small
in-memory or no-op helpers for tests.

Queue messages should carry stable metadata such as id, type, schema version,
payload, enqueued-at timestamp, optional tenant id, optional correlation id,
optional idempotency key, optional delay, and optional message group key where
a product or runtime needs ordered work. Payloads should stay plain and
serializable so platform adapters can move them through queues, retries, logs,
tests, workers, and dead-letter paths without provider-specific objects.
Queue payloads should reject non-finite numeric values and non-plain runtime
objects before they cross app/platform boundaries.

Queue message versions should be explicit positive integers. Core helpers may
default new queue messages to the current version to preserve additive
compatibility, but durable platform adapters must preserve the version when a
message is serialized, retried, replayed, or moved to a dead-letter path.

Queue message type names are portable work-kind facts. They should not be
treated as concrete broker queue names, SQS queue URLs, Kafka topics, routing
keys, or worker deployment names. Platform adapters may translate message
types into provider-specific routing later.

Sending failures and handling failures should use stable queue error
vocabulary rather than exposing provider-specific broker errors directly to app
code.

Queue contracts may name retry and dead-letter metadata so apps and platform
can reason about attempts, max attempts, next retry time, dead-letter reason,
and idempotency without forcing core to implement worker loops, provider
receive/delete semantics, or broker-specific retry policies.

The `queues` module must not define product job catalogs, product handlers,
worker runtimes, broker queue resources, queue URLs, receipt handles,
visibility timeouts, concrete retry algorithms, scheduler loops,
dead-letter queue resources, ordering guarantees, cloud SDK clients, or
deployment topology. Apps own product work meaning and handlers. Platform owns
worker runtime mechanics and concrete delivery adapters. Infra owns broker
resources, dead-letter resources, alarms, permissions, and deployment topology.

## Audit Contract Boundary

The `audit` module should define provider-neutral contracts for accountability
records: audit event identifiers, audit event type names, actor references,
audit event schema versions, target references, outcomes, timestamps, tenant
context, correlation ids, translation-ready reasons, JSON-safe metadata,
recorder error meanings, recorder ports, and small in-memory or no-op helpers
for tests.

Audit records should answer who did what, to which target, in which tenant or
context, when, from which correlated request or job, and with which outcome.
Outcomes should distinguish successful, denied, and failed actions so security
review and product history do not depend on parsing operational logs.
Audit events should carry an explicit actor and target. Anonymous and system
actors should be represented explicitly instead of omitting actor data; global
or system-scoped actions should use a deliberate target instead of omitting the
target.

Audit event versions should be explicit positive integers. Core helpers may
default new audit events to the current version to preserve additive
compatibility, but durable audit recorders, exporters, retention workflows, and
SIEM adapters must preserve the version when an audit event crosses storage,
export, or compliance boundaries.

Audit metadata should stay plain and serializable. It may include evidence
needed for review, compliance, debugging, or product history, but it must not
carry secrets, tokens, raw credentials, rich provider objects, raw request
bodies by default, or runtime-only values.
Audit metadata should reject non-finite numeric values and non-plain runtime
objects before it crosses storage, export, or compliance boundaries.

Audit records are not operational logs, analytics events, monitoring metrics,
or event-bus messages. Logging explains what the system is doing. Events let
other runtime components react. Audit records preserve accountability facts.

The `audit` module must not define product-specific audit catalogs, audit
storage tables, object-storage buckets, retention policy, legal hold,
redaction jobs, export workflows, SIEM integrations, CloudWatch sinks, cloud
SDK clients, or product workflow decisions. Apps own which product actions
must be audited. Platform owns durable audit recorder implementations. Infra
owns storage resources, retention topology, and deployment resources.

## Message, i18n, and Localization Boundary

Core, platform, and app-facing contracts should pass stable meaning rather than
final localized prose. User-facing or consumer-facing explanations should carry
machine-stable codes, optional translation keys, fallback/default messages, and
primitive interpolation params.

Validation issues, core errors, policy denials, notification descriptions,
report labels, and API/display responses should use translation-ready
descriptors when they may be shown to people. The fallback/default message is
for debugging, logs, tests, and untranslated contexts; it is not the canonical
localized copy.

The `i18n` contract layer owns translation keys, message catalogs, translators,
fallback behavior, and translation params. The `localization` contract layer
owns locale-sensitive formatting for dates, times, numbers, currency, and
regional display conventions. Validation and other core capability modules
should emit facts that those layers can translate or format later.

Operational logs may keep direct operational messages when they are not
user-facing display contracts.

## Placement Rules

Core owns the shape of stable cross-cutting contracts. Platform owns concrete
runtime adapters. Apps own product-specific workflows. Infra owns deployment
resources and cloud topology.

Provider adapters for AWS, databases, queues, object storage, observability,
or authentication systems must not live in `packages/core`. They belong under
platform or infra depending on whether they are runtime code or deployment
resources.

## RAG Implication

When agents add or change `packages/core` contracts, the RAG/rulebook layer must
be able to answer how the contracts should be used and where implementation
code belongs. Code changes to `packages/core` therefore require a RAG knowledge
disposition at commit time: covered by source/rules/selector proof, no-impact
with a reason, or deferred with an explicit corpus gap.
