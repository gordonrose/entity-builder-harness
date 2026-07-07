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

## Shared Primitives

`shared` contains the lowest-level vocabulary used by the rest of core:

- `Brand` and `EntityId` distinguish important string identifiers at type level.
- `CorrelationId` connects logs, audit records, events, and errors from one request.
- `ISODateTime` stores strict ISO date-time values with explicit timezone
  information in a JSON-safe text form.
- `MessageDescriptor` carries stable meaning plus optional translation hooks.
- `Result`, `ok`, `err`, `isOk`, and `isErr` make expected success/failure explicit.
- `CoreError` gives failures a stable `code`, `defaultMessage`, optional translation metadata, and optional debugging metadata.
- `Clock`, `systemClock`, and `fixedClock` keep time-dependent code testable.
- `RequestContext` carries only the minimum shared request metadata.

Keep this module small. Tenant, principal, permission, persistence, audit, and
event-specific concepts should live in their own modules and import shared
primitives when needed.

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
copy for every locale. The future `i18n` layer should translate `messageKey`
and `params`; the future `localization` layer should format locale-sensitive
dates, numbers, currencies, and regions.

Operational logs may still use direct log messages. User-facing errors,
validation issues, policy denials, notifications, reports, and API/display
responses should use translation-ready descriptors.

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
