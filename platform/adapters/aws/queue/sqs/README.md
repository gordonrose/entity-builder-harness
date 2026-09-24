# AWS SQS Queue Adapter

This package translates the provider-neutral Core queue ports to and from AWS
SQS Standard. A producer serializes the complete Core message envelope before
SQS accepts it. A worker validates that envelope after SQS delivers it, then
acknowledges or releases the temporary delivery using its receipt handle.

The distinction is deliberate: SQS `MessageId` and `ReceiptHandle` describe a
provider delivery. The envelope `id` identifies the durable outbox work item.
The latter—not a provider-generated value—is what downstream idempotency and
causation logic must use.

| File | Responsibility |
| --- | --- |
| `src/metadata.ts` | Declares the adapter's provider, capability, implementation, and package identity. |
| `src/queue.ts` | Implements Core `Queue.send` with SQS Standard send semantics and bounded delay validation. |
| `src/messages.ts` | Encodes and decodes the durable Core envelope, including correlation, causation, trace, and idempotency context. |
| `src/worker.ts` | Receives one SQS delivery, exposes acknowledgement/release, and validates target environment configuration. |
| `src/errors.ts` | Provides safe adapter errors that do not expose raw provider response or message-body data. |
| `src/index.ts` | Deliberate public exports only. |
| `tests/` | Prove sender/receiver envelope preservation, provider-ID separation, command shapes, malformed-envelope containment, and package boundaries. |

## What happens when an outbox item is sent

The platform relay passes a Core `QueueMessage` to `Queue.send`. The sender
places its stable message ID, type, version, timing, and permitted causal
context in the SQS body. Once SQS accepts that body, the relay may record that
the outbox entry was published. If SQS rejects it, the adapter returns a safe
`QUEUE_SEND_FAILED` result; the relay leaves the durable entry available for a
later retry.

On the other side, SQS supplies a receipt handle that is valid only for the
current delivery. The worker adapter reads the message body and reconstructs
the Core envelope from it. It never substitutes SQS's `MessageId` for the
envelope ID. This keeps an outbox entry identifiable across delivery retries.

## Deliberate boundaries

The adapter never exposes raw SQS response bodies or provider exceptions in
its errors. It does not create queues, choose redrive limits, retention,
encryption, IAM, FIFO ordering, or implement business idempotency. Those are
owned respectively by infrastructure, target composition, and persistence
policy. This package only translates the declared Core queue contract to the
AWS SDK.
