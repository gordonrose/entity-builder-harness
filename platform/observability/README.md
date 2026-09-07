# Platform Observability

`platform/observability` provides provider-neutral helpers for safe runtime
diagnostics: bounded structured-log fields, log writing, metric recording, and
safe trace-span adaptation through the Core tracer port. It is the
platform-side operational-record boundary; it does not define durable audit
evidence or provider delivery.

It does not select a logging, metrics, tracing, SIEM, or cloud provider; create
spans; provision a sink; set retention; or decide app-specific audit and
security policy. Those responsibilities belong to approved adapters,
target-profile and infrastructure decisions, and apps/products respectively.

## Boundary

Consumers import `@kanbien/platform-observability`. Source may depend only on
public `@kanbien/core` contracts and local topic files. It must not import app
or infrastructure code, cloud SDKs, or provider implementation vocabulary. The
package boundary test protects that dependency direction.

## Responsibility map

| Path | Responsibility | Verification |
| --- | --- | --- |
| `src/normalization.ts` | Redacts, bounds, and converts unknown log and trace values into safe JSON-shaped fields. | `npm run platform:observability:check` |
| `src/logging.ts` | Adapts a Core logger so normal runtime writes pass through the normalisation boundary. | `npm run platform:observability:check` |
| `src/metrics.ts` | Records provider-neutral metric points and the current request, job, and health helper measurements. | `npm run platform:observability:check` |
| `src/tracing.ts` | Prepares bounded safe trace attributes and safely adapts Core `Tracer` spans. | `npm run platform:observability:check` |
| `src/index.ts` | Deliberate public package exports only. | `npm run platform:observability:check` |

The [source map](src/README.md) explains why the topics remain separate and
how their dependencies flow. The server and worker now create safe
provider-neutral spans; a worker may use the Core trace parent carried in its
queue message without exposing it to application handlers. The topic files are
internal organisation, not public subpath APIs. A tracing adapter is still
future work: no provider, exporter, external propagation format, sampling
policy, retention decision, or trace store is selected here.
