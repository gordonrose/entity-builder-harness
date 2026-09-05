# Platform Runtime

`platform/runtime` turns public app contributions into one validated, in-memory
catalogue for a single server or worker process. It also provides the composed
request/job contexts and ordered lifecycle mechanics used by host shells.

It is not an HTTP server, queue consumer, cloud adapter, or deployment system.
Those targets compose this package after their own target-specific concerns are
selected.

## Boundary

Consumers import `@kanbien/platform-runtime`. The source may depend on public
`@kanbien/core` and `@kanbien/platform-contracts` exports, but never app
internals, provider SDKs, or infrastructure artifacts. Apps contribute through
the public `PlatformApp` mount contract; the runtime does not import their
private source files.

## Responsibility map

| Path | Responsibility | Verification |
| --- | --- | --- |
| `src/errors.ts` | Stable runtime and mount failure vocabulary. | `npm run platform:runtime:check` |
| `src/registry.ts` | Per-process registry, app-scoped registration view, validation, and app-mount orchestration. | `npm run platform:runtime:check` |
| `src/contexts.ts` | Provider-neutral request/job context and shared runtime-dependency factories. | `npm run platform:runtime:check` |
| `src/lifecycle.ts` | Ordered startup, readiness, graceful shutdown, resource, and telemetry coordination. | `npm run platform:runtime:check` |
| `src/index.ts` | Deliberate public package exports only. | `npm run platform:runtime:check` |
| `tests/platform-runtime-types.test.ts` | Public TypeScript contract proof. | `npm run platform:runtime:check` |
| `tests/platform-runtime-runtime.test.ts` | Runtime registration, namespace, duplicate, context, and lifecycle proof. | `npm run platform:runtime:check` |
| `tests/platform-runtime-boundaries.test.mjs` | Import-boundary proof. | `npm run platform:runtime:check` |

The [source map](src/README.md) explains why those runtime responsibilities
are separate. External callers continue to use the single public package
import; topic files are not public subpath APIs.

## App-scoped registrations

`mountPlatformRuntimeApps` validates each app ID, obtains a scoped registry with
`registry.forApp(appId)`, and passes that view to the app's `mount` function.
The view accepts only permission, route, job, and health names beginning with
`<app-id>.`; otherwise it records
`PLATFORM_CONTRACT_NAMESPACE_MISMATCH`. The complete registry still rejects
global duplicates, such as two valid apps claiming the same HTTP method and
path. Configuration schemas remain app-supplied schema declarations and are
not name registrations in the current contract.

The registry is built anew during process startup. A deployment system decides
how to retain old capacity, cut traffic over, and roll back; this package only
decides whether its own process has a valid catalogue before it becomes ready.
