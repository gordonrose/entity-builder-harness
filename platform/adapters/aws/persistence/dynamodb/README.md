# AWS DynamoDB Persistence Adapter

This package makes the provider-neutral persistence contracts durable in one
selected DynamoDB table. It belongs at the target composition boundary: apps
use Core and `platform/persistence`; the staging target chooses this adapter
and supplies its table and index names.

It is a deliberately narrow reference adapter for the harmless platform-smoke
workflow. It is not a generic ORM, an entity-schema engine, a migration
framework, or a claim that DynamoDB is the future storage choice for every
product entity.

| File | Responsibility |
| --- | --- |
| `src/configuration/index.ts` | Exposes the checker and its two public types; it contains no checking logic. |
| `src/configuration/contract/types.ts` | Describes the four pieces of text the existing adapter needs: region, table name and two index names. |
| `src/configuration/contract/errors.ts` | Describes the failure result returned when supplied configuration is rejected. |
| `src/configuration/domain/validation.ts` | Checks the supplied object, checks required fields through Core's string reader, then applies the existing blank and length checks. It performs no environment lookup or AWS operation. |
| `src/client.ts` | Names the small command-client seam and creates the AWS SDK client only when the target composition selects it. |
| `src/records.ts` | Owns the private DynamoDB key and attribute encoding for outbox, processing, and lineage rows. |
| `src/outbox-store.ts` | Implements due-work lookup, conditional relay leasing, and fence-protected publication marking. |
| `src/processing-store.ts` | Implements durable worker claims, retry release, completion, and stale-fence rejection. |
| `src/lineage-store.ts` | Appends bounded record-change facts and queries them by record or direct cause. |
| `src/transactions.ts` | Builds the two-fact transaction and the provider-local atomic-writer seam through which target composition can add one product-owned write. |
| `src/errors.ts` | Maps AWS failure categories to bounded platform errors; it never returns raw provider payloads. |
| `src/observations.ts` | Observes existing command boundaries and bounded stored-attribute predicates through the shared Platform catalog. |
| `src/index.ts` | Deliberate public composition exports only. |

## Checking the information before use

Before this adapter can use a table, the code choosing it must supply the AWS
region, the table name and the names of its two existing lookups. These supplied
values are its configuration. An index is a database lookup structure; deciding
which lookups persistence needs is separate from checking that a name was supplied.

The configuration folder separates the description of the information
(`contract/`) from the code that checks it (`domain/`). The public package root
and `src/configuration/index.ts` expose the same checker. Other adapter files import
types through `configuration/index.ts`, this submodule's supported interface. The former sibling
forwarding file has been retired; no second checker was removed.

The three public names remain:

- `DynamoDbPersistenceConfiguration`: a TypeScript description of the four
  required string fields. It helps check code while building; it does not
  inspect values received when the program runs.
- `DynamoDbPersistenceConfigurationError`: the failure's code, fixed summary,
  field/reason description and optional diagnostic packet.
- `dynamoDbPersistenceConfiguration(input)`: the function that actually checks
  the supplied information and returns either accepted information or a failure.
  Future composition code can reuse it; it is not exclusive to the smoke app.

### Example: complete information

This illustrative code is outside the adapter. It uses the public package
export; it is not another file that must be added to the repo.

```typescript
import { dynamoDbPersistenceConfiguration } from "@kanbien/platform-adapter-aws-persistence-dynamodb";

const supplied = {
  region: "example-region",
  tableName: "example-records",
  outboxDueIndexName: "example-due",
  lineageCauseIndexName: "example-cause",
};
const result = dynamoDbPersistenceConfiguration(supplied);
```

The function first obtains the supplied properties once for checking, without
catching or relabelling an exception thrown while reading them. Core's
`stringConfigValue` reads that captured information to establish whether each
required field exists and contains text. The adapter then runs its existing
blank/length checks. On success, `result` is `{ ok: true, value: ... }`, where
`value` is the existing copied configuration. Accepted text is not trimmed.
This example passes the checks; it does not establish that the example region,
table or indexes exist in AWS.

### Example: information is missing or has the wrong type

JavaScript callers or unchecked external information can omit `region`, even
though the TypeScript description requires it. The function then returns:

```json
{
  "ok": false,
  "error": {
    "code": "PLATFORM_ADAPTER_AWS_DYNAMODB_PERSISTENCE_CONFIG_INVALID",
    "defaultMessage": "DynamoDB persistence adapter configuration is invalid.",
    "details": { "path": "region", "reason": "A required value is missing." },
    "diagnosticRecord": {
      "schema": "core/diagnostic-record/v1",
      "code": "persistence.configuration-input-invalid",
      "definitionVersion": 1,
      "detail": { "field": "region", "reason": "missing" }
    }
  }
}
```

If `region` is a number instead, the same failure structure identifies
`wrong-type`; it does not attempt a text operation on that number. If both
`region` and `tableName` have presence/type problems, region is reported first.
The fixed order is region, table, due-index name, cause-index name. This returns
one failure, not a list. Empty or spaces-only strings still use the historical
`persistence.configuration-invalid` diagnostic with reason `blank`.

```text
Composition code supplies the existing four fields
    -> configuration/index.ts exposes the checker
    -> domain/validation.ts checks the captured information
         -> Core string reader establishes missing / wrong type
         -> existing adapter checks establish blank / too long
    <- accepted copy OR structured failure returns to composition code
```

Platform persistence owns the diagnostic definitions in
[`platform/persistence/src/diagnostics.ts`](../../../../persistence/src/diagnostics.ts).
Core supplies reusable reading and diagnostic-packet construction. This adapter
establishes which field failed. The code calling it must handle the returned
failure before starting dependent work; the SDK client factory does not
automatically call this checker.

The [configuration standard](../../../../../.agentic/03.product/standards/config-runtime-settings.md)
and [module structure standard](../../../../../.agentic/03.product/standards/public-module-structure.md)
own the requirements. Their checks and source review do not prove every caller
uses the result correctly.

**Not yet implemented in this slice:** full dependency-loading adoption,
extra-property policy and index-specific configuration changes. Additional
properties keep their legacy checking/copying behaviour; this is not a promise
to turn every malformed extra into a structured failure. The known oversized-
index error-path mismatch also remains. These are recorded under N01B in the
[configuration plan](../../../../../.agentic/03.product/plans/implementation/configuration-ownership-and-loading.md#n01b-persistence-handoff--deferred-not-lost)
for the later persistence slice, not silently fixed here. No indexes or resources
are created by these checks.

## The table model

The initial target will use one table with a partition key `PK` and sort key
`SK`. The keys are an adapter-private implementation detail; product code must
not construct them.

| Logical record | Primary key | Index/access path | Why it exists |
| --- | --- | --- | --- |
| Outbox | `OUTBOX#<outbox-id>` / `OUTBOX` | Due index: `OUTBOX#DELIVERABLE` ordered by the next eligible timestamp | A relay can ask for due delivery obligations without scanning the table. A pending entry is due from `createdAt`; a leased one is due again only after lease expiry. |
| Processing claim | `PROCESSING#<outbox-id>` / `PROCESSING` | Direct read by stable outbox identity | A worker can atomically claim, retry, or complete the same logical work even when SQS redelivers it. |
| Record-change lineage | `LINEAGE#<kind>#<id>` / zero-padded revision | Cause index: `CAUSE#<direct-cause>` ordered by occurrence | An operator can find a record's safe revisions or trace a direct event to its bounded changes. |

The table contains references, states, timestamps, attempt/fence values, and
the allowlisted Core fields only. It must not contain a business payload,
request body, secret, queue receipt handle, raw provider response, or complete
before/after entity image.

## Conditions make concurrent changes safe

DynamoDB evaluates a conditional update and its write as one operation. The
adapter uses that property for the controls defined by `platform/persistence`:

- an outbox claim checks the current state, prior attempt, and—when present—the
  previous fence and expiry before writing the next lease;
- publication checks that the same lease has not expired and its fence still
  matches;
- a processing claim can create a new row, take a retry-eligible row, or take
  an expired claim, but never take an active one;
- worker completion and retry release require the current, unexpired fence.

If a competing operation wins first, the adapter rereads the row and returns
the current state (`lease-active` or `already-completed`) where possible.
Publication/completion/release reconciliation also retains the existing policy
that successful validation may return success without issuing another write.
That is not proof that this caller durably performed the requested mutation;
diagnostics report only the read result. Changing that policy is separate work.

## Transaction boundary—and its current limit

`DynamoDbPlatformPersistenceFactWriter` uses `TransactWriteItems` to make the
initial lineage fact and outbox obligation appear together or not at all. This
protects the two platform-owned durable facts.

`DynamoDbPlatformPersistenceAtomicWriter` is the next, stricter seam. It gives
an app repository an opaque Core transaction handle. Only target composition
can pass that handle to `stageDynamoDbTransactionWrite`, which contributes one
provider-specific product-state operation to the same DynamoDB transaction.
The writer refuses to send an incomplete operation: it requires at least one
product participant and at least one validated lineage/outbox mutation. The
adapter's recording-client test proves the resulting request has all three
writes.

The scope permits no after-commit callback. Reliable later work belongs in the
durable outbox, not a process-local callback that might be lost after commit.

It intentionally does **not** claim to atomically write an arbitrary product
entity too. The Core `Transaction` interface is deliberately provider-neutral
and does not expose a generic item model. The next smoke-app slice must
implement the target-composed repository that uses this seam so the work-item
state, lineage, and outbox obligation become one DynamoDB transaction. The
adapter will not pretend that two separately saved records are atomic merely
because they are adjacent in code.

## DynamoDB limits and target responsibilities

- A DynamoDB transaction supports at most 100 write actions and a 4 MB request
  size. The smoke transaction is intentionally tiny; a future product must
  design and validate against these limits.
- Reads used to decide leases and fences are strongly consistent. Index queries
  are eventually consistent, so they select candidates only; the conditional
  claim remains the authority.
- DynamoDB TTL is not used to decide a lease, business retention, restore, or
  legal hold. If later used for a disposable technical record, it is only
  best-effort background deletion.
- CloudFormation owns table/index definitions, encryption, point-in-time
  recovery, backups, tagging, retention posture, and IAM. The target profile
  owns selected non-secret names and references. This package owns neither.

## Bounded provider diagnostics

The adapter never exposes an AWS error message, request identifier, ARN, item,
or provider response as a platform error. When an operation fails, it carries
only its fixed logical operation name and one of these finite categories:
`access_denied`, `conditional_check_failed`, `resource_not_found`,
`validation`, `throttled`, `transport`, or `unknown`.

These legacy parameters retain their original meaning and getter behavior.
Optional `PlatformPersistenceDiagnosticOptions` on stores, writers and SDK
client construction add selected safe diagnostic records without altering them.
`atomicWriter.run(operation, diagnostics?)` owns its invocation's observer;
omission uses defaults, while an explicit empty object silences the defaults.
Observers use the existing target-selected/profile-governed reporting seam;
exceptions and rejected observer promises cannot change workload results.

The command records distinguish selection, argument encoding, SDK invocation,
response traversal and decoding. Client construction is not a connection test.
Only positively supplied finite native invocation names select a native meaning;
transaction cancellation alone does not establish a condition conflict. Supplied
cancellation reasons are reduced to at most64ordinal/finite-code observations
with explicit truncation. Accessors are not invoked to discover optional facts.
Unknown getter/conversion throws remain unknown command boundaries, not invalid
stored data. Existing rejected attribute predicates are coalesced to at most16
logical issues with counts/positions and explicit truncation; no stored values,
keys, identifiers, provider text or command payload enters diagnostic detail.
Independent own records do not consume any of a source's primary/eight slots.

The outbox tests additionally prove that each DynamoDB conditional request
supplies only values that its chosen expression references. Initial claims and
expired-lease reclaims use different condition branches, so their expression
value maps must differ too. DynamoDB treats an unused placeholder as a
validation error rather than ignoring it.

## Safe imports

```text
app / platform composition
  -> @kanbien/core + @kanbien/platform-persistence
  -> this adapter (only at AWS composition)
  -> AWS SDK
```

No Core or generic Platform source may import this package. No app should know
the physical key names, index names, condition expressions, or AWS SDK types.

## Test evidence

The deterministic tests use a recording command client rather than AWS. They
verify configuration rejection, item shape, due-index query shape, two-fact and
three-write transaction construction, incomplete-transaction rejection,
conditional claim/fence operations, duplicate/conditional error translation,
and import boundaries. Passing them proves local request construction; it is
not live AWS evidence.
