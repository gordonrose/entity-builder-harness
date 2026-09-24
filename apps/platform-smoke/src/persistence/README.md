# Platform-Smoke Persistence Capability

This folder owns the harmless **work-item acceptance** meaning used by the
future persistence smoke proof. It is application code: it declares a work
item that becomes `accepted`, a first revision, and the two durable platform
facts that must accompany that change.

| File | Responsibility |
| --- | --- |
| `types.ts` | Work-item state, the create-once repository port, and typed acceptance input/output. |
| `acceptance.ts` | Builds the safe lineage + outbox facts and asks an injected atomic writer to coordinate all three writes. |
| `index.ts` | Deliberate public exports. |

## The transaction request

```text
platform-smoke capability
  ├── create work item: accepted, revision 1
  ├── stage safe record change: created because of direct cause
  └── stage initial outbox obligation: work-item accepted
                         │
                         ▼
             injected PlatformPersistenceAtomicWriter
```

The app does not know a DynamoDB table name, a key format, an index, a
condition expression, an AWS SDK type, or an IAM role. It receives a
transaction-aware repository and atomic writer from composition. The selected
implementation must honour the promise that the work item, lineage, and
outbox either commit together or do not appear at all.

`PlatformSmokeWorkItemRepository.create` is intentionally a **create-once**
operation. Reusing the same work-item identity must return a duplicate/conflict
result; it must not overwrite the first accepted record. That is the small,
explicit business rule that the eventual DynamoDB repository will enforce with
its own conditional transaction operation.

The identifiers derived here are stable logical identities, not telemetry
fields. Observability must continue using the registered profile’s allowlisted
facts and must not emit the work-item or outbox identifier as a metric label or
trace attribute.
