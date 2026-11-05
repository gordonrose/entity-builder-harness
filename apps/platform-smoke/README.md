# Platform Smoke App

`apps/platform-smoke` is a deliberately small app contribution used to prove
that the platform contracts, server shell, worker shell, health checks, config,
authentication, and lifecycle can work together. It is not a template for a
future product app's internal architecture.

The app owns the logical `app-name` configuration diagnostic and accepted-job
`payload.outboxEntryId` validation diagnostic. Generic schema position and Core
reader evidence are retained separately. Existing validators still decide
acceptance, including inherited data fields and nonempty whitespace strings.
Diagnostic projection never invokes the payload getter again: accessors,
uninspectable objects and a bounded prototype walk report `not-assessed`, not a
guessed invalid value. No supplied payload, app name or environment value enters
these closed records. Server/worker mounts explicitly select this app catalog;
public response/error and metric projections remain unchanged.

## Boundary

Consumers import `@kanbien/app-platform-smoke` through its public package
entry point. Hosts compose the exported `PlatformApp`; they do not import the
app's private files. The app declares intent through platform contracts and
does not start a server, select a queue provider, or configure deployment
infrastructure.

## Responsibility map

| Path | Responsibility | Verification |
| --- | --- | --- |
| `src/app.manifest.ts` | Stable app identity, declared permission, route base path, job, health, and required-config metadata. | `npm run app:platform-smoke:check` |
| `src/app.mount.ts` | Public app contribution: config schema, route, job, health check, and lifecycle hooks. | `npm run app:platform-smoke:check` |
| `src/persistence/` | Harmless work-item acceptance meaning and the transaction-aware repository seam; it imports no provider adapter. | `npm run app:platform-smoke:check` |
| `src/index.ts` | Deliberate public exports only. | `npm run app:platform-smoke:check` |
| `tests/platform-smoke-runtime.test.ts` | Server and worker composition proof using platform test dependencies. | `npm run app:platform-smoke:check` |

## Current semantic names

The app ID is `platform-smoke`. Its permission is
`platform-smoke.smoke:read`; its route, job, and health names use the same
owner prefix. This lets the runtime reject an accidental declaration in another
app's namespace during startup or contract testing.

## Persistence smoke boundary

The persistence capability is deliberately small: a unique work item becomes
`accepted` at revision `1`. It asks an injected
`PlatformPersistenceAtomicWriter` for one transaction scope, passes the scope
to its repository, and stages the matching safe lineage and outbox facts.

This is the boundary that keeps responsibilities honest. The app owns the
meaning of a work item and the create-once rule. A selected composition and
storage adapter own the table, keys, conditional writes, and physical atomic
transaction. The app has no DynamoDB client, configuration, or provider
vocabulary.

## Controlled acceptance route

The default smoke app exposes only its existing read route. A host must opt in
to the persistence proof by calling `createPlatformSmokeApp` with the
app-facing persistence dependencies. Only that opt-in app registers
`POST /smoke/work-items` and its separate
`platform-smoke.persistence.work-item:create` permission.

The endpoint accepts no request body. It derives its work-item ID, direct
cause, and retry identity from the platform request ID, then replies `202`
with only that opaque identifier and the `accepted` status. Retrying a request
with the same ID reaches the create-once rule rather than creating a new work
item. The route intentionally does not expose table names, outbox IDs, queue
payloads, provider errors, tenants, or business data.

Acceptance forwards selected Core/Persistence source diagnostics through the
request's profile-governed `onDiagnostic` callback, independently of its existing
business failure record. Each invocation tracks actual attempts, retaining a
returned primary plus eight companions without replaying already attempted
copies. Selection alone is not delivery. Observer failures never alter the
500 invalid-generated-ID, 409 duplicate, 503 other-error or native-throw paths.
An opted-out/non-log profile supplies `{}` to silence writer defaults. No
observer/options state is shared across concurrent requests. Hosts can add
`diagnosticDefinitions` to `createPlatformSmokeApp` for source selection, but
must separately register the corresponding reporter catalogs in composition.
Only validated own-data copies are compared; submitted values/native messages
are never diagnostic detail or deduplication input.

## Durable delivery boundary

The accepted work item creates an immutable outbox fact with message type
`platform-smoke.work-item.accepted`. The app registers a job with that same
type, so a relay-produced envelope has exactly one declared worker handler.
The handler is deliberately harmless: it records only a safe completion log.
The platform worker, not this app, owns durable claim, fence, completion,
retry, and duplicate-skip mechanics.

The runtime test proves the local chain below using in-memory stores and the
provider-neutral queue port:

```text
accept work item -> stage outbox fact -> relay -> queue envelope
                                              -> durable worker completion
                                              -> duplicate delivery skipped
```

This is a source and local-control-flow proof. It does not mean that this app
starts a relay, runs a scheduler, selects SQS, or has live DynamoDB access.
Those deployment choices remain in the Kanbien staging target composition.

## Write-admission diagnostic

When the same opt-in persistence seam is selected, the app also exposes
`POST /smoke/work-items/admission`. It requires the exact same declared write
permission and accepts no request body, so it traverses the public HTTP,
authentication, authorisation, rate-limit, route-validation, and profile
telemetry path. Its handler returns `204` and deliberately does not call the
repository, atomic writer, outbox, queue, or any provider client.

This is a bounded diagnostic, not a second persistence capability. It exists
only to distinguish a pre-handler boundary failure from a transaction failure
before a newly authorised persistence acceptance is attempted.
