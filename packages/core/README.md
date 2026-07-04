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
