<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.adr.0026-use-app-mount-as-platform-integration-boundary
  version: 1
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  kind: adr
  purpose: Record the app mount module as the platform integration boundary while leaving app internals app-owned.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: harness.architecture.rules.layers.platform
    path: docs/harness/architecture/rules/layers/platform.yml
  - id: harness.architecture.rules.layers.apps
    path: docs/harness/architecture/rules/layers/apps.yml
  - id: harness.architecture.rules.concerns.dependency-direction
    path: docs/harness/architecture/rules/concerns/dependency-direction.yml
-->
# ADR 0026: Use App Mount As Platform Integration Boundary

## Status

Accepted.

## Context

The platform runtime needs a stable way to mount apps before the product app
architecture is fully settled. A future app may organize its internals by
service, feature, capability, domain, use case, or another app-owned pattern.

If platform rules require that internal structure now, platform runtime work
would freeze an app design prematurely. If platform imports those internals,
the platform boundary leaks and normal app refactors become platform changes.

At the same time, the platform still needs one explicit, testable integration
surface so it can mount routes, jobs, health checks, config schemas, lifecycle
hooks, permissions, and app metadata consistently.

## Decision

Apps expose platform integration through one approved public mount module,
normally `apps/<app>/app.mount.ts`.

Platform composition roots such as `platform/server/mount.ts` and
`platform/workers/mount.ts` may import app mount modules. Other platform code
must stay unaware of app internals.

The app mount module may aggregate any app-owned internal structure, including
service, feature, capability, domain, use-case, route, job, health, config, or
workflow modules. That structure is not part of the platform contract.

When another layer needs app information, the app should expose it through an
approved public mount module, app manifest, generated deployment metadata, or
platform/app contract. The consuming layer should not inspect app internals to
discover runtime or deployment behavior.

## Consequences

Platform runtime work can proceed without deciding the final app internal
architecture.

Apps can refactor their internals without platform changes as long as the app
mount contract remains compatible.

Platform contract tests should exercise the mount module and registered
contributions rather than app-internal services, features, or capabilities.

If app teams later need a shared internal app pattern, that decision should be
made as an app-layer or product architecture decision, not as a platform
runtime requirement.
