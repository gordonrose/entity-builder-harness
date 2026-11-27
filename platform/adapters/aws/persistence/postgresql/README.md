# AWS PostgreSQL Persistence Adapter

This package translates provider-neutral persistence contracts into PostgreSQL
driver calls. It is selected only by AWS target composition; applications use
`@kanbien/core` and `@kanbien/platform-persistence` rather than importing the
`pg` driver or this adapter's private row layout.

It is a deliberately small relational reference. It supplies transaction,
outbox, processing-lease, change-lineage, one-off schedule storage, migration,
safe-error, and safe telemetry mechanics. It does not define a product entity,
schedule recurrence, timezone policy, a due-job runner, tenant policy, generic
ORM, or arbitrary SQL interface.

| File | Responsibility |
| --- | --- |
| [src/configuration/](src/configuration/README.md) | Owns reusable requirements, direct validation and assembly of checked values plus target-selected policy. |
| [src/metadata.ts](src/metadata.ts) | Owns the existing adapter identity exported by the root index. |
| `src/connection.ts` | Creates the `pg` connection pool only from validated settings plus separately supplied credentials and CA material. |
| `src/errors.ts` | Reduces driver outcomes to finite, provider-neutral failure categories; raw PostgreSQL errors never leave the adapter. |
| `src/transactions.ts` | Owns `BEGIN`/`COMMIT`/`ROLLBACK` and the provider-local atomic seam for one product DML statement plus platform lineage/outbox facts. |
| `src/migrations.ts` | Validates and applies an ordered checksum manifest, or checks an existing migration-history prefix without applying changes. |
| `src/outbox.ts` | Stores delivery obligations and provides atomic lease/fence-protected relay operations. |
| `src/processing.ts` | Stores worker-processing claims, retry releases with their earliest next attempt, completion, and stale-fence rejection. |
| `src/lineage.ts` | Appends and queries the bounded record-change facts defined by Core. |
| `src/scheduling.ts` | Stores and reads one validated future job instruction in PostgreSQL; it does not decide when to run it. |
| `src/records.ts` | Keeps PostgreSQL column layout, safe conversion, parameterised statement creation, and reviewed relation identifiers private to this package. |
| `src/telemetry.ts` | Emits only operation/outcome/duration/error-class/bounded-pool observations; it never emits SQL, values, rows, credentials, endpoints, or raw errors. |
| `src/index.ts` | Deliberate public composition exports only. |

## Configuration ownership

The [configuration guide](src/configuration/README.md) explains each new file and
export. The target selects this implementation and supplies concrete source
bindings. Platform config coordinates reading/checking; Core supplies reusable
checks. Neither the target nor a build script owns a copy of PostgreSQL rules.
Selection does not establish another database implementation is interchangeable.

## Inspecting migration progress

Before adding scheduler tables, a target may need to confirm which reviewed
migrations have already run. `readPostgreSqlMigrationPrefix`, implemented in
[src/migrations.ts](src/migrations.ts) and exported through the package index,
accepts a checked-out client and a manifest with an explicit
`continuation.minimumAppliedMigrations`. A **prefix** means the first entries of
that ordered manifest, with every recorded ID and checksum matching. For example,
if two of seven migrations are recorded and the accepted minimum is two, the
function returns `{ ok: true, value: 2 }`. Missing history, too few entries,
an unknown or missing-middle entry, a changed checksum, or a failed read returns
a failed `Result` with the existing safe persistence error; it does not create
tables or apply the missing migrations.

The [shared target observer](../../../../../infra/04.deploy/03.product/entrypoints/shared/persistence/scheduling-administration.ts)
owns the read-only transaction, takes the migration lock without waiting, checks
database/schema/history ownership, and turns the returned count into a bounded
receipt. It does not require scheduler tables to exist. The adapter function
does not open that transaction or take the lock itself. A successful observation
describes that snapshot only: the migration writer still checks the same prefix
again under its own locks before applying changes. The existing
[contract tests](tests/contract/postgresql-persistence-adapter-runtime.test.ts)
and [disposable-engine fixture](tests/integration/postgresql-persistence-adapter-integration.test.ts)
cover these separate read and write paths; they are not AWS deployment proof.

## How the atomic seam is used

A product repository owns its own table and its reviewed, static DML. Target
composition gives that repository the `Transaction` received from
`PlatformPersistenceAtomicWriter`. It stages one parameterised DML statement
through `stagePostgreSqlTransactionStatement`, then stages the matching
provider-neutral mutation through `scope.stage`.

The adapter commits three kinds of fact together:

```text
product state write + record-change lineage + durable outbox obligation
```

If any participant fails, PostgreSQL rolls all of them back. `afterCommit`
callbacks are intentionally forbidden: reliable later work is represented by
the committed outbox, not a process-local callback that could be lost.

The statement seam admits one `INSERT`, `UPDATE`, or `DELETE` statement only.
It rejects DDL, transaction-control commands, and multiple statements. Values
must be bind parameters; table/column/order identifiers must come from
reviewed source or a constrained generated manifest, never a request.

## One-off schedules

`createPostgreSqlPlatformScheduleStore` is the durable version of the small
provider-neutral schedule-store contract in `@kanbien/platform-persistence`.
The caller gives it a schedule that Core has already made: an ID, a registered
job name, one exact due time, and the initial `waiting` state. The adapter
inserts those values using bind parameters, then checks the row returned by
PostgreSQL before handing it back. A later lookup makes the same checks.

The target chooses the schema and immutable migration IDs.
`postgreSqlPlatformScheduleMigration` supplies the first waiting-table shape;
`postgreSqlPlatformScheduleHandoffMigration` is the later, separate change
that adds the outbox link and the state/index needed for due selection. It
does not rewrite an earlier migration checksum.

Later additive migrations keep that history intact:

- `postgreSqlPlatformScheduleSubjectMigration` adds the optional record reference
  identifying exactly which application record a reminder concerns.
- `postgreSqlPlatformProcessingRetryMigration` adds `retry_at`, so restarting a
  worker does not forget when a failed job may next be attempted.
- `postgreSqlPlatformScheduleControlMigration` adds the blocked states used to
  keep unavailable jobs or invalid stored reminders out of the normal due scan.

`listDue` reads only waiting rows whose due time has arrived. `handoverDue`
opens one PostgreSQL transaction, locks one schedule row, inserts the supplied
outbox entry, and marks that schedule `delivery-created` with the outbox ID.
If it was already handed over, is blocked, or is not yet due, it changes nothing. For Entity
Smoke, target composition selects the existing `entity_smoke` schema and its
next migration IDs. This still does not create a schedule on server startup,
run due selection on a timer, choose the job's message type, send a queue
message, or run the cleanup job.

The ordinary `listDue` call remains read-only and rejects an invalid stored row.
The dispatcher explicitly requests `blockInvalid: true`: in one transaction,
the adapter locks a bounded page, checks its rows, and moves invalid rows into
`blocked-invalid-row` with one bulk update. It preserves their original fields
for inspection and returns only valid reminders. Blocking is reported only
after a successful commit. A failed update or uncertain commit is not reported
as successful isolation. This prevents an invalid oldest reminder from stopping
healthy work indefinitely without silently dropping it.

`blockDue` similarly holds a reminder whose job is unavailable. After an
operator repairs the record or restores the job, `resumeBlocked` checks the
stored record under a lock before returning it to `waiting`. It never repairs
business data or retries a failed repair automatically.

## Safety boundary

- Configuration contains a secret *reference*, never the secret value. The
  caller supplies runtime credentials and CA material separately.
- Connections use certificate verification and a server name. Plaintext TLS,
  unbounded pool sizes, unbounded timeouts, blank configuration, and unsafe
  SQL identifiers are rejected before connection.
- The driver query timeout is the checked statement timeout plus one second.
  This bounds a stalled client read as well as the server's statement execution;
  it does not establish a hard end-to-end function completion guarantee.
- SQL values use `$1`, `$2`, and later bind parameters. The adapter validates
  its own schema/table identifiers and never interpolates user/request values.
- The runtime role must be DML-only. A separate migration identity performs
  reviewed DDL through an immutable migration manifest; migrations never run
  automatically on application startup.
- Fences are stored with leases. A stale relay or worker cannot publish,
  complete, or release work after a later claimant has acquired a higher fence.
- Read methods whose provider failure cannot be represented in their legacy
  return type throw only a stable platform error. They never quietly report an
  unavailable database as an empty result.

## Failure diagnostics

`postgreSqlFailureDiagnostic(error)` returns the existing Core diagnostic
shape with a closed classification, `recognized`/`unrecognized`/`absent` code
status, observed phase and elapsed milliseconds. Unobserved timing is `null`
and phase is `unknown`. The low-level pool seam preserves driver error identity
for adapter SQL semantics; consumers must emit only this descriptor or the
sanitized platform operation error, never the raw driver object.

Phases identify the actual call boundary: `pool_connect` includes acquisition
and any driver connection work; `pool_query` includes acquisition plus query;
`query` is a checked-out client's query; `authentication_value` is the token
callback. These observations do not prove internal TCP/TLS/authentication
stages. A separate probe has its own connection. Unknown errors remain unknown
and do not grant retries. PostgreSQL `57014` reports `query_canceled`, since its
code alone cannot distinguish an explicit cancellation from a statement timeout.
The older provider failure class retains its broad timeout bucket for compatibility.

Transaction/store options and the optional final connection-constructor argument
accept `PlatformPersistenceDiagnosticOptions`. Its optional observer receives
validated records, never raw driver errors. Core/Persistence definitions and
explicitly supplied companion definitions select upstream evidence. A new
boundary record is emitted independently of an upstream primary plus eight
companions; observer failures cannot change database work or cause replay.

Independent records describe acquisition, transaction stages, rollback/release,
idle-pool events, pool end, local migration/statement/state guards and bounded
stored-row reductions. Native query/authentication phases keep their original
meaning. Row findings are coalesced into at most sixteen field/reason groups
with counts and explicit truncation. Existing malformed-row null/filter/duplicate
reductions and successful reconciliation dispositions remain unchanged. A later
SELECT describes the state observed then; it does not establish why an earlier
UPDATE missed or who performed a write. Write effects remain unknown where the
adapter cannot prove them, including failed commit/rollback calls. Migration
preflight rejection precedes SQL; later checksum/schema observations do not
claim that earlier statements never ran.

Arbitrary getter, date-conversion or decoder throws are unknown decoding
boundaries; a thrown value alone does not prove corrupt stored data. The legacy
lease-expired fallback result also remains unchanged, but its observation only
states that reconciliation found a lease with the matching fence: that branch
does not compare expiry. Custom migration `every` return truthiness is preserved;
a false aggregate without a rejecting callback carries only a generic predicate
location. Positively generated TLS peer records are delivered independently of
a full source envelope, with identical already-retained peers emitted once.

## Tests and evidence

The package-level tests use a recording pool and disposable loopback protocol
and TLS fixtures through the real `pg` driver, without AWS or a shared database. They prove configuration redaction, parameterised values,
safe error mapping, commit/rollback behaviour, safe telemetry, atomic
participant/fact composition, migration checksums, and source import
boundaries.

`npm run platform:adapter:aws:persistence:postgresql:integration` adds the
Stage 3 disposable-engine proof. It first uses an ephemeral, loopback-only
Docker PostgreSQL container when its daemon is available. Otherwise it starts
an installed local PostgreSQL engine only in a newly generated temporary data
directory and private socket directory. Both routes use a generated,
unrecorded password and always remove their exact generated state. The local
route never uses a host database, host-wide socket path, AWS credentials,
shared database, real record, or production TLS bypass.

The proof covers migration checksum immutability, atomic smoke
state/lineage/outbox writes, rollback, optimistic concurrency, synthetic
tenant predicates, outbox relay compatibility, and lease/fence rejection on a
real engine. It also verifies rejected authentication, a missing database, and
query cancellation under a configured statement timeout. It injects a test-only non-TLS `pg` pool solely because the
disposable loopback fixture has no trusted certificate. The public production
pool constructor continues to require `verify-full` TLS; Stage 5 proves that
live boundary.

The expanded engine fixture also exercises targeted Entity Smoke cleanup,
atomic deletion/reminder writes, exact retention and restore boundaries,
concurrent schedule handover, blocked-row repair, stored retry timing, and the
baseline app's durable completion through reconstructed workers. These are
local-engine scenarios, not evidence of an automatic AWS trigger or deployed
Lambda image; those require separate live acceptance.
