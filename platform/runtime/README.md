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
| `src/diagnostics.ts` | Closed runtime state/boundary meanings and isolated optional observation. | `npm run platform:runtime:check` |
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
The view accepts only permission, route, job, observability-profile, and health names beginning with
`<app-id>.`; otherwise it records
`PLATFORM_CONTRACT_NAMESPACE_MISMATCH`. The complete registry still rejects
global duplicates, such as two valid apps claiming the same HTTP method and
path or the same observability-profile name. It also verifies that every route
and job references a registered profile or carries a bounded, controlled
opt-out. Configuration schemas remain app-supplied schema declarations and
are not name registrations in the current contract.

The registry is built anew during process startup. A deployment system decides
how to retain old capacity, cut traffic over, and roll back; this package only
decides whether its own process has a valid catalogue before it becomes ready.

## Diagnostic observation

`platformRuntimeDiagnosticCatalog` (owner `platform-runtime`) exports version-one
`platform-runtime.state-rejected` and `platform-runtime.boundary-failed` definitions.
Lifecycle, mount, and context inputs accept optional `onDiagnostic` and
`diagnosticDefinitions`. No observer is installed globally. Definitions are selected
only after failure, using Core's data-only evidence selector; they are not an
additional app or dependency admission policy.

State rejections describe the known unchanged state. Boundary observations describe
the operation, phase, subject, boundary, and known effect, not a guessed cause.
Optional `ordinal` is the zero-based yield position within that phase, not an
assertion about the original collection's indexing. IDs, resource names, native
messages, paths, and supplied dependency values are absent from these records.

Mount/lifecycle observers receive their own boundary record followed by selected
upstream evidence. The returned error retains a selected upstream primary and all
eight possible companions unchanged in meaning; the runtime location is delivered
independently rather than becoming a ninth companion. Without a selected primary,
the runtime record is the primary. Mount observers additionally receive the current
validated registered catalog snapshot, so a host can select app definitions before
output. Context observers emit only the runtime location; synchronous throws retain
their exact identity and upstream evidence for the caller to handle once.

Observation failures (including rejecting asynchronous callbacks) are isolated and
never awaited. Success, callback receivers and getter/iteration order, first-failure
behavior, lifecycle transitions, and legacy returned-error versus raw-throw boundaries
remain unchanged. A completed step followed by timestamp or event-append failure is
not reported as an uninvoked step. Construction and snapshot/projection failures are
observed separately, including the shutdown snapshots that already escaped as raw
rejections. This adds evidence, not rollback, retry, cleanup, or readiness policy.
