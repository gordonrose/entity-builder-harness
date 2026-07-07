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
- `ISODateTime` stores timestamps in a JSON-safe text form.
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
- `recordConfigSource` is a pure in-memory source for tests and simple composed
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
