# Lease duration instructions

A lease gives one worker or relay a time-limited claim on a piece of work.
For example, a duration of `1000` means that a claim acquired now expires one
second later. This module checks the duration before it is used. It does not
grant a claim, read a database, renew a claim, or choose how long a target needs.

The duration must be supplied as a finite positive whole number of milliseconds.
There is no default and no newly imposed maximum. `1000` passes; `"1000"`,
`0`, `0.5`, a missing value and infinity do not. Values are not converted.

## What each file does

| File | Responsibility |
| --- | --- |
| [index.ts](index.ts) | Exposes the approved names below without implementing checks. |
| [contract/requirements.ts](contract/requirements.ts) | Declares the positive-whole-number requirement and the allowed failure reasons. |
| [domain/validation/duration.ts](domain/validation/duration.ts) | Uses Core config's numeric check, then the lease requirement, to return a checked duration or reason. |
| [contract/reporting/diagnostics.ts](contract/reporting/diagnostics.ts) | Defines and constructs the relay-construction diagnostic; it does not decide whether a duration is valid. |
| [contract/reporting/errors.ts](contract/reporting/errors.ts) | Creates a fixed-message TypeError carrying that diagnostic. |
| [contract/reporting/diagnostics.v1.json](contract/reporting/diagnostics.v1.json) | Generated copy for diagnostic readers. Edit the TypeScript definition, not this file. |

## Worked example and callers

`validatePersistenceLeaseDuration(1000)` returns `{ ok: true, value: 1000 }`.
`validatePersistenceLeaseDuration(0)` returns
`{ ok: false, error: { reason: "not-positive" } }`.

The same check has three current callers, each retaining its own response form:

```text
Target supplies duration
           |
           +-> relay.ts: check before returning a relay
           +-> workers/src/worker.ts: check before returning a worker
           +-> types.ts: check when constructing a particular lease
                         |
             leasing/domain/validation/duration.ts
                         |
             Core config numeric check + shared lease requirement
                    /                   \
             checked number          precise reason
                    |                   |
             caller uses it      caller's existing error/report form
```

`relay.ts` captures the accepted duration once at construction and uses it when
claiming work. If invalid, it throws the controlled relay error before reading
the clock, selecting the store or sending a message. The worker preserves its
existing durable-configuration Result and diagnostic. `types.ts` preserves the
existing lease-construction Result and diagnostic. None redefines the numeric
rule. The expiry calculation is still performed in `types.ts`, not this folder.

## Public names and use

Import through `@kanbien/platform-persistence`:

- `persistenceLeaseDurationRequirement` declares minimum `1` and whole-number
  interpretation. Use the validator rather than copying these bounds.
- `persistenceLeaseDurationReasons` lists `missing`, `wrong-type`, `not-finite`,
  `invalid-integer` and `not-positive`. `PersistenceLeaseDurationReason` restricts
  TypeScript arguments to those names; it does not itself check a value.
- `validatePersistenceLeaseDuration(value)` returns the checked number or one
  of those reasons. Use the returned number, not a second read of the input.
- `persistenceRelayConfigurationDiagnostic` defines the safe record with code
  `persistence.relay-configuration-invalid`, version `1`, and fixed operation,
  phase, setting and effect (`relay-not-created`). Only the reason varies.
- `persistenceRelayConfigurationRecord(reason)` constructs that record;
  `persistenceRelayConfigurationError(reason)` attaches it to a TypeError.
  These functions describe relay construction, not every possible lease failure.
- `persistenceLeasingDiagnosticCatalog` exposes this module's definition for
  selected readers. The combined persistence catalogue also includes it.

Tools may import `@kanbien/platform-persistence/leasing/diagnostics.v1.json`.
Reports never include the supplied duration or a native exception message.
A supplied property getter that throws still throws its original exception;
that is not misreported as an invalid number.

## Governance and tests

The [configuration standard](../../../../.agentic/03.product/standards/config-runtime-settings.md#worker-retry-and-persistence-leases)
places this common requirement with Platform persistence. Future relay/worker
paths should use this check and consume its successful value.
`tests/leasing-configuration-runtime.test.ts` and the type companion prove the
value cases, safe records, actual relay/lease use and shared-check reuse. Worker
tests separately prove that caller. Existing persistence tests cover the
surrounding state transitions. A valid numeric duration alone does not prove
database connectivity, timely execution, a representable future timestamp, or
successful distributed coordination.
