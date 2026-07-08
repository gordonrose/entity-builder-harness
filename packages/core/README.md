# @kanbien/core

`packages/core` is the shared contract layer for stable Kanbien concepts.

It should contain product-neutral types, ports, error shapes, policy facts, and
small pure helpers that apps and platform implementations can depend on without
pulling in runtime providers.

## Boundary

- Core may define contracts for apps and platform to consume.
- Core may define no-op or in-memory test helpers when they preserve the same
  public contracts.
- Core must not import apps, platform, infra, cloud SDKs, ORMs, web servers, or
  vendor clients.
- Concrete provider adapters belong in `platform`.
- Product workflows belong in `apps`.

This initial slice establishes the package surface and core capability modules.
Provider implementations and app runtimes are intentionally out of scope.

## Changing Core Contracts Safely

Core is a shared contract layer, so exported names and meanings should be
treated as compatibility-sensitive. Prefer additive changes: new optional
fields, new helpers, new stable error codes, or new modules are usually safer
than changing an existing contract.

Before renaming, removing, narrowing, or changing the meaning of an exported
type, helper, error code, message key, metric name, config key, event type,
queue message type, or port interface, record the compatibility decision in
the architecture source material and rule projection. Include what changed,
why an additive path was not enough, which consumers are affected, and how
existing consumers should migrate.

Durable or asynchronous payloads need explicit schema/version facts before
they become persisted, replayed, retried, exported, or shared across deployed
versions. Events already carry `EventVersion`. Queues, audit records,
persistence snapshots, and similar cross-runtime payloads should add versioned
contracts before platform/runtime adapters make them durable.

`tests/compatibility` contains compile-only canary usages for older public
contracts. Keep those fixtures passing unless a breaking change is deliberate,
documented, and paired with migration guidance.

## Shared Primitives

`shared` contains the lowest-level vocabulary used by the rest of core:

- `Brand` and `EntityId` distinguish important string identifiers at type level.
- `CorrelationId` connects logs, audit records, events, and errors from one request.
- `ISODateTime` stores strict ISO date-time values with explicit timezone
  information in a JSON-safe text form.
- `MessageDescriptor` carries stable meaning plus optional translation hooks.
- `Result`, `ok`, `err`, `isOk`, and `isErr` make expected success/failure explicit.
- `JsonValue` and `copyJsonValue` keep cross-boundary facts plain,
  serializable, and finite-number safe.
- `CoreError` gives failures a stable `code`, `defaultMessage`, optional translation metadata, optional diagnostic metadata, and optional debugging metadata.
- `Clock`, `systemClock`, and `fixedClock` keep time-dependent code testable.
- `RequestContext` carries only the minimum shared request metadata.

Keep this module small. Tenant, principal, permission, persistence, audit, and
event-specific concepts should live in their own modules and import shared
primitives when needed.

## Diagnostics Contracts

`diagnostics` defines the small shared vocabulary for classifying failures so
logs, monitoring, queues, events, audit, and platform workflows can agree on
what happened:

- `FailureKind` names the broad kind of failure, such as user input,
  validation, dependency outage, timeout, conflict, data integrity, bug, or
  unknown.
- `FailureSource` names where the failure appears to come from: user, app,
  platform, provider, infra, external system, or unknown.
- `FailureSeverity`, `RecoveryDisposition`, and `RecoveryAction` describe how
  serious the failure is and what kind of follow-up is safe.
- `DiagnosticFacts` keeps extra correlation and classification facts primitive
  and finite-number safe.
- `DiagnosticDescriptor`, `diagnosticDescriptor`,
  `isRetryableDiagnostic`, and `isUserCorrectableDiagnostic` give apps and
  platform code a common way to attach recovery meaning to failures.

Diagnostics is the vocabulary for self-healing, not the self-healing engine.
The intended loop is: detect, classify, correlate, decide, act, verify, then
escalate if automation is unsafe or exhausted. Core names those facts;
platform/runtime workflows perform retries, repairs, log lookups, runbook
actions, and escalation when a product has allowed that behavior.

Do not put secrets, tokens, raw request bodies, provider objects, class
instances, or rich runtime values into diagnostic facts.

## Translation-Ready Meaning

Core, platform, and app-facing contracts should pass meaning rather than final
localized prose. Use stable codes, optional translation keys, fallback/default
messages, and primitive params:

```ts
{
  code: "VALIDATION_REQUIRED",
  messageKey: "validation.required",
  defaultMessage: "Field is required.",
  params: { field: "email" }
}
```

The `defaultMessage` is fallback/debug text. It is not the final user-facing
copy for every locale. The `i18n` layer translates `messageKey` and `params`;
the `localization` layer formats locale-sensitive dates, numbers, currencies,
and regions.

Operational logs may still use direct log messages. User-facing errors,
validation issues, policy denials, notifications, reports, and API/display
responses should use translation-ready descriptors.

## i18n Contracts

`i18n` defines translation contracts without choosing a translation library,
catalog file format, locale negotiation strategy, or copywriting workflow:

- `LocaleTag` stores normalized language tags such as `en-GB`.
- `MessageTemplate` names simple message templates for catalog/test use.
- `TranslationCatalog` maps message keys to templates for one locale.
- `TranslationRequest` carries the requested locale and optional fallback
  locales.
- `TranslatedMessage` records the locale, rendered text, source, optional
  message key, and params used for a translation.
- `MessageTranslator` is the small port that apps and platform runtime code can
  depend on.
- `catalogMessageTranslator` and `defaultMessageTranslator` are pure helpers
  for tests, local flows, and composed contract examples.
- `I18nError` provides stable translation error vocabulary.

Core i18n may describe translation keys, catalogs, translator ports, fallback
behavior, and primitive interpolation params. It does not own final product
copy, load message files, negotiate browser/user locale, choose ICU, i18next,
FormatJS, or any other library, or format dates, numbers, money, or regions.

## Localization Contracts

`localization` defines locale-sensitive formatting contracts without choosing a
formatter implementation:

- `CurrencyCode`, `RegionCode`, and `TimeZoneId` brand common regional facts.
- `LocalizableDateTime`, `LocalizableNumber`, `LocalizableCurrency`, and
  `LocalizableRegion` describe values that need locale-sensitive formatting.
- `LocalizationRequest` combines a locale and localizable value.
- `LocalizedFormat` records formatted text plus the locale and value kind.
- `Localizer` is the formatting port consumed by apps and platform runtime.
- `fixedLocalizer` and `unsupportedLocalizer` are pure test/local helpers.
- `LocalizationError` provides stable formatting error vocabulary.

Core localization names the formatting intent and keeps values finite,
branded, and provider-neutral. It does not call `Intl`, format display copy,
infer user locale, choose time-zone policy, perform currency conversion,
choose exchange rates, load CLDR data, or decide product presentation rules.

## Config Contracts

`config` defines how apps and platform code can read product-neutral runtime
settings without binding core to a provider:

- `ConfigSource` is the small port for looking up a value by key.
- `recordConfigSource` is a pure snapshot source for tests and simple composed
  configs.
- `requiredConfigValue` distinguishes missing values from present `null` values.
- `stringConfigValue`, `numberConfigValue`, and `booleanConfigValue` add typed
  reads for common primitive settings.
- `ConfigError` reports missing or invalid config through validation issues, so
  config failures stay translation-ready.

Core does not read `process.env`, AWS SSM, Secrets Manager, files, or databases.
Platform adapters can translate those provider-specific sources into
`ConfigSource`.

## Logging Contracts

`logging` defines operational log contracts without choosing a log sink:

- `LogRecord` captures level, message, correlation id, and diagnostic fields.
- `logRecord` creates a shallow-copied record so callers can pass fields safely.
- `defaultSensitiveLogFieldNames`, `defaultLogRedactor`,
  `createLogRedactor`, `redactLogFields`, and `keyRedactor` define
  provider-neutral redaction behavior.
- `redactingLogger` wraps another logger and redacts fields before they reach
  the sink.
- `noopLogger` is a safe logger for tests and disabled logging paths.

Common sensitive field names discovered later should be maintained in this
module so apps and platform adapters inherit the same default defensive
behavior. App-specific, platform-specific, or provider-specific sensitive
fields can extend the default redactor through `createLogRedactor`.

Log messages are operational text for developers and operators. They are not
the user-facing translation boundary. Core does not write to console,
CloudWatch, OpenTelemetry, files, or vendor SDKs; platform adapters own those
sinks.

## Monitoring Contracts

`monitoring` defines operational signal contracts without choosing a metrics or
health backend:

- `MonitoringComponentRef` names the component being observed, such as an API,
  worker, queue, database, cache, event bus, runtime, or platform adapter.
- `HealthCheckType`, `HealthStatus`, `HealthCheckResult`, and `HealthCheck`
  define liveness, readiness, dependency, and capability probe results.
- `MetricName`, `MetricKind`, `MetricUnit`, `MetricPoint`, and `Metrics`
  define provider-neutral metric emission.
- `MetricLabels`, `metricLabels`, `defaultUnsafeMetricLabelNames`, and
  `defaultMetricLabelStringLengthLimit` keep metric dimensions primitive,
  bounded, and protected from common secret or high-cardinality labels.
- `MonitoringSignalDefinition` records why a signal exists, who owns it, what
  component it describes, and whether it is intended for alerting, capacity
  planning, health detection, cost control, debugging, or SLI use.
- `fixedHealthCheck` and `noopMetrics` are pure helpers for tests and composed
  local flows.

Core monitoring names the shared operational signal language. It does not
define CloudWatch, Datadog, Prometheus, OpenTelemetry exporters, health HTTP
endpoints, dashboards, alert thresholds, PagerDuty routes, production SLO
targets, or runtime wiring. Apps decide which product paths matter, platform
adapters emit and aggregate signals, and infra provisions monitoring backends,
alarms, dashboards, and notification routes.

Metric labels should be low-cardinality dimensions such as service, route,
method, status class, dependency, queue, or job type. Do not use raw user ids,
principal ids, request ids, correlation ids, session ids, URLs, paths, tokens,
emails, IP addresses, or secrets as metric labels.

## Security Contracts

`security` defines shared security vocabulary without choosing a runtime
security provider:

- `SecretString` and `secretString` mark sensitive string values that should
  not be treated as ordinary display/logging data.
- `HashAlgorithm`, `HashValue`, `Hash`, and `hash` describe stored hash values
  without choosing bcrypt, Argon2, KMS, or another implementation.
- `Hasher` is the small async port for hashing and verifying secrets.
- `DataSensitivity`, `SensitiveValueKind`, `DataClassification`, and
  `dataClassification` classify data that needs defensive handling across
  logs, audit, export, events, or provider adapters.
- `SecurityPolicyViolationCode`, `SecurityPolicyViolation`, and
  `securityPolicyViolation` give defensive policy failures stable,
  translation-ready meanings.
- `SecurityPolicyDecision`, `securityPolicyAllowed`,
  `securityPolicyDenied`, `SecurityPolicyEvaluator`, and
  `fixedSecurityPolicyEvaluator` define provider-neutral policy-result
  contracts and test helpers.

Core security names the shared contract for sensitive values, hashes,
classification, and policy outcomes. It does not define product password
rules, tenant-specific security policy, JWT/session parsing, MFA behavior,
secret storage, encryption providers, IAM, KMS keys, rate limits, middleware,
or concrete hashing algorithms. Apps decide product policy, platform enforces
runtime policy, and infra provisions cloud security resources.

## Tenancy Contracts

`tenancy` defines the shared way core consumers name tenant ownership and
isolation:

- `TenantId` is a branded entity id so tenant ids do not get confused with
  principal ids or other strings.
- `TenantContext` carries the tenant id plus an isolation key for data,
  authorization, audit, logs, and events that must stay tenant-scoped.
- `tenantId` and `tenantContext` create those values consistently.
- `TenantResolver` is the small async port for resolving tenant context from
  provider-specific input.
- `fixedTenantResolver` is a pure helper for tests and composed local flows.

Core does not decide whether tenants come from hostnames, JWT claims, headers,
database rows, AWS account mappings, or product workflows. Platform and app
code can translate those inputs into `TenantContext`.

## Authentication Contracts

`authn` defines the shared identity shape after credentials have been checked:

- `PrincipalId` is a branded id for a global actor identity.
- `PrincipalType` distinguishes user and service identities.
- `Principal` carries the actor id, type, stable subject, optional current
  tenant context, normalized provider-neutral claims, and optional scopes.
- `PrincipalClaimValue` and `PrincipalClaims` keep claims plain,
  serializable, and safe to pass across app/platform boundaries.
- `principalId` and `principal` create those values consistently.
- `AuthenticationResult` is either a `Principal` or `null`.
- `Authenticator` is the small async port for turning provider-specific
  credentials into an authentication result.
- `fixedAuthenticator` is a pure helper for tests and composed local flows.

A `Principal` is not the tenant-specific user profile or account. The same
human or service may authenticate as one global principal and still have
different tenant profiles, memberships, roles, names, preferences, or account
state in different tenants. `currentTenantId`, when present, means the current
tenant context for this request or job; it is not the full tenant membership
model.

Core does not parse JWTs, verify sessions, check API keys, call identity
providers, decide permissions, or model tenant-specific account workflows.
Platform and app code translate real credentials and account data into the
core `Principal` contract. Raw provider objects, rich runtime values, sessions,
credentials, and tokens should not be carried as principal claims.

## Authorization Contracts

`authz` defines the shared shape for asking and answering permission questions:

- `Permission` and `permission` provide a simple validated `resource:action`
  vocabulary.
- `ResourceRef` and `resourceRef` identify a target resource and optional
  parent resource for relationship-style authorization.
- `AuthorizationRelation` records lightweight relationship facts such as a
  principal belonging to a team or a team being assigned to a deal.
- `AuthorizationAttributes` carries ABAC facts about the principal, tenant,
  resource, and environment.
- `AuthorizationRequest` combines the principal, permission, optional tenant,
  resource, relations, attributes, and additional facts.
- `AuthorizationDecision`, `allow`, and `deny` return explicit allow/deny
  answers. Denied decisions require translation-ready reasons; decisions may
  carry plain serializable evidence.
- `Authorizer` and `fixedAuthorizer` define the async port and a pure test
  helper.

The contract supports role/permission, relationship/resource, and
attribute-based authorization questions. Core does not define product roles,
relationship inheritance rules, ABAC policy language, team membership storage,
or tenant-specific permission meanings. Apps and product modules own those
policies; platform can bind the port to a policy engine or provider.

## Persistence Contracts

`persistence` defines provider-neutral contracts for loading and saving state:

- `PageRequest`, `pageRequest`, `Page`, and `page` keep pagination shape
  consistent without choosing a database cursor format.
- `PageTotal`, `PageTotals`, `pageTotal`, and `pageTotals` provide optional
  total-count metadata when a product use case needs it. Totals are not
  required, but when included they must be non-negative whole numbers.
- `ConcurrencyToken` and `SaveOptions` give repositories a shared optimistic
  concurrency hook for stale-write protection.
- `PersistenceErrorCode`, `PersistenceError`, and `persistenceError` give
  storage failures stable meanings such as conflict, duplicate, timeout,
  unavailable storage, invalid page request, and transaction failure.
- `Repository` is the small async port for loading and saving one kind of
  entity by id.
- `UnitOfWork`, `Transaction`, and `afterCommit` define transaction boundaries
  and post-commit side effects without choosing a database.
- `inMemoryRepository` and `inMemoryUnitOfWork` are pure helpers for tests and
  composed local flows.

Core does not define tables, indexes, shards, backups, SQL, ORM models, cloud
clients, or product-specific repositories. Platform adapters translate real
database behavior into the core contracts. Infra owns deployment resources such
as backups, indexes, storage topology, and scaling. Apps and product modules
own product-specific query methods and workflow decisions.

Use totals only when the app use case needs them, because total counts can be
expensive or approximate in some storage backends. Use `afterCommit` for side
effects that should only happen after a transaction has successfully committed,
such as publishing events or scheduling work. Use `expectedConcurrencyToken`
when a caller needs to prevent stale updates from overwriting newer stored
state.

Unexpected in-memory transaction or after-commit failures are wrapped as
`PERSISTENCE_TRANSACTION_FAILED` so test helpers do not leak raw transaction
failure shapes. Platform adapters should translate provider-specific
transaction failures into the same stable persistence vocabulary.

## Files Contracts

`files` defines provider-neutral contracts for uploaded and stored file
metadata without choosing object storage, local disk, request parsing, virus
scanner, or signed URL machinery:

- `FileId`, `FileName`, `FileContentType`, `FileSizeBytes`,
  `FileChecksum`, and `FileStorageRef` name the core file identity and storage
  facts.
- `FileMetadata` keeps product metadata plain, JSON-safe, and finite-number
  safe.
- `FileScanStatus` and `FileScanResult` record provider-neutral scan outcomes
  such as pending, passed, failed, quarantined, or not required.
- `FileObject` and `StoredFile` describe stored file metadata, including
  tenant context where relevant, correlation id, checksum, scan result, created
  timestamp, storage reference, and retention/legal-hold facts.
- `PutFileInput` keeps the file body generic so platform/runtime adapters can
  choose streams, buffers, browser file objects, or provider-specific upload
  mechanisms outside core.
- `FilePutOptions` names duplicate handling so retries and accidental overwrites
  are not adapter-specific.
- `FileAccessIntent` names read, write, or delete access intent without
  granting public URLs or choosing a signed-access implementation.
- `FileStorage` is the async port for putting, loading metadata for, and
  deleting files. Reads and deletes use `FileAccessIntent`, not raw file ids.
- `FileError` can carry diagnostic metadata so runtime/platform code can
  classify storage, policy, scan, or metadata failures consistently.
- `inMemoryFileStorage` is a pure helper for tests and composed local flows.

Files are high-risk storage because they are large, user-controlled, and often
sensitive. Validate content type and size before accepting uploads. Keep
tenant isolation, access intent, retention/legal-hold needs, scan outcomes,
and audit/log correlation visible at the app or platform boundary.
Use duplicate conflicts by default and opt into idempotent duplicate handling
only when the attempted put still matches the stored metadata.

Core does not define object-storage buckets, public URLs, signed URL
generation, virus scanner integrations, image processing, file parser
implementations, storage SDK clients, retention resources, legal-hold jobs, or
product document workflows. Apps decide product meaning and retention needs,
platform implements storage/scanning/access adapters, and infra provisions
storage resources, permissions, encryption, retention, and alarms.

## Events Contracts

`events` defines provider-neutral contracts for facts that happened and may be
published to other parts of the system:

- `EventId`, `EventType`, and `EventVersion` provide explicit identifiers,
  type names, and schema versions.
- `EventPayloadValue` and `EventPayload` keep event payloads plain,
  JSON-safe, finite-number safe, and portable across app, platform, worker,
  and broker boundaries.
- `EventEnvelope` and `eventEnvelope` wrap an event with id, type, version,
  timestamp, optional tenant id, optional correlation id, and copied payload.
- `EventPublishErrorCode`, `EventPublishError`, and `eventPublishError` give
  publish failures stable translation-ready meanings.
- `EventPublisher`, `EventBus`, and `EventHandler` define the small async
  publishing and handling contracts.
- `inMemoryEventBus` and `noopEventBus` are helpers for tests and composed
  local flows.

Event type names are portable domain facts, not concrete broker topics. Apps
decide which product events to emit and when. Platform adapters decide whether
events are delivered through EventBridge, SNS/SQS, Kafka, an outbox relay, or
another runtime. Use persistence `afterCommit` hooks when an event should only
be published after storage has successfully committed.

`inMemoryEventBus.publishedEvents()` returns events accepted by the helper
after all registered handlers have succeeded. A failed handler returns
`EVENT_HANDLER_FAILED` and does not add the event to the successful published
events list.

Core does not define product event catalogs, broker topics, queue names,
subscriber deployment, retries, dead-letter queues, ordering guarantees,
schema registries, or cloud SDK clients.

## Queues Contracts

`queues` defines provider-neutral contracts for retryable background work:

- `QueueMessageId`, `QueueMessageType`, and `QueueMessageVersion` identify a
  work item, its stable work-kind name, and its payload schema version.
- `QueuePayloadValue` and `QueuePayload` keep message payloads plain,
  JSON-safe, finite-number safe, and portable across app, platform, worker,
  broker, retry, dead-letter, and test boundaries.
- `QueueMessage` and `queueMessage` wrap a message with id, type, version,
  timestamp, optional tenant id, optional correlation id, optional idempotency
  key, optional message group key, and copied payload. `queueMessage` defaults
  the version to the current v1 contract when a caller does not supply one.
- `QueueSendOptions`, `QueueDelaySeconds`, and `queueSendOptions` define
  provider-neutral send metadata without choosing a broker delay mechanism.
- `QueueDelivery`, `QueueAttempt`, `QueueRetryMetadata`, and
  `QueueDeadLetterMetadata` name delivery, retry, and dead-letter facts
  without implementing a worker loop. Retry and dead-letter states are mutually
  exclusive for a single delivery.
- `QueueErrorCode`, `QueueError`, and `queueError` give queue failures stable
  translation-ready meanings.
- `Queue`, `QueueHandler`, `inMemoryQueue`, and `noopQueue` define the async
  send/handle ports and test helpers.

Queue message type names are portable work-kind facts, not concrete broker
queue names or SQS queue URLs. Apps decide when product work should be
enqueued and which handler owns it. Platform runtime owns worker mechanics,
payload validation, idempotency, retry/backoff, dead-letter handling,
observability, and shutdown. Platform adapters translate to providers such as
AWS SQS. Infra provisions queues, DLQs, alarms, permissions, encryption,
retention, and worker deployment resources.

Queue message versions are positive integer schema facts. Durable queue
adapters, retry paths, replay tools, and dead-letter paths should preserve the
version so workers can safely handle old and new payload shapes during
deployment transitions.

`inMemoryQueue.acceptedSends()` and `acceptedMessages()` return messages
accepted by the helper. They are useful for tests, but they are not durable
queue, retry, worker, or dead-letter implementations.

Core does not define product job catalogs, product handlers, worker runtimes,
queue resources, queue URLs, receipt handles, visibility timeouts, concrete
retry algorithms, scheduler loops, DLQ resources, cloud SDK clients, or
deployment topology.

## Audit Contracts

`audit` defines provider-neutral contracts for accountability records:

- `AuditEventId`, `AuditEventType`, and `AuditEventVersion` identify durable
  audit records, stable action names, and audit payload schema versions.
- `AuditActor` captures the explicit user, service, system, or anonymous actor
  that caused the audited action.
- `AuditTarget` identifies the resource acted on, with an optional parent
  target for tenant/account/resource hierarchy.
- `AuditOutcome` distinguishes succeeded, denied, and failed actions.
- `AuditMetadataValue` and `AuditMetadata` keep audit evidence plain,
  JSON-safe, finite-number safe, and portable across storage, review, export,
  and compliance boundaries.
- `AuditEvent` and `auditEvent` combine actor, tenant, version, timestamp,
  correlation id, target, outcome, optional reason, and copied metadata.
  `auditEvent` defaults the version to the current v1 contract when a caller
  does not supply one.
- `AuditRecordErrorCode`, `AuditRecordError`, and `auditRecordError` give
  recorder failures stable translation-ready meanings.
- `AuditRecorder`, `inMemoryAuditRecorder`, and `noopAuditRecorder` define the
  async recording port and test helpers.

Audit records are accountability facts, not operational logs and not event-bus
messages. Use audit for actions that need a durable explanation of who did
what, to which target, under which tenant/context, and with which outcome.
Every audit event must carry an explicit actor and target. Use an `anonymous`
or `system` actor when no authenticated principal exists, and use a deliberate
target such as an account, session, export, or system resource rather than
omitting the target.

Audit event versions are positive integer schema facts. Durable audit
recorders, exporters, retention workflows, and SIEM adapters should preserve
the version so old accountability records remain interpretable after contract
changes.

Core does not define audit database tables, object storage, retention policy,
legal hold, export workflows, SIEM integrations, CloudWatch sinks, or product
audit catalogs. Platform owns durable recorder implementations, and infra owns
storage resources and retention topology.

## Validation Contracts

`validation` defines the shared shape for explaining why unknown input is or is
not acceptable:

- `ValidationIssue` names the failed field/path and carries a translation-ready message descriptor.
- `validResult` represents accepted input with no issues.
- `invalidResult` requires at least one issue so failures are explicit.
- `isValid` and `isInvalid` narrow validation results for callers.
- `combineValidationResults` merges several validation checks into one result.
- `withValidationPathPrefix` lets composed validators keep precise nested paths.

Core validation should stay provider-free and product-neutral. Feature-specific
schemas, API response mapping, UI messages, and persistence constraints belong
in apps, platform, or feature packages that consume these contracts.
