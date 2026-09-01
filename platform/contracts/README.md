# Platform Contracts

`platform/contracts` is the stable app-facing contract layer for the runtime
platform. It lets apps register routes, jobs, health checks, config schemas,
and lifecycle hooks without receiving a raw server, worker loop, provider SDK,
or platform internals.

Source imports are intentionally narrow: `platform/contracts/src/**` may import
only local relative modules or public `@kanbien/core` package exports. It must
not reach into core source paths, app packages, infra code, runtime hosts, or
provider SDKs. `npm run platform:contracts:boundary` enforces that boundary.

The composed request and job contexts start here rather than in
`packages/core/shared`. They combine core concepts such as correlation ids,
tenant context, principals, locale, config, flags, logging, metrics, and clocks
with runtime facts such as request ids, paths, job names, queue messages, and
abort signals.

Core still owns provider-neutral primitive contracts. Platform contracts own
the runtime integration shape. Provider adapters and runtime modules will later
translate this contract into concrete server, worker, config, security,
observability, and lifecycle behavior.

Apps may organize their internals by service, feature, capability, domain,
use case, or another app-owned structure. Platform contracts do not prescribe
that structure. The platform consumes the approved public app mount module and
registered contributions, not app-internal files.

## Optional Tenant And Resource Authorization

Authenticated routes may opt into `tenant: "optional"` or
`tenant: "required"`. Routes with no tenant declaration preserve the existing
permission-only behavior. The server may enrich an optional route when a
provider-neutral `PlatformTenantResolver` is configured; a required route
cannot start without one and returns a generic `403` when it cannot resolve a
verified tenant.

An authenticated route may also declare `resourceAuthorization`. The app
provides an app-declared permission and a contribution that supplies only
resource, relationship, attribute, and fact inputs. The platform always binds
the authenticated principal and resolved tenant before it calls the core
`Authorizer`. The contribution can return a deliberate `not-found` outcome
with either `not-found` or `forbidden` disclosure; an `Authorizer` denial is
always a generic `403` and never exposes decision evidence.

These contracts do not define roles, groups, regions, clearance levels,
residency rules, resource storage, or an authorization-policy language. Those
are app or product concerns. Platform supplies the opt-in mechanics and fails
closed only when a route declares that it needs them.

Every public contract change should keep the source, type tests, runtime tests,
boundary test, README, and RAG evidence in sync when the contract meaning
changes.
