# Shared Core values and capabilities

A feature needs to distinguish an entity ID from an ordinary string, represent
time consistently and handle checked results. This module provides those common
values and small capabilities. Consumers import its public surface through
`@kanbien/core/shared`; [index.ts](index.ts) only re-exports the owning files.

## Files and ownership

| Theme | Files and responsibility |
| --- | --- |
| Contracts | [branding.ts](contract/branding.ts) defines `Brand` and `brand`; [messages.ts](contract/messages.ts) owns message types and constructors; [errors.ts](contract/errors.ts) defines `CoreError`; [results.ts](contract/results.ts) owns checked results; [json-value.ts](contract/json-value.ts) defines serializable JSON values. |
| Identity | [contracts.ts](identity/contracts.ts) defines entity, correlation and causation IDs; [operations.ts](identity/operations.ts) constructs them. |
| Time | [contracts.ts](time/contracts.ts) defines `ISODateTime` and `Clock`; [date-time.ts](time/date-time.ts) parses and normalises time; [clock.ts](time/clock.ts) supplies system/fixed clocks; [request-context.ts](time/request-context.ts) combines correlation identity and time. |
| UUID | [contracts.ts](uuid/contracts.ts) defines `UUID` and `UuidGenerator`; [uuid.ts](uuid/uuid.ts) validates UUIDs; [generator.ts](uuid/generator.ts) supplies the current Web Crypto implementation. |
| JSON | [copy.ts](json/copy.ts) copies JSON values with finite-number and plain-object guards. |
| Diagnostics | [definitions.ts](diagnostics/definitions.ts) owns versioned schemas and their ordered collection; [records.ts](diagnostics/records.ts) builds records and attaches evidence to existing errors. |

The thematic files import their actual owners directly. They never import the
shared public barrel. Contract types may refer to the upstream Core diagnostics
types; definitions and record construction use its public framework. The Core
catalogue assembles the shared definitions through the public shared export.

## Using the public surface

This illustrative consumer parses a supplied timestamp:

```ts
import { isoDateTime } from "@kanbien/core/shared";

const time = isoDateTime("2026-11-06T14:00:00+02:00");
// { ok: true, value: "2026-11-06T12:00:00.000Z" }
```

`isoDateTime` first checks the string format, then calls `Date.parse`, then
normalises to UTC. The returned `Result` requires the caller to handle failure.
A rejected string produces `INVALID_ISO_DATE_TIME` and a structured reason.
Existing error `details.value` retains the submitted string; the diagnostic
record excludes it. Do not assume the whole error is safe to publish or log.
`isoDateTimeFromDate` normalises a supplied `Date`; a normalisation failure
retains the original thrown value with best-effort diagnostic attachment.
Parsing retains JavaScript Date's existing acceptance semantics.

For a deterministic operation, the caller can supply `fixedClock` and a
`UuidGenerator` instead of using ambient time and randomness:

```ts
import { fixedClock, isoDateTimeFromDate, uuid } from "@kanbien/core/shared";

const clock = fixedClock(new Date("2026-11-06T12:00:00Z"));
const now = isoDateTimeFromDate(clock.now());
// "2026-11-06T12:00:00.000Z"
const identifier = uuid("A0B1C2D3-E4F5-4A67-8B90-123456789ABC");
// { ok: true, value: "a0b1c2d3-e4f5-4a67-8b90-123456789abc" }
```

`fixedClock` returns a fresh Date on each read from the supplied Date's current
milliseconds; `systemClock` reads current system time. `requestContext`
combines a `CorrelationId` with a Date or an already branded timestamp,
normalising only the Date input. It does not generate identity.

## Public contracts and limits

- `Brand<Value, Name>` distinguishes values at compile time; `brand` applies
  that distinction without runtime validation. `EntityId`, `CorrelationId`
  and `CausationId` have `entityId`, `correlationId` and `causationId`
  constructors. These constructors do not enforce UUID syntax.
- `MessageKey`, `MessageParamValue`, `MessageParams` and
  `MessageDescriptor` describe a stable code, fallback message, optional
  translation key and primitive parameters. `messageKey` brands the key;
  `messageDescriptor` builds the descriptor without translating it.
- `CoreError` extends a message descriptor with optional cause, diagnostic
  classification, primary/related diagnostic records and legacy details.
  `Result<Value, Failure>` is either `{ ok: true, value }` or
  `{ ok: false, error }`. `ok`/`err` construct those branches;
  `isOk`/`isErr` narrow them. They do not catch exceptions.
- `ISODateTime` is the branded timestamp representation; `Clock` is the
  injectable time source and `RequestContext` groups correlation identity and
  a timestamp. Brands alone do not revalidate supplied data.
- `UUID` represents the UUID syntax accepted by `uuid`: versions 1–5,
  standard variant bits, case-insensitive input normalised to lowercase.
  `UuidGenerator.generate` returns a checked UUID. The current
  `systemUuidGenerator` invokes `globalThis.crypto.randomUUID()`, checks
  its output and returns a generation error on failure. It never retries.
- `JsonValue` describes JSON primitives, readonly arrays and string-keyed
  objects. `copyJsonValue` recursively copies arrays and plain objects,
  rejecting non-finite numbers and non-plain objects. Its label contributes to
  thrown messages; diagnostics carry bounded positions rather than values.
  Existing custom-array-map behaviour is preserved. This is not a general
  parser for arbitrary unknown data or cyclic objects.

## Diagnostic exports

`coreDateDiagnostic`, `coreDateNormalizationDiagnostic`,
`coreUuidDiagnostic`, `coreUuidGenerationDiagnostic` and
`coreJsonDiagnostic` define the supported reasons.
`coreSharedDiagnosticDefinitions` collects those definitions for catalogue
assembly. The corresponding `coreDateRecord`,
`coreDateNormalizationRecord`, `coreUuidRecord`,
`coreUuidGenerationRecord` and `coreJsonRecord` functions construct validated
records. Construction establishes schema validity; the actual operation must
establish the reported condition.

`attachCoreDiagnosticRecord` returns the original supplied value.
`inspectCoreDiagnosticAttachment` reports a `CoreDiagnosticAttachmentStatus`:
unsupported target, existing field, failed inspection, failed write or accepted
write. It does not overwrite an existing diagnostic property. A successful
attachment does not prove later retention or delivery. This module has no
reporter, logging sink or registration side effects.

## Verification and governance

The [time unit tests](../../tests/shared/time/unit/date-time-runtime.test.ts)
cover normalization and exact rejection diagnostics; the
[clock tests](../../tests/shared/time/unit/clock-runtime.test.ts) cover isolated
readings, and [request-context tests](../../tests/shared/time/unit/request-context-runtime.test.ts)
cover Date and branded-timestamp inputs. The
[time type-level tests](../../tests/shared/time/type-level/time-types.test.ts)
check accepted and rejected public types. These cases are grouped by capability,
theme and test type under the
[test layout standard](../../../../.agentic/03.product/tests/standards/test-layout.md).

The [UUID parsing unit tests](../../tests/shared/uuid/unit/uuid-runtime.test.ts)
cover accepted versions/variants, normalization and exact rejected-input
diagnostics. The [generation unit tests](../../tests/shared/uuid/unit/generator-runtime.test.ts)
retain a real-system success check and use controlled Crypto responses for
normalization, invalid output, thrown values and unavailable capabilities.
They assert primary/companion diagnostic meaning and single invocation, then
restore the original Crypto property even when a fixture throws. These cases
do not establish entropy, uniqueness or remote reporting. The
[UUID type-level tests](../../tests/shared/uuid/type-level/uuid-types.test.ts)
check branding, result narrowing and generator return shapes.

The [result tests](../../tests/shared/contract/unit/results-runtime.test.ts),
[message tests](../../tests/shared/contract/unit/messages-runtime.test.ts) and
[JSON copy tests](../../tests/shared/json/unit/json-runtime.test.ts) retain the
remaining shared runtime cases. Their type-level companions cover
[results](../../tests/shared/contract/type-level/results-types.test.ts),
[messages](../../tests/shared/contract/type-level/messages-types.test.ts),
[JSON](../../tests/shared/json/type-level/json-types.test.ts) and
[identity brands](../../tests/shared/identity/type-level/identity-types.test.ts).
The
[foundation diagnostics tests](../../tests/diagnostics/contract/foundation-diagnostics-runtime.test.ts)
and [diagnostic attachment tests](../../tests/diagnostics/contract/diagnostic-record-runtime.test.ts)
exercise the public consumers and failure behaviour. Type tests check brands
and result narrowing. The existing Core runtime command compiles nested runtime
fixtures and executes their source-backed compiled counterparts, excluding
type-only fixtures and stale compiled files. Its
[runner unit tests](../../tests/test-infrastructure/unit/runtime-runner-runtime.test.ts)
prove discovery and failure propagation. The Core boundary check and
[module-structure check](../../../../scripts/repo/module-structure/README.md)
cover source boundaries. Run the registered `core-runtime` and
`module-index-structure` checks through the repository check selector.
These establish local code behaviour, not feature persistence or AWS readiness.

The [public module standard](../../../../.agentic/03.product/standards/public-module-structure.md)
governs this split. Public names remain available through the shared barrel;
the old mixed index and private sibling diagnostic bridge have been retired.
