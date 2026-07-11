<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.adr.0031-use-products-as-app-composition-boundary
  version: 1
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  kind: adr
  purpose: Record products as the boundary that composes apps while deployment targets describe where products run.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: harness.architecture.plans.platform-runtime-implementation
    path: docs/harness/architecture/plans/platform-runtime-implementation-plan.md
  - id: harness.architecture.rules.layers.apps
    path: docs/harness/architecture/rules/layers/apps.yml
  - id: harness.architecture.rules.layers.platform
    path: docs/harness/architecture/rules/layers/platform.yml
  - id: product.workflow.platform-runtime-implementation
    path: .agentic/product/workflows/platform-runtime-implementation.md
-->
# ADR 0031: Use Products As App Composition Boundary

## Status

Accepted.

## Context

The platform runtime now has an app mount boundary: apps expose public mount
modules, and platform internals must not depend on app internals. The next
question is where a named product, such as Kanbien Platform, says which apps it
contains.

It is tempting to treat the first staging environment as the product because
that is the first place the shell will run. That would mix product identity
with deployment topology. Over time, the same product may run in staging,
production, client-owned accounts, different repositories, or different cloud
providers. Those target choices should not define the product itself.

The app layer also needs to own app-specific permission vocabulary. If the
platform or deployment target invents those permissions, app meaning leaks into
provider-neutral runtime code or environment-specific configuration.

## Decision

Products compose apps.

Product composition belongs under:

```text
products/<product>/
```

The first product composition target is:

```text
products/kanbien-platform/
```

`products/kanbien-platform` represents the Kanbien Platform product. It should
initially compose `apps/platform-smoke` so the platform shell can prove product
composition, app mounting, authz wiring, and deployment readiness with a boring
dummy app. Later it can compose real Kanbien apps.

Deployment targets remain separate. `kanbien/staging` is an environment target
for the Kanbien Platform product, not the product itself.

Product manifests may reference app public manifests, app mount modules, or
generated app metadata. They may include product-level role groupings only when
those groupings reference permissions declared by the apps included in the
product.

Product manifests must not contain AWS account, region, DNS, CORS origins,
auth provider secrets, image digests, readiness blockers, or other
environment-specific deployment values. Those belong in deployment target
profiles.

## Consequences

The repo keeps three different questions separate:

1. Apps answer what behavior and permission vocabulary they expose.
2. Products answer which apps form a named product.
3. Deployment targets answer where and how that product runs.

The Kanbien Platform can start with a smoke app without making the smoke app
the real product architecture template.

Future clients, environments, repositories, AWS accounts, Azure subscriptions,
regions, runtime families, identity providers, and secrets can be added through
target profiles and provider adapters without changing ordinary app feature
code.

Platform runtime code can validate and enforce app-declared permissions while
remaining provider-neutral.

## Non-Goals

This ADR does not define the final product manifest schema.

This ADR does not authorize cloud mutation, public internet exposure, DNS
changes, IAM changes, secret provisioning, image publishing, or production
deployment.

This ADR does not decide the final internal structure of real Kanbien apps.

This ADR does not choose an authentication provider.
