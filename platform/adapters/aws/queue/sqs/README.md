# AWS SQS Worker Delivery Adapter

This package translates an AWS SQS delivery into a validated Core
`QueueMessage` and translates explicit worker outcomes into SQS acknowledge or
release calls. It polls at most one message at a time; worker concurrency and
job behaviour remain a target composition decision.

| File | Responsibility |
| --- | --- |
| `src/index.ts` | SQS receive, bounded envelope parsing, acknowledgement/release, and target environment validation. |
| `tests/` | Prove valid delivery, empty polling, malformed-envelope containment, acknowledgement/release command shape, and provider-boundary imports. |

The adapter never exposes raw SQS response bodies to logs or errors. It does
not create SQS resources, choose redrive limits, or implement a business
idempotency store. Infrastructure owns queues, DLQs, retention, encryption,
and IAM; the target worker composition owns the poll loop and maps a generic
worker outcome to acknowledgement or release.
