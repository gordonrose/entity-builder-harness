<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.adr.0025-place-composed-runtime-contexts-in-platform-contracts
  version: 1
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  kind: adr
  purpose: Record where composed request and job runtime contexts belong before platform runtime implementation.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: harness.architecture.rules.layers.platform
    path: docs/harness/architecture/rules/layers/platform.yml
  - id: harness.architecture.rules.layers.packages-core
    path: docs/harness/architecture/rules/layers/packages-core.yml
  - id: harness.architecture.source-material.platform-runtime-enterprise-obligations-v1
    path: docs/harness/architecture/source-material/platform-runtime-enterprise-obligations-v1.md
-->
# ADR 0025: Place Composed Runtime Contexts In Platform Contracts

## Status

Accepted.

## Context

The platform runtime needs a request context and job context before concrete
server and worker modules are implemented. Those contexts naturally combine
facts from many core modules: tenancy, authentication, i18n/localization,
logging, monitoring, config, queues, shared identifiers, clocks, and
cancellation.

Putting that composed shape in `packages/core/shared` would invert the module
graph. `shared` sits at the bottom of the core dependency stack, while a
composed runtime context depends on higher-level core capabilities and platform
runtime concerns.

At the same time, apps need a stable integration surface before platform/server
and platform/workers are built, so the context cannot remain implicit in future
runtime code.

## Decision

Composed request and job runtime contexts start in `platform/contracts`.

`packages/core/shared` may keep primitive context facts such as
`CorrelationId`, `CausationId`, `ISODateTime`, `Clock`, and the small
correlation/time `RequestContext`.

`platform/contracts` may compose those primitives with tenant context,
principal, locale, logger, metrics, config source, feature flag reader, queue
message, delivery metadata, route metadata, cancellation, and lifecycle/mount
dependencies.

A composed context may move down into `packages/core` only after at least two
independent consumers need the same provider-neutral shape and the dependency
direction can remain acyclic.

## Consequences

Platform runtime implementation can proceed against an explicit app-facing
contract without freezing server or worker internals too early.

Core remains provider-neutral and dependency-safe. Shared primitives continue
to be usable from every core module without importing tenancy, authn,
localization, logging, monitoring, queues, or platform concepts.

Future server and worker code should treat `platform/contracts` as the stable
boundary for app mounting, route handling, job handling, feature flags, and
runtime contexts until a later compatibility decision deliberately promotes a
shape into core.
