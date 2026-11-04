# Persistence Observability Source Map

Transition projection failures report an independent observation boundary and
selected source primary/eight through the same profile-governed reporter, then
preserve the original throw for the existing outer observer isolation. Earlier
signals may already exist: this means observation-incomplete, never rollback.

This folder owns the optional persistence-to-observability integration. It is
part of `@kanbien/platform-persistence`, so generic observability does not pull
persistence into an otherwise persistence-free server graph.

| File | Responsibility |
| --- | --- |
| `port.ts` | Closed transition facts and the best-effort observer port used by durable coordination. |
| `integration.ts` | Converts those facts into profile-projected generic logs, metrics, and traces. |
| `index.ts` | The deliberate public exports for the folder. |

The integration never exposes outbox IDs, payloads, record subjects, tenant
identifiers, queue receipts, fences, provider responses, or raw error messages.
Telemetry failure remains unable to change durable persistence behaviour.

The existing operational-log profile gate governs both default and injected
diagnostic reporters. Core and Persistence definitions are selected by default;
cross-cutting catalogs remain explicit. An observation's independent
`diagnosticRecord` is delivered separately from its error's selected primary
and eight companions, so a location record cannot displace source evidence.
Unselected, malformed and accessor-backed records are excluded before delivery.
The optional `onDiagnostic` method delivers selected store observations through
that same reporter/profile gate with runtime context, without fabricating a
transition, outcome or correlation reference.
Its optional second operation argument selects `relay` for raw relay evidence;
omission retains `store-observation`. Both observer callbacks isolate synchronous
throws and asynchronous rejection without awaiting or changing callback receivers.
