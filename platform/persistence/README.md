# Platform Persistence

`@kanbien/platform-persistence` implements provider-neutral coordination for
durable delivery. It uses the stable Core outbox and lineage facts, then owns
the mutable mechanics that make retries safe: attempts, leases, fences, and
terminal processing completion.

This package does not select a database, queue, scheduler, cloud region, or
application entity. The first provider implementation will live separately at
`platform/adapters/aws/persistence/dynamodb/`.

## Source map

| File | Owns | Does not own |
| --- | --- | --- |
| `errors.ts` | Stable, provider-neutral platform-persistence failure meanings. | Provider exception objects or application error policy. |
| `observability.ts` | Closed no-payload transition vocabulary and best-effort observer port. | Logging, metric, trace-provider selection, profile policy, or cloud delivery. |
| `types.ts` | Mutable outbox/processing record shapes, attempts, leases, fences, and safe constructors. | A database representation or target configuration. |
| `outbox.ts` | Pending-entry storage port, claim/lease/publish transitions, and deterministic in-memory proof store. | Queue sends; a relay calls a queue adapter after it claims an entry. |
| `processing.ts` | Worker claim, release-for-retry, and completion transitions; duplicate recognition; and stale-fence rejection. | A job handler's business effect or queue acknowledgement. |
| `lineage.ts` | Append-oriented record-change storage port and deterministic in-memory proof store. | Full record snapshots, free-form metadata, or audit-event storage. |
| `relay.ts` | One-entry outbox claiming, minimal queue-envelope creation, sending, and post-acceptance publication marking. | Queue receive, worker retry/DLQ policy, acknowledgement, target lifecycle, or provider APIs. |
| `transaction.ts` | The atomic-write port and the validated state-change/lineage/outbox mutation envelope. | A pretend in-memory transaction or a provider-specific database transaction. |
| `index.ts` | Deliberate public exports. | Automatic publication of internal helper details. |

## The key safety sequence

1. A transaction makes a work-item state, safe change entry, and immutable
   Core outbox entry (including its stable work-item reference) durable together.
2. A relay claims a pending outbox entry. The claim has an expiring lease and
   a higher fence than every earlier claim.
3. After the queue accepts the message, the relay marks the entry published
   using that same fence. A crash before this marker may produce a duplicate
   send; it must not lose the obligation.
4. A configured worker claims processing of the stable outbox ID. It stores
   success or terminal failure before its existing queue-success/dead-letter
   outcome; it releases its current fenced claim before a retry.
5. A claimant must complete before its lease expires. A stale relay or worker
   cannot write after a later claimant because its older fence is rejected.

An in-memory store proves those state rules locally. It is not durable and is
not a substitute for the later adapter or AWS evidence.

## The relay boundary

The relay is the bridge between a durable outbox promise and the existing Core
queue-send contract. It claims one due entry, sends a queue message containing
only the stable outbox identity, then marks the entry published with the same
unexpired fence. A queue-send failure leaves the entry leased for later retry;
a crash after queue acceptance but before the marker may create a duplicate,
which the worker's stable idempotency identity must tolerate.

The relay does not receive messages, retry a job, dead-letter a job,
acknowledge a provider delivery, emit worker telemetry, or manage worker
shutdown. Those responsibilities remain with the existing worker and provider
queue boundaries. The concrete queue sender and durable outbox store remain
future adapter work.

## Transition observability

The relay and optional durable worker emit closed transition facts through an
optional `PlatformPersistenceObserver`. The persistence package owns only the
fact that a named transition happened—for example `outbox.published`,
`processing.retry_released`, or `processing.duplicate_terminal_failure`. It
does not send an outbox ID, payload, record subject, tenant, fence, attempt,
queue receipt, provider response, or a raw error message as telemetry data.

`platform/observability` provides the complementary profile-governed observer.
It projects capability/action/execution-context/outcome and a bounded error
class into fixed log and trace names and fixed metric series. A Core correlation
reference may link logs, while an existing trace parent may link spans; neither
becomes a metric label or general trace attribute. Until an owning app
registers a profile and target composition approves its metric catalogue
entries, these local observer hooks are not live target evidence.

## The worker-processing boundary

`platform/workers` optionally composes this package's `PlatformProcessingStore`
for a dedicated durable-outbox queue. It requires one stable identity in three
places: the Core queue message ID, its idempotency key, and the minimal payload
field `outboxEntryId`. A mismatch is rejected before the handler runs.

When processing is configured, the durable store—not an optional in-memory
idempotency helper—is the authority for duplicate protection. A completed
**successful** delivery skips the handler and can be acknowledged. A completed
`terminal-failure` also skips the handler, but remains a non-success
dead-letter outcome so the transport can redrive it to its DLQ. A handler
failure releases the current fence so the worker's normal retry path can
reclaim it; a final failure records `terminal-failure` before the worker
reports dead-lettering. The concrete adapter still owns receipt handles and
physical acknowledgement.

## The atomic-write seam

The `PlatformPersistenceAtomicWriter` is a port for an adapter that can make a
product-state write, a `RecordChange`, and an `OutboxEntry` commit together.
The product passes `scope.transaction` to its transaction-aware repository,
then calls `scope.stage(...)` with a `platformPersistenceMutation(...)`.

The mutation requires the same stable record reference and direct causation on
the lineage and outbox facts. This lets the queue message carry a safe outbox
identifier while the worker retrieves the durable work record by reference.

There is deliberately no in-memory implementation of this port. The existing
Core in-memory repository rejects a transaction handle because it cannot make
that promise. A fake that silently writes outside the transaction would be a
false proof of atomicity; the DynamoDB adapter must provide the real one.

## Boundaries

- Core supplies immutable, versioned outbox entries and safe lineage facts.
- This package owns generic coordination, but not business state transitions,
  entity schemas, tenant policy, retention policy, or product deletion rules.
- An adapter translates these ports to a selected database and queue provider.
- Target infrastructure supplies table/index resources, encryption, IAM,
  backup/retention configuration, queue resources, alarms, and cost controls.
