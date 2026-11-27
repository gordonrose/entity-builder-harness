# Platform Persistence

`@kanbien/platform-persistence` implements provider-neutral coordination for
durable delivery. It uses the stable Core outbox and lineage facts, then owns
the mutable mechanics that make retries safe: attempts, leases, fences, and
terminal processing completion.

This package does not select a database, queue, scheduler, cloud region, or
application entity. Provider implementations live separately in the
[PostgreSQL](../adapters/aws/persistence/postgresql/README.md) and
[DynamoDB](../adapters/aws/persistence/dynamodb/README.md) adapters.

## Source map

The [leasing module](src/leasing/README.md) owns the shared positive-whole-number
duration check used by relay construction, durable worker configuration and
individual lease creation. Targets still choose durations; these checks do not
grant leases or prove database availability.

The [maintenance instruction module](src/maintenance/README.md) owns supported
migration/restore job choices and reference-proof requirements. It checks those
instructions without opening a database. Targets bind environment names and
run the existing jobs using the returned checked instructions. Its local JSON
catalogue is exported as `@kanbien/platform-persistence/maintenance/diagnostics.v1.json`;
the existing combined catalogue remains available too.

| File | Owns | Does not own |
| --- | --- | --- |
| `errors.ts` | Stable, provider-neutral platform-persistence failure meanings. | Provider exception objects or application error policy. |
| `diagnostics.ts` | Versioned finite validation, stored-record reduction, native operation and resource-boundary evidence; safe source selection and optional observation. | Native classifiers, SQL, submitted values, replay authority or provider selection. |
| `observability/port.ts` | Closed no-payload transition vocabulary and best-effort observer port. | Logging, metric, trace-provider selection, profile policy, or cloud delivery. |
| `observability/integration.ts` | Persistence-owned translation from a closed transition into generic observability helpers. | Provider selection, telemetry delivery, or cloud configuration. |
| `observability/index.ts` | Deliberate transition-observability exports. | A second package or target boundary. |
| `types.ts` | Mutable outbox/processing record shapes, attempts, leases, fences, and safe constructors. | A database representation or target configuration. |
| `scheduling.ts` | One-off reminder creation, due-row selection, and the one-time handoff from a due reminder to an outbox entry; plus a deterministic in-memory proof store. | Recurrence, timezone rules, choosing a job's message type, a running scheduler, queue sends, or job execution. |
| `schedule-delivery.ts` | A bounded due pass with a stop check between reminders; unavailable jobs are retained as blocked records. | Queue sending, timers or interrupting an in-flight store call. |
| `schedule-jobs.ts` | Maps selected public job registrations to declared message types and stable reminder-based outbox identities. | A global list of every app's jobs or automatic app mounting. |
| `schedule-reference.ts` | Checks a received envelope against the scoped outbox and due reminder. | Choosing an application entity from queue data or applying its business rules. |
| `schedule-dispatch.ts` | One due pass followed by a bounded number of existing relay attempts, including older waiting work. | Interrupting in-flight calls, automatic invocation, worker execution, AWS selection or calendar rules. |
| `outbox.ts` | Pending-entry storage port, claim/lease/publish transitions, and deterministic in-memory proof store. | Queue sends; a relay calls a queue adapter after it claims an entry. |
| `processing.ts` | Worker claim, release-for-retry, and completion transitions; duplicate recognition; and stale-fence rejection. | A job handler's business effect or queue acknowledgement. |
| `processing-retry.ts` | Checks a persisted retry deadline and rejects malformed stored timing. | Deciding retry policy or starting a timer. |
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
not a substitute for real database or AWS evidence.

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
queue boundaries. Concrete sending and storage remain in the existing
[SQS](../adapters/aws/queue/sqs/README.md) and persistence adapters.

Relay boundary records distinguish raw throws from returned failures and retain
the last observed send/publication milestone. A failed send leaves acceptance
unknown; a failed marker after send success retains both facts. Missing leases
reuse the local contract predicate, and envelope rejection retains both original
Core type/version results. Optional direct queue-message diagnostic options and
relay selected definitions preserve source primary/eight without replacing raw
throws. Raw relay evidence uses the existing observer's `relay` operation;
ordinary idle/contention remains free of failure diagnostics.

## One bounded scheduling pass

[createPlatformScheduleDispatcher](src/schedule-dispatch.ts) joins two existing
operations. First, due delivery moves ready reminders into the **outbox**: the
stored waiting list of work promised for delivery. Then the relay sends waiting
work to the queue. It runs the relay even when no new reminders became due,
so a previous failed send can be retried after its claim expires.

The public exports are:

| Export | Purpose |
| --- | --- |
| `createPlatformScheduleDispatcher` | Construct the caller-driven operation from existing due delivery and relay instances. |
| `PlatformScheduleDispatcher` | The object exposing asynchronous `runOnce`. |
| `PlatformScheduleDispatchOptions` | Select those two dependencies, a `maximumRelayAttempts` integer from 1 through 100, and optional diagnostic reporting. The checked attempt limit is captured once. |
| `PlatformScheduleDispatchInvocation` | Optional synchronous `shouldContinue` checked before due selection, each reminder and each relay call. `shouldContinueDelivery` can stop the due phase earlier to reserve time for relay work. |
| `PlatformScheduleDispatchRunResult` | Due-pass counts (or null if never started), relay-attempt and published counts, and the reason this call stopped. |

For example, with already configured `delivery` and `relay` instances:

```ts
const dispatcher = createPlatformScheduleDispatcher({
  delivery,
  relay,
  maximumRelayAttempts: 10,
});
const result = await dispatcher.runOnce();
```

Suppose one reminder is due. Its handover succeeds but queue sending fails.
The result has one newly created delivery, one relay attempt, zero published,
and `stopReason: "queue-send-failed"`. The existing relay leaves that outbox
entry unpublished. After its lease expires, a later call can report zero new
due reminders yet publish that same entry. The
[connected runtime test](tests/integration/schedule-dispatch-runtime.test.ts)
proves this using controlled stores and the actual due-delivery and relay code;
it does not prove real database transactions or AWS delivery.

`stopReason` distinguishes `requested-stop`, `attempt-limit`, `idle`,
`contended`, `queue-send-failed` and `publish-marker-failed`. Only a
`published` relay outcome increases the published count. A successful Result
therefore does **not** mean all waiting work was sent. Idle means this relay
call observed no eligible work, not that the whole database is empty.

A returned dependency error or thrown value is preserved unchanged. Due-pass
failure stops before relay; existing backlog then waits for a later successful
pass. Prior writes are not undone, and failure Results do not include partial
counters. Source diagnostics remain available alongside an optional independent
dispatcher boundary record. The exported
`persistenceScheduleDispatchConfigurationDiagnostic` and
`persistenceScheduleDispatchBoundaryDiagnostic`, their `...Record` builders
and `PersistenceScheduleDispatchConfigurationDetail` /
`PersistenceScheduleDispatchBoundaryDetail` types define these safe, closed
records. They contain logical conditions and observed call boundaries, not
submitted values, job IDs or raw error text.

There is **no automatic timer in this package**. The caller chooses when to
invoke `runOnce`. `createPlatformScheduleDelivery` accepts `maximumSchedules`
(1–100, default 100) and checks the stop callback between reminders. Stopping
cannot interrupt a database or queue call already in progress. Target composition
must still provide dependency timeouts and a function-time budget.

### From a selected job to a checked delivery

`createPlatformScheduleJobOutboxFactory` takes the registrations actually mounted
in this runtime, a Core delivery-policy reference and a clock. Its
`PlatformScheduleJobOutboxOptions` describes those inputs. A job's declared
message type can differ from its name; the factory preserves that type and
reuses the reminder UUID as the stable outbox ID. Repeated construction cannot
invent a second work identity. An unavailable job returns `null`, causing the
due pass to block the reminder instead of continually selecting it.

`PlatformSchedule.subject` is an optional Core record reference: a kind and ID
chosen by the job owner, not arbitrary arguments. The outbox points to the
reminder; the reminder can point to an entity. A cleanup job must reject old
subjectless reminders rather than treating them as permission to sweep all rows.

```text
selected app job → reminder → outbox → queue {outboxEntryId}
                                ↑          │
                     checked durable reads ← loadPlatformScheduleDelivery
```

`loadPlatformScheduleDelivery(message, options)` returns a Result containing the
due reminder. `PlatformScheduleDeliveryReferenceOptions` supplies scoped
`outbox`/`schedules` readers, the expected job/message type, one `asOf` timestamp
and optional diagnostics. It checks identity, version, tenant, stored linkage
and due time. Missing, early or mismatched references return
`PLATFORM_PERSISTENCE_QUEUE_MAPPING_INVALID`; store throws remain unchanged.
The job must still check its own subject, lifecycle and retention rules.

`listDue` is normally read-only and fails closed on invalid data. The due runner
explicitly passes `blockInvalid: true`. PostgreSQL locks at most that page,
preserves invalid rows in `blocked-invalid-row`, commits their isolation and
returns valid rows. Later passes can reach later work. `resumeBlocked` first
revalidates a repaired row; an unrepaired row stays blocked. Unknown valid jobs
use `blocked-job-unavailable`. These controls do not repair data, cancel already
queued work or make a failed database call successful.

The exported scheduling diagnostic definitions, `...Record` builders and
`PersistenceSchedule...Detail` types cover configuration, due boundaries, job
mapping, subjects, control rejection, stored control rows, delivery references
and confirmed blocking. They contain finite conditions, not IDs or payloads.
Historical definition versions remain. The [bounded-pass tests](tests/integration/schedule-delivery-bounds-runtime.test.ts)
and [reference tests](tests/integration/schedule-reference-runtime.test.ts) exercise
shared code; real-engine and AWS proof remain separate obligations.

## Transition observability

The relay and optional durable worker emit closed transition facts through an
optional `PlatformPersistenceObserver`. The persistence package owns only the
fact that a named transition happened—for example `outbox.published`,
`processing.retry_released`, or `processing.duplicate_terminal_failure`. It
does not send an outbox ID, payload, record subject, tenant, fence, attempt,
queue receipt, provider response, or a raw error message as telemetry data.

The `observability/` folder owns the complementary profile-governed integration.
It uses generic `platform/observability` helpers to project
capability/action/execution-context/outcome and a bounded error class into
fixed log and trace names and fixed metric series. A Core correlation reference
may link logs, while an existing trace parent may link spans; neither becomes a
metric label or general trace attribute. Until an owning app registers a
profile and target composition approves its metric catalogue entries, these
local observer hooks are not live target evidence.

Local mutation, lease and in-memory state rejections carry finite diagnostic
records while retaining their existing errors, parameters and successful
duplicate/contention outcomes. A failed lease sequence retains both independently
failed fence and attempt observations. No new input or date validation is added.

Adapters can observe local predicates, transaction/resource boundaries and
stored-row reductions using the exported builders. Stored-row findings use a
bounded list (at most sixteen safe field/condition observations) with explicit
truncation; adapters coalesce findings at the existing operation boundary.
Missing data and malformed returned data remain distinct, and a reconciliation
read establishes observed state without proving ownership of earlier writes.

`PlatformPersistenceDiagnosticOptions` selects Core, Persistence and explicitly
supplied definitions. Its optional `onDiagnostic` receives an independent local
record and all validated source evidence (primary plus eight companions) without
replacing the thrown value or waiting for the observer. The transition observer
also accepts an independent `diagnosticRecord` and an optional injected reporter;
selection and operational-log profile permissions apply to both default and
injected delivery. Historical native v1/v2 schemas and emission remain unchanged;
the additive v3 constructor is restricted to generic create/read/delete and the
actual primary/reconciliation boundary.
An informational reconciliation record names the observed read result without attributing a prior write to this invocation.

Command v4 observations retain the actual call boundary and finite native category.
Recognized invocation condition rejection uses an informational command-condition
record without classifying the workflow as failed. Stored-attribute v1 findings
are bounded with explicit truncation, and state
reconciliation v2 records only the read result. Atomic writers accept optional
per-invocation diagnostic options: omission retains defaults, while a supplied
empty object silences the default observer. Resolution touches only diagnostic
properties and preserves observer receivers. Background stores can use the
existing persistence observer's optional `onDiagnostic` method, which honors
the same selected catalogs and operational-log profile permission.

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

Processing release can now persist `retryAt`. A claim before that timestamp
returns `retry-not-due` without advancing the durable attempt. A restarted
worker cannot forget the delay. `validatePlatformProcessingRetryAt` checks that
the deadline is valid and not before release; `decodePlatformProcessingRetryAt`
rejects malformed stored timing instead of treating it as immediate retry.
Omission preserves existing immediate-release callers. The worker's checked
policy chooses the delay; these helpers do not choose it or start a timer.

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
false proof of atomicity; the selected persistence adapter must provide the real one.

## Boundaries

- Core supplies immutable, versioned outbox entries and safe lineage facts.
- This package owns generic coordination, but not business state transitions,
  entity schemas, tenant policy, retention policy, or product deletion rules.
- An adapter translates these ports to a selected database and queue provider.
- Target infrastructure supplies table/index resources, encryption, IAM,
  backup/retention configuration, queue resources, alarms, and cost controls.
