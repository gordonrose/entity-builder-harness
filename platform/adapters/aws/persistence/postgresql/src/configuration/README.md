# PostgreSQL configuration

Before a connection can be created, this adapter needs a host, destination port,
database, schema and an explicit authentication reference. It also needs selected
pool/timeout/TLS policy. This folder owns those PostgreSQL requirements, not the
environment variable names or which target uses PostgreSQL.

## What each file does

| File | Job |
| --- | --- |
| [index.ts](index.ts) | Exposes the supported configuration functions and types. |
| [contract/types.ts](contract/types.ts) | Describes the complete accepted configuration and the separate policy supplied by a caller. |
| [contract/requirements.ts](contract/requirements.ts) | Declares the five required logical items and existing PostgreSQL text/login/identifier rules. |
| [contract/errors.ts](contract/errors.ts) | Describes the existing adapter failure code and fixed path/reason/reasonCode detail. |
| [domain/validation.ts](domain/validation.ts) | Checks direct configuration objects, retaining numeric input and first-failure behaviour. |
| [domain/assembly.ts](domain/assembly.ts) | Builds an object from checked logical values and explicitly selected policy, then applies direct adapter validation. |

Target consumers use the adapter's public root exports in [../index.ts](../index.ts).
Other adapter files use this folder's [index.ts](index.ts) rather than its private
contract/domain files. Inside this folder, files use their owning files directly. The former sibling forwarding file has
been retired; it did not provide another checker.

## Worked example and flow

The target binds `database.port` to a supplied source containing text "443".
It obtains the requirement from `postgreSqlPersistenceRequirements`; it does not
rewrite the accepted port range.

```text
target source bindings + adapter requirements
                    |
       Platform loader → Core checks
                    |
   { "database.port": 443, ...other checked values }
                    |
 assemblePostgreSqlPersistenceConfiguration(values, policy)
                    |
    adapter's direct configuration validator
                    |
       accepted connection configuration
```

All five logical values are needed for assembly. Supplying valid values produces
the existing adapter success object. A blank port fails in Core before assembly,
with `{ setting: "database.port", reason: "blank" }`. Direct numeric callers can
continue to call `postgreSqlPersistenceConfiguration` with a complete object;
passing a text port there remains a wrong-type failure. Those paths share a
requirement, not identical input representations.

For an administrator operation, target code binds the authentication reference
to its administrator source and maps that logical finding to the existing
administrator diagnostic name. The adapter does not learn target purposes.

## Exported functions and variables

### postgreSqlPersistenceRequirements

The source-independent five-item list in `contract/requirements.ts`, in host,
port, database, schema, reference order. It uses Core's shared destination-port
constraint and this adapter's existing text rules. It supplies no defaults,
source names, credentials or client. Future compatible targets may reuse it.

### assemblePostgreSqlPersistenceConfiguration

The function in `domain/assembly.ts` accepts checked logical values plus
`PostgreSqlPersistenceConfigurationPolicy`. It maps only the declared fields
and explicit policy into the direct validator, returning its success/failure.
An omitted checked value still fails; arbitrary extra policy fields cannot
replace host/port/reference values.

### postgreSqlPersistenceConfiguration

The retained direct checker in `domain/validation.ts`. Its input is the complete
`PostgreSqlPersistenceConfiguration`; output is the existing checked result.
It preserves text checks, numeric pool/timeouts/port limits and strict injected
verify-full TLS. It does not obtain credentials or open connections.

### postgreSqlPersistenceConfigurationTextRules

The retained host, database, schema and reference text rules. The requirement
list and direct validator use their owning patterns. Target callers can retain
existing imports without copying those patterns.

### postgreSqlLoginNameRule

The existing separate login-name rule; a leading underscore remains permitted.
This is not the database/schema naming rule.

### postgreSqlIdentifier

The retained internal compatibility helper in `domain/validation.ts` returns an
accepted SQL identifier unchanged, or undefined. It does not quote arbitrary SQL.
It remains available through the parent compatibility file, not newly exposed
through the adapter root.

## Types and internal exports

`PostgreSqlPersistenceConfiguration` describes all accepted fields.
`PostgreSqlPersistenceConfigurationPolicy` selects pool size, three timeouts and
TLS policy from that shape. Targets choose values; the adapter checks its supported
limits. Both are in `contract/types.ts`.

`PostgreSqlPersistenceConfigurationError` in `contract/errors.ts` retains
`PLATFORM_ADAPTER_AWS_POSTGRESQL_PERSISTENCE_CONFIG_INVALID` and its old detail.
Private pattern exports in `contract/requirements.ts` let the validator use one
owner; they are not new public adapter imports.

## Limits, governance and proof

Success establishes acceptable configuration, not a reachable database, valid
credentials or a successful TLS handshake. Those operations and observations
remain in the parent connection/security implementation.

The [configuration standard](../../../../../../../.agentic/03.product/standards/config-runtime-settings.md)
and [module structure standard](../../../../../../../.agentic/03.product/standards/public-module-structure.md)
govern ownership. The existing
[adapter runtime fixture](../../tests/contract/postgresql-persistence-adapter-runtime.test.ts)
checks direct compatibility and actual shared-rule use; the target configuration
fixture checks the real checked-loading path. Live deployment and engine
qualification are separate from these local checks.
