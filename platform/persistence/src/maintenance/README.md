# Persistence maintenance instructions

Before a program changes database tables or checks a restored database, it must
know which job was requested. For example, `"apply"` requests the existing table
migration job; `"connection"` requests only a connection check. This folder checks
those instructions. It does not connect to a database, run SQL or create tables.

The target supplies values from its environment. This module owns what those
values mean and when they are required. Core config performs the common text
and allowed-choice checks. The entrypoint receives either checked instructions
or a report that identifies each rejected instruction without repeating its value.

## What each file does

| File | Responsibility |
| --- | --- |
| [index.ts](index.ts) | Exposes the names below; contains no checking logic. The package root exposes the same names. |
| [contract/instructions.ts](contract/instructions.ts) | Declares the supported jobs, required information and returned result shapes. |
| [contract/acceptance-proof.ts](contract/acceptance-proof.ts) | Declares the existing reference test's record-ID and fingerprint formats. A fingerprint is the 64-character lowercase hexadecimal summary compared with the stored fact. These are not rules for every application's records. |
| [contract/reporting/diagnostics.ts](contract/reporting/diagnostics.ts) | Declares the two report codes and their permitted logical names and reasons. It does not decide whether an input is wrong. |
| [contract/reporting/diagnostics.v1.json](contract/reporting/diagnostics.v1.json) | Generated copy of those two definitions for readers that cannot import TypeScript. Do not edit it separately. |
| [domain/validation/instructions.ts](domain/validation/instructions.ts) | Selects the applicable requirements, asks Core to check values, and constructs either usable instructions or the declared failure report. |

## Worked example: a missing record ID

Illustrative code outside this module can import from the package root:

```typescript
import { validatePersistenceVerificationInstructions } from "@kanbien/platform-persistence";

const result = validatePersistenceVerificationInstructions(undefined, {
  "verification.expected-record-id": undefined,
  "verification.expected-fingerprint": "a".repeat(64),
});
```

1. The caller supplies no special mode, so normal record verification applies.
2. The function selects the two expected-record requirements from `contract/instructions.ts`.
3. Core checks both values. The ID is missing; the fingerprint passes its text pattern.
4. The function returns the following object to the caller. No database work has run.

```json
{
  "ok": false,
  "error": {
    "code": "CONFIGURATION_INVALID",
    "diagnostic": {
      "schema": "core/diagnostic-record/v1",
      "code": "persistence.verification-instructions-invalid",
      "definitionVersion": 1,
      "detail": {
        "issues": [{ "setting": "verification.expected-record-id", "reason": "missing" }]
      }
    }
  }
}
```

If the ID is `"core-persistence-example1"`, the same call succeeds and returns
`{ ok: true, value: { mode: "verify-record", expected: { recordId:
"core-persistence-example1", factDigest: "a".repeat(64) } } }`.
The caller uses those returned fields for its existing query and comparison;
it must not reread and use the original unchecked inputs.

If the mode is `"connection"`, the result is instead
`{ ok: true, value: { mode: "connection" } }`. Expected-record contents are not
checked because this job does not inspect a stored record.

```text
Target environment bindings       Platform maintenance contracts
map existing source names        declare job choices and proof formats
             |                              |
             +----------> maintenance validation <---- Core config checks
                                    |
                         checked instructions OR safe diagnostic
                                    |
                           existing target entrypoint
                      runs the job OR reports and stops
```

The actual callers are [migration](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts)
and [restore verification](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts).
Their [configuration binding](../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts)
reads the existing environment names and supplies the existing Platform config
loading process. The two report definitions also remain available through the
combined persistence catalogue and the target's generated reader catalogue.
Runtime registration uses each owner once, not both the combined reader
catalogue and its constituent catalogues.

## Public names and when to use them

- `persistenceMigrationRequirements`, `persistenceVerificationModeRequirements`
  and `persistenceExpectedRecordRequirements` are immutable lists of the checks
  this module owns. Reuse them rather than copying the accepted words or patterns.
- `persistenceAcceptanceProof` holds the two reference-proof text rules used by
  the expected-record list. It is not a general persistence record schema.
- `validatePersistenceMigrationInstructions(operation, check?)` accepts omitted
  operation as `"apply"`; rejects other unusable or unsupported values; returns
  `PersistenceMigrationInstructions` on success.
- `validatePersistenceVerificationInstructions(mode, expected, check?)` returns
  `PersistenceVerificationInstructions`: either connection mode or record mode
  with both checked proof fields. Independent record failures are returned together.
- `persistenceConnectionDiagnosticMode(value)` answers only whether the raw
  value is exactly `"connection"`. It preserves the existing verdict on early
  configuration failures; it is not a substitute for instruction validation.
- `PersistenceExpectedRecordInput` names the two supplied proof fields.
  `PersistenceInstructionFailure` describes the failed result and safe record.
- `PersistenceInstructionCheck` describes the optional **trusted code** checker
  argument. The default is Core's `validateConfigRequirements`; target composition
  supplies the existing Platform loader. This is not a hook for untrusted input
  to declare itself valid. Returned checked values, not original values, are used.
- `persistenceMigrationInstructionsDiagnostic` and
  `persistenceVerificationInstructionsDiagnostic` define the reports; their
  `persistenceMaintenanceDiagnosticCatalog` groups them for explicit registration.
  The JSON equivalent is available at
  `@kanbien/platform-persistence/maintenance/diagnostics.v1.json`.

## Compatibility and proof

For compatibility, an undefined, non-text, blank or surrounding-whitespace
verification mode still means normal record verification. A usable unsupported
mode is rejected, not treated as a request for record verification. A supplied
migration operation does not have that optional-mode behavior: wrong type,
blank text, surrounding whitespace and an unsupported choice are four distinct
rejections. Expected-record fields have five possible rejections each: missing,
wrong type, blank, surrounding whitespace and invalid format.

The report schema restricts field and reason names. It cannot itself prove
that a diagnosis is true. The checker and its tests establish which of these
fifteen failures actually occurred. Source-read exceptions are not relabelled
as missing content; this module does not fetch secrets or remote configuration.

[Maintenance runtime tests](../../tests/integration/maintenance-configuration-runtime.test.ts)
exercise all fifteen failures, defaults, combined problems and value safety.
[Compiled caller tests](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs)
prove rejection before pool/token/connection work; the
[restore fixture](../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/restore-diagnostic-test.mjs)
proves checked values reach the real query path and retains cleanup behavior.
Catalogue fixtures check local assets, freshness and selected Python readers.
These are local proofs, not a live database or deployment qualification.

The ownership requirements live in the harness's
[configuration standard](../../../../.agentic/03.product/standards/config-runtime-settings.md),
not in this README. New maintenance tasks need their own demonstrated requirements;
this module does not automatically enable rollback, new operations or new databases.
