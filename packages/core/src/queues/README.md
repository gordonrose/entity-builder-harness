# Core Queue Source Map

Its message envelope, delivery metadata, queue port, and in-memory helper are a
tightly coupled stable Core contract. Consumers import from `@kanbien/core/queues`;
they do not import this file by path.

| File | Owns | Boundary |
| --- | --- | --- |
| `index.ts` | Versioned queue-message envelope, delivery/retry/dead-letter facts, queue port, and in-memory/no-op test helpers. | It may name portable Core identifiers, JSON payloads, and an optional trace parent, but it cannot select a broker, worker process, provider SDK, or product job. |
| `diagnostics.ts` | Closed validation, unknown boundary and informational receive-reduction meanings. | No broker names, receipts, message/payload values or replay authorization. |

`QueueMessage.traceParent` carries only the producer span context needed for a
later worker span to be its child. It is copied and validated with the message
but is not exposed as a general trace attribute, metric label, or business
handler dependency. `causationId` remains separate: it names the immediate
event or message that caused this queue message. The worker runtime establishes
the input message itself as the direct cause of the job it runs.

Future broker adapters must validate this versioned envelope when deserialising
untrusted provider data and preserve correlation, causation, idempotency, and
trace-parent facts through accepted retries and dead-letter handling.

Queue errors compatibly retain a selected primary and at most eight companions.
Optional `CoreQueueDiagnosticOptions` observes independently owned records without
consuming a source slot. Own records and selected source records are validated
before delivery; callback getters, throws and rejected promises cannot change work.
The optional second callback argument identifies the actual observed operation
and boundary for both own and source records; it is not guessed from source detail.
Boundary evidence does not establish send nonacceptance, unchanged visibility,
settlement completion or DLQ movement. Ordinary empty receives are quiet.

The new queue boundary draft optionally carries finite `native` observations.
It retains unknown source/manual recovery and the same effect; a modeled code
observation does not prove cause, acceptance, settlement or a safe retry.
