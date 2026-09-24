# Core Persistence Source Map

`@kanbien/core/persistence` defines the portable vocabulary for saving and
retrieving state. It is a contract layer: it names the question a storage
provider must answer, but it does not choose a database, table, query language,
ORM, cloud SDK, or product schema.

Consumers import from `@kanbien/core/persistence` or the Core root barrel.
The files below improve discoverability; they are not separately supported
public import paths.

| File | Owns | Why it is separate |
| --- | --- | --- |
| `concurrency.ts` | `ConcurrencyToken` and its branded constructor. | Stale-write protection is a distinct contract from background-work fencing. |
| `errors.ts` | Stable persistence error codes and `persistenceError`. | Apps should handle portable meanings, not provider exception shapes. |
| `pagination.ts` | Page requests, optional totals, page construction, and validation. | List/cursor semantics are separate from saving one record. |
| `repository.ts` | The small `Repository` port, expected-version save option, and optional transaction handle. | Product repositories may add their own queries outside Core. |
| `transactions.ts` | Explicit transaction and post-commit contracts. | It establishes atomicity without selecting a transaction manager. |
| `lifecycle.ts` | Logical deletion, restoration-window, retention-reference, and purge-eligibility contracts. | It makes repairable deletion explicit without choosing a universal retention period or physically deleting data. |
| `in-memory.ts` | Deterministic in-memory repository and unit-of-work helpers. | These support tests and local composition; they are not a durable store. |
| `outbox.ts` | Versioned durable-delivery identity, subject reference, and routing facts. | It deliberately contains no raw message payload or mutable relay state. |
| `lineage.ts` | Safe record-revision/change envelopes and allowlisted field names. | It records references and changed field names, never full before/after records or free-form metadata. |
| `index.ts` | Deliberate public exports. | Existing imports remain compatible while the module stays scanable. |

### What belongs elsewhere

- A DynamoDB, SQL, ORM, or cloud implementation belongs in a platform adapter.
- Tables, indexes, encryption, backup, IAM, retention resources, and capacity
  settings belong in target infrastructure.
- Entity fields, migrations, tenant queries, deletion/restore meaning, and
  business state transitions belong to the owning app or product package.
- A worker lease and fence belong to a restartable background-processing
  boundary. They are not required for ordinary record updates, which use an
  expected concurrency token when stale writes must be rejected.
- Mutable relay/worker claim state, lease expiry, fencing, and terminal
  completion belong in `platform/persistence`. Core owns only the stable facts
  that a platform implementation or later provider adapter must share.
- A repository that is passed a `Transaction` must actually enlist in that
  transaction or reject the save. The in-memory repository rejects it because
  it cannot provide durable atomicity; silently ignoring it would be unsafe.
- A product that adopts `lifecycle.ts` must put the lifecycle state beside its
  own row, deliberately exclude deleted rows from normal reads, write a
  `RecordChange` for create/update/delete/restore, and select an authorised
  repository/retention/legal-hold path. The Core eligibility helper returns a
  decision only; it never performs a physical purge or turns provider TTL into
  a privacy promise.
