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
| `src/configuration.ts` | Validates the explicitly injected region, table, and index names. It performs no environment lookup. |
| `src/client.ts` | Names the small command-client seam and creates the AWS SDK client only when the target composition selects it. |
| `src/records.ts` | Owns the private DynamoDB key and attribute encoding for outbox, processing, and lineage rows. |
| `src/outbox-store.ts` | Implements due-work lookup, conditional relay leasing, and fence-protected publication marking. |
| `src/processing-store.ts` | Implements durable worker claims, retry release, completion, and stale-fence rejection. |
| `src/lineage-store.ts` | Appends bounded record-change facts and queries them by record or direct cause. |
| `src/transactions.ts` | Builds the two-fact transaction and the provider-local atomic-writer seam through which target composition can add one product-owned write. |
| `src/errors.ts` | Maps AWS failure categories to bounded platform errors; it never returns raw provider payloads. |
| `src/index.ts` | Deliberate public composition exports only. |

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
the truthful state (`lease-active` or `already-completed`) where possible. It
does not turn a race into a false success.

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

The Kanbien relay entrypoint has a second allowlist before it writes either
field to its structured startup-failure log. This gives an operator enough
information to correct a target configuration safely—for example,
`claim_outbox` plus `validation`—without creating an accidental diagnostic
channel for customer data or AWS provider payloads.

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
