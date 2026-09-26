# AWS PostgreSQL Persistence Adapter

This package translates provider-neutral persistence contracts into PostgreSQL
driver calls. It is selected only by AWS target composition; applications use
`@kanbien/core` and `@kanbien/platform-persistence` rather than importing the
`pg` driver or this adapter's private row layout.

It is a deliberately small relational reference. It supplies transaction,
outbox, processing-lease, change-lineage, migration, safe-error, and safe
telemetry mechanics. It does not define a product entity, database schema,
repository query, tenant policy, generic ORM, or arbitrary SQL interface.

| File | Responsibility |
| --- | --- |
| `src/config.ts` | Validates injected, non-secret connection settings: a reviewed host/database/schema, bounded timeouts/pool, explicit secret reference, and strict TLS policy. |
| `src/connection.ts` | Creates the `pg` connection pool only from validated settings plus separately supplied credentials and CA material. |
| `src/errors.ts` | Reduces driver outcomes to finite, provider-neutral failure categories; raw PostgreSQL errors never leave the adapter. |
| `src/transactions.ts` | Owns `BEGIN`/`COMMIT`/`ROLLBACK` and the provider-local atomic seam for one product DML statement plus platform lineage/outbox facts. |
| `src/migrations.ts` | Validates and applies an ordered checksum manifest, recording only identifier, checksum, tool version, timestamp, and outcome. |
| `src/outbox.ts` | Stores delivery obligations and provides atomic lease/fence-protected relay operations. |
| `src/processing.ts` | Stores worker-processing claims, retry releases, completion, and stale-fence rejection. |
| `src/lineage.ts` | Appends and queries the bounded record-change facts defined by Core. |
| `src/records.ts` | Keeps PostgreSQL column layout, safe conversion, parameterised statement creation, and reviewed relation identifiers private to this package. |
| `src/telemetry.ts` | Emits only operation/outcome/duration/error-class/bounded-pool observations; it never emits SQL, values, rows, credentials, endpoints, or raw errors. |
| `src/index.ts` | Deliberate public composition exports only. |

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

## Safety boundary

- Configuration contains a secret *reference*, never the secret value. The
  caller supplies runtime credentials and CA material separately.
- Connections use certificate verification and a server name. Plaintext TLS,
  unbounded pool sizes, unbounded timeouts, blank configuration, and unsafe
  SQL identifiers are rejected before connection.
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

## Tests and evidence

The package-level tests are deterministic and use a recording pool, not AWS or
a shared database. They prove configuration redaction, parameterised values,
safe error mapping, commit/rollback behaviour, safe telemetry, atomic
participant/fact composition, migration checksums, and source import
boundaries.

`npm run platform:adapter:aws:persistence:postgresql:integration` adds the
Stage 3 disposable-engine proof. It starts an ephemeral, loopback-only Docker
PostgreSQL container with a generated, unrecorded password and a temporary
data directory, then always removes the exact generated container. It proves
migration checksum immutability, atomic smoke state/lineage/outbox writes,
rollback, optimistic concurrency, synthetic tenant predicates, outbox relay
compatibility, and lease/fence rejection on a real engine. The local fixture
deliberately uses no AWS credentials, shared database, real record, or
production TLS bypass: it injects a test-only non-TLS `pg` pool solely because
the disposable loopback fixture has no trusted certificate. The public
production pool constructor continues to require `verify-full` TLS; Stage 5
proves that live boundary.
