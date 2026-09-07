# Core Queue Source Map

This directory currently has one implementation file because its message
envelope, delivery metadata, queue port, and in-memory helper are a tightly
coupled stable Core contract. Consumers import from `@kanbien/core/queues`;
they do not import this file by path.

| File | Owns | Boundary |
| --- | --- | --- |
| `index.ts` | Versioned queue-message envelope, delivery/retry/dead-letter facts, queue port, and in-memory/no-op test helpers. | It may name portable Core identifiers, JSON payloads, and an optional trace parent, but it cannot select a broker, worker process, provider SDK, or product job. |

`QueueMessage.traceParent` carries only the producer span context needed for a
later worker span to be its child. It is copied and validated with the message
but is not exposed as a general trace attribute, metric label, or business
handler dependency. `causationId` remains separate: it names the immediate
event or message that caused this queue message. The worker runtime establishes
the input message itself as the direct cause of the job it runs.

Future broker adapters must validate this versioned envelope when deserialising
untrusted provider data and preserve correlation, causation, idempotency, and
trace-parent facts through accepted retries and dead-letter handling.
