# Persistence Observability Source Map

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
