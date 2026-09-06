# Platform Runtime Source Map

This directory implements `@kanbien/platform-runtime`. Consumers import the
package root rather than individual source files. The
[package README](../README.md) owns the package boundary and verification
route.

`index.ts` is a deliberate public barrel. It preserves the supported runtime
API while allowing the implementation to be grouped by responsibility. A
source-level helper may be exported between local topic files without becoming
part of that public API.

| File | Owns | Why it remains separate |
| --- | --- | --- |
| `errors.ts` | Runtime failure codes, mount-failure shape, and internal failure constructors. | Registry mounting and lifecycle coordination can report safe, consistent failures without importing one another’s mechanics. |
| `registry.ts` | App registration catalogue, scoped app views, cross-registration validation, and app-mount orchestration. | Only this topic can see every app contribution and enforce relationships such as duplicate routes or namespace ownership. |
| `contexts.ts` | Shared dependency defaults plus request and job context construction. | Handlers receive a consistent bundle of runtime facts without the registry or lifecycle becoming a service locator. |
| `lifecycle.ts` | State machine, app hooks, resource startup/draining/closing, telemetry flushing, and ordered shutdown. | Process lifecycle has a different stateful sequencing concern from registration or individual request/job facts. |
| `index.ts` | Approved public exports only. | Consumers keep one stable import while implementation files remain navigable. |

## Detailed guide to the files

### `errors.ts` — a safe language for runtime failures

This file describes the failures the runtime itself can report: an app threw
during mounting, the complete registry was invalid, the lifecycle failed, or a
lifecycle action was attempted from an invalid state. It also distinguishes a
mount failure from a more general runtime failure.

It does not decide whether a route is malformed or a permission is unknown.
Those are platform-contract failures produced by contracts and collected by the
registry. Runtime errors explain what went wrong while composing or operating a
process; they do not replace the lower-level contract vocabulary.

### `registry.ts` — assembling one process’s app catalogue

This file is the meeting point for app declarations. At process startup, it
collects permissions, routes, jobs, health checks, and config schemas from each
mounted app. Because it sees the complete catalogue, it can reject duplicate
routes, jobs, and health names, a route that refers to an undeclared
permission, and an app attempting to register another app’s namespace.

`mountPlatformRuntimeApps` creates a fresh registry for one process and passes
each app a scoped `forApp(appId)` view. The app may describe its contributions,
but it cannot choose another app’s identity or start a server. This registry is
not a global live database: a new server or worker builds it during startup,
then deployment tooling decides whether that valid process receives traffic.

### `contexts.ts` — a consistent bundle of runtime facts

Request and job handlers need shared facts such as a correlation ID, tenant,
principal, logger, metrics, config source, feature-flag reader, clock, and
cancellation signal. This file constructs those context objects with safe,
deterministic defaults for absent optional dependencies.

It is intentionally not a container of every application service. A context
can tell a handler who is acting and when work occurs; it should not quietly
hand that handler a billing repository, provider SDK, or arbitrary product
dependency. Apps own those business dependencies themselves.

### `lifecycle.ts` — starting and stopping in a controlled order

This file coordinates a process state machine: created, starting, ready,
stopping, stopped, or failed. It runs app startup hooks, starts resources,
marks readiness, then reverses the appropriate work during shutdown: app
pre-stop hooks, resource draining, reverse-order closing, telemetry flushing,
and app post-stop hooks. A host may call `beginDrain()` first: this moves the
state from ready to stopping and therefore makes readiness false before it
stops accepting new server or worker work.

It does not open a listening socket, poll a queue, or choose an orchestrator.
Server and worker hosts call this lifecycle controller while their own modules
handle HTTP or queue mechanics. The distinction is important: lifecycle says
whether a process is ready to work; a server or deployment target decides how
that fact is exposed and acted upon.

### `index.ts` — one stable public doorway

The barrel explicitly re-exports the supported runtime contracts and factory
functions. Callers continue to import from `@kanbien/platform-runtime`, even
though maintainers now have smaller files to inspect.

Internal error-construction helpers are intentionally absent from the barrel.
They help the registry and lifecycle implement their responsibilities, but they
are not a promise that applications, servers, or adapters may depend on their
current shape.

## Dependency direction

`errors.ts` is foundational. `registry.ts` uses it to report mount failures;
`lifecycle.ts` uses it to report lifecycle failures. `contexts.ts` is separate
from both because it only builds handler facts. `registry.ts`, `contexts.ts`,
and `lifecycle.ts` may depend on public Core and platform-contract vocabulary,
but not app internals, provider SDKs, server transport, worker delivery, or
infrastructure. `index.ts` comes last as the deliberate public barrel.

## What this split does not change

The split does not add a server, a queue provider, a scheduler, global mutable
registry, new lifecycle phase, app capability, or deployment behaviour. It
makes the current process-coordination responsibilities easier to locate while
the same type, runtime, and boundary tests prove the public behaviour.
