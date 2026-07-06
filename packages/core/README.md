# @kanbien/core

`packages/core` is the shared contract layer for stable Kanbien concepts.

It should contain product-neutral types, ports, error shapes, policy facts, and
small pure helpers that apps and platform implementations can depend on without
pulling in runtime providers.

## Boundary

- Core may define contracts for apps and platform to consume.
- Core may define no-op or in-memory test helpers when they preserve the same
  public contracts.
- Core must not import apps, platform, infra, cloud SDKs, ORMs, web servers, or
  vendor clients.
- Concrete provider adapters belong in `platform`.
- Product workflows belong in `apps`.

This initial slice establishes the package surface and core capability modules.
Provider implementations and app runtimes are intentionally out of scope.

## Shared Primitives

`shared` contains the lowest-level vocabulary used by the rest of core:

- `Brand` and `EntityId` distinguish important string identifiers at type level.
- `CorrelationId` connects logs, audit records, events, and errors from one request.
- `ISODateTime` stores timestamps in a JSON-safe text form.
- `Result`, `ok`, `err`, `isOk`, and `isErr` make expected success/failure explicit.
- `CoreError` gives failures a stable `code`, readable `message`, and optional metadata.
- `Clock`, `systemClock`, and `fixedClock` keep time-dependent code testable.
- `RequestContext` carries only the minimum shared request metadata.

Keep this module small. Tenant, principal, permission, persistence, audit, and
event-specific concepts should live in their own modules and import shared
primitives when needed.
