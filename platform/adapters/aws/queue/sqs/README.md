# AWS SQS Queue Adapter

This package translates the provider-neutral Core queue ports to and from AWS
SQS Standard. A producer serializes the complete Core message envelope before
submitting the SDK call. A worker validates that envelope after SQS delivers it, then
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
| `src/observations.ts` | Supplies Core-owned, bounded command, guard and informational receive-reduction evidence. |
| `src/index.ts` | Deliberate public exports only. |
| `src/configuration/` | Source-independent sender/receiver requirements, strict checking, assembly and safe reports; see its [guide](src/configuration/README.md). |
| `tests/` | Prove sender/receiver envelope preservation, provider-ID separation, command shapes, malformed-envelope containment, and package boundaries. |

## What happens when an outbox item is sent

The platform relay passes a Core `QueueMessage` to `Queue.send`. The sender
places its stable message ID, type, version, timing, and permitted causal
context in the SQS body. Once SQS accepts that body, the relay may record that
the outbox entry was published. If the call fails, the adapter returns a safe
`QUEUE_SEND_FAILED` result; the relay leaves the durable entry available for a
later retry.

A failed call does not prove nonacceptance. The retained legacy error message is
not stronger evidence than the observed boundary: send/receive/settlement effects
remain unknown on invocation failure. Release only requests visibility zero; it
does not attest DLQ movement, message deletion or redrive completion.

On the other side, SQS supplies a receipt handle that is valid only for the
current delivery. The worker adapter reads the message body and reconstructs
the Core envelope from it. It never substitutes SQS's `MessageId` for the
envelope ID. This keeps an outbox entry identifiable across delivery retries.

## Deliberate boundaries

For new configuration work, use the [configuration module](src/configuration/README.md)
with Platform loading or the guarded `FromConfiguration` factories. The existing
`createAwsSdkPlatformSqsWorkerQueueFromEnv` remains a compatibility path for its
current callers: it does not silently acquire strict parsing. This slice does
not migrate the retiring target. Local catalogue JSON is public through
`@kanbien/platform-adapter-aws-queue-sqs/configuration/diagnostics.v1.json`.

The adapter never exposes raw SQS response bodies or provider exceptions in
its errors. It does not create queues, choose redrive limits, retention,
encryption, IAM, FIFO ordering, or implement business idempotency. Those are
owned respectively by infrastructure, target composition, and persistence
policy. This package only translates the declared Core queue contract to the
AWS SDK.

Constructor options optionally accept Core's `diagnosticDefinitions` and
`onDiagnostic(record, context)`. The environment factory accepts those options as
argument two. The context identifies the actual operation/boundary for own and
all selected source records, including startup source records. Reporting remains
target-selected and profile-governed. Synchronous/rejected sinks and unavailable
getters cannot change workload results. Source primary/eight are independent of
own evidence; no raw cause reaches the observer. Repeated reads, Number coercion,
first-message processing, optional omission, guard throws and public errors stay
unchanged. Malformed response/count fallback findings are coalesced (at most16,
explicit truncation) and informational; ordinary empty receives are quiet.

Only actual SDK invocation failures inspect an own data `name` descriptor.
Modeled names are recognized only for the applicable send/receive/delete/visibility
operation; unsupported names, other-operation names and unavailable accessors stay
unknown. This never reads error text, HTTP status, transport codes or nested causes.
RequestThrottled is not inferred from HTTP403; InvalidSecurity is not an IAM or TLS
chain diagnosis; key rejection is not queue absence. Recovery and effects remain
manual/unknown, with no new retry. The optional detail belongs to the new B06 draft
definition; existing records without it remain valid.
