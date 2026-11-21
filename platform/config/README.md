# Platform configuration

A program may need a database port supplied as text, such as "443". The database
implementation declares what it requires; target code says which supplied item
contains it. This module connects those instructions, asks Core to check the
information, and passes accepted values to the implementation's assembly function.

It does not choose a database, create clients, fetch secrets on its own, provision
resources or decide feature behaviour. A source is a supplied object with a
`get(name)` function; that function may read information or throw.

## What each file does

| File | Responsibility |
| --- | --- |
| [src/index.ts](src/index.ts) | Makes the public functions/types below available; no implementation. |
| [src/diagnostics.ts](src/diagnostics.ts) | Keeps old report-helper imports working by re-exporting Core config and Platform's own definitions. |
| [src/contract/loading.ts](src/contract/loading.ts) | Describes requirements, concrete source bindings, supplied reader, optional comparisons and assembly, plus the returned result. |
| [src/contract/validation.ts](src/contract/validation.ts) | Describes the existing registered-schema input and failure shapes. |
| [src/contract/errors.ts](src/contract/errors.ts) | Creates a fixed diagnostic-bearing TypeError when loading instructions are invalid. No supplied values enter it. |
| [src/contract/diagnostics.ts](src/contract/diagnostics.ts) | Owns schema-position, thrown-schema and loading-declaration definitions and their catalog. |
| [src/domain/loading.ts](src/domain/loading.ts) | Coordinates checking and assembly; returns failure without assembling invalid values. |
| [src/domain/source-resolution.ts](src/domain/source-resolution.ts) | Checks and snapshots bindings, then translates logical names into supplied source keys. |
| [src/domain/validation.ts](src/domain/validation.ts) | Runs existing registered schemas in order, preserving their result/throw behaviour and optional diagnostic observations. |

The package manifest exposes the index. The tsconfig files govern compilation
and the tests folder contains type, runtime and dependency-boundary proof.

## Worked example: one required value

This is invented calling code outside Platform config:

```typescript
import { destinationPortConstraint, recordConfigSource } from "@kanbien/core/config";
import { loadPlatformConfiguration } from "@kanbien/platform-config";

const result = loadPlatformConfiguration({
  requirements: [{ setting: "database.port", rule: destinationPortConstraint }],
  bindings: { "database.port": "DATABASE_PORT" },
  source: recordConfigSource({ DATABASE_PORT: "443" }),
  assemble: values => ({ ok: true, value: { port: values["database.port"] } }),
});
```

The requirement describes the logical item `database.port`. The binding says to
read it from `DATABASE_PORT`; it does not supply a value. The source supplies the
text "443". Core checks that text and returns the number 443. Only then does
assembly run, producing:

```typescript
{ ok: true, value: { port: 443 } }
```

If the item is absent, the result is instead:

```typescript
{
  ok: false,
  error: {
    code: "CONFIGURATION_INVALID",
    issues: [{ setting: "database.port", reason: "missing" }]
  }
}
```

Assembly does not run. Text "-20" gives `out-of-range`; a space gives `blank`.
No diagnostic packet is automatically constructed for these ordinary field
findings: the consuming operation chooses its approved definition and delivery.

## Several values and other failures

Suppose the caller also declares a text requirement named `service.name`, bound
to `SERVICE_NAME`. Supplying port "-20" and name " " produces this exact finding
list, in requirement order:

```typescript
[
  { setting: "database.port", reason: "out-of-range" },
  { setting: "service.name", reason: "blank" }
]
```

That list is inside the same `CONFIGURATION_INVALID` failure, and assembly is
still not called. Extra supplied items are not checked or passed to assembly.
Bindings must match the declared requirements: a missing or extra binding is
an instruction error, rejected before reading any values.

A reader throwing does not establish missing or invalid contents. Core preserves
the thrown value and adds its source-boundary evidence where possible. An
assembly failure result is returned unchanged; an assembly throw also propagates.
Do not log raw exceptions: they may contain private information.

## How the responsibilities connect

```text
Dependency implementation             Target
declares logical requirements         chooses implementation and source bindings
                 \\                    /
                  Platform config loading
                   reads through supplied source
                             |
                   Core config checks values
                             |
                   accepted values only
                             |
                  dependency-owned assembly
                             |
                   result returns to target
                             |
                 entrypoint continues or stops
```

This process is reusable for future dependencies. Provider selection and client
construction remain outside this module; it never switches services after a
failure. Configuration success is not proof of a working remote connection.

## Public loading API

### loadPlatformConfiguration

Implemented in `src/domain/loading.ts`. Accepts the input shown above. It checks
instructions, invokes Core's `validateConfigRequirements`, then calls `assemble`
only on success. An optional `relationships` list uses Core's declared comparison
rules. All declared inputs are required in this API; callers select conditional
requirements and permitted defaults explicitly before invoking it.

### PlatformConfigurationLoadingInput

The type in `contract/loading.ts` describes that request. Its two type parameters
describe the configuration assembly produces and the failure assembly can return.
This is not permission to pass unchecked values to a client.

### PlatformConfigurationLoadingResult

The result type in the same file permits successful assembled configuration,
Core setting/comparison failures or the declared assembly failure. Throws remain
throws, not additional invented result fields.

## Existing registered-schema API

`validatePlatformConfigSchemas` in `domain/validation.ts` still runs each
`ConfigSchema.parse` in order. Success returns the parsed values; the first
rejection returns the existing `PlatformConfigError`. `assertPlatformConfigValid`
uses it but returns no parsed values on success.

`PlatformConfigValidationInput` describes its source, schemas, selected
`diagnosticDefinitions` and optional `onDiagnostic` observer.
`PlatformConfigErrorCode` retains `PLATFORM_CONFIG_INVALID`;
`PlatformConfigError` retains legacy details and optional checked evidence.
These types live in `contract/validation.ts`.

This remains supported for existing consumers. It is not a competing provider
selection mechanism. Callback throws/rejections cannot change parsing, and the
original schema/projection throw is rethrown. Observation is not proof of delivery.

## Reports and compatibility exports

`defineConfigurationDiagnostic` and `configurationDiagnostic` define and
construct approved setting reports. `defineConfigurationRelationshipDiagnostics`
and `configurationRelationshipDiagnostic` do the same for comparisons.
`defineConfigurationSourceReadDiagnostic` and
`configurationSourceReadDiagnosticRecord` describe established read failures.

These six names are now implemented in Core config's
[reporting capability](../../packages/core/src/config/domain/reporting/diagnostic-reporting.ts)
and explained in its [guide](../../packages/core/src/config/README.md#reading-domaindiagnostic-reportingts).
Platform re-exports them for existing callers; their historical classification
and packet shapes remain unchanged.

`platformConfigDiagnostic` is the existing version-1 schema rejection definition.
`platformConfigDiagnosticCatalog` includes its retained larger-position version,
the thrown-boundary definition and the new finite loading-declaration definition.
Register/select this catalog where those records are consumed.

## Governance and proof

The [configuration standard](../../.agentic/03.product/standards/config-runtime-settings.md)
owns requirements; the [module structure standard](../../.agentic/03.product/standards/public-module-structure.md)
owns file/dependency boundaries. This guide explains their implementation.

[Loading runtime tests](tests/integration/configuration-loading-runtime.test.ts) exercise the
examples, read order, comparisons, invalid instructions, throw identity, assembly
failures and actual shared-result consumption. Existing runtime/evidence/type
tests and the package boundary checker retain registered-schema/report proof.
No source scan proves all future callers use checked results; actual caller
tests and source review remain necessary.
