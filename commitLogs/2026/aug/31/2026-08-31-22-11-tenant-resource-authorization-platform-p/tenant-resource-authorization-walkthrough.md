# Tenant And Resource Authorization Walkthrough

## Why This Exists

This note preserves the user-facing explanation for the planned platform seam.
It is reference material for this chat session. The durable implementation plan
is `.agentic/03.product/plans/implementation/tenant-resource-authorization-platform-seam.md`.

## Starting Point

The current server can authenticate a caller and enforce a route-level
permission such as `smoke:read`. An authenticated route handler receives a
provider-neutral `Principal`.

The core package already has the vocabulary for richer future checks:

- `TenantContext` and `TenantResolver`;
- `ResourceRef`, relationship facts, attribute facts, and `Authorizer`;
- explicit allow or deny decisions.

What is not yet live is the platform plumbing that resolves a tenant, carries
it into handler context, and invokes an `Authorizer` before the handler
receives a protected resource request.

## The Three Planned Tasks

### Task 1: Route Contract

Extend the public route-registration contract so an app may explicitly declare
that an authenticated route has an optional or required tenant and/or a
resource-authorization step.

An app that declares neither retains today’s behaviour: the server does not
attempt tenant resolution or resource authorization.

The resource step accepts neutral facts: a resource reference, an app-declared
permission, relationships, attributes, and other serializable facts. It does
not define roles, groups, regions, clearance levels, membership storage, or a
policy language.

### Task 2: Runtime Context

Extend the runtime request-context factory to accept an optional, verified
`TenantContext` and expose it as `context.tenant` to the route handler.

This task only carries trusted context. It does not decide a tenant, query a
database, inspect a request-body tenant id, or evaluate a permission rule.

### Task 3: Server Enforcement

Make the server apply the declarations from Task 1 and build the context from
Task 2. The intended request sequence is:

1. Match the route and authenticate the caller.
2. Enforce declared route permissions.
3. Resolve a tenant only when the route declares one.
4. Build the handler context with the verified principal and tenant.
5. Validate request input.
6. Obtain app-supplied resource facts and invoke the provider-neutral
   `Authorizer` when the route declares resource authorization.
7. Invoke the handler only after all required checks allow the request.

Missing or invalid credentials remain `401`. A valid caller who lacks the
route permission, cannot resolve a required tenant, or is denied by the
resource authorizer receives `403` before the handler runs.

## Default And Failure Behaviour

| Route declaration | Platform behaviour |
| --- | --- |
| No tenant or resource declaration | Current permission-only behaviour; no additional provider is required. |
| Optional tenant, no resolver configured | The handler receives no tenant; this mode is context enrichment, not an access-control guarantee. |
| Required tenant, no resolver configured | Server creation fails before it listens. |
| Required tenant, resolver returns no verified tenant | The request is denied before the handler runs. |
| Resource authorization declared, no `Authorizer` configured | Server creation fails before it listens. |
| `Authorizer` denies | The request is denied before the handler runs. |

The fallback is therefore “do nothing unless an app opts in,” never “allow a
route that declared a required security control but lacks its provider.”

## Bill Example

For a future invoice route, the eventual app—not generic platform code—would
provide facts such as:

- Bill is the authenticated principal;
- Bill is assigned to a Benelux group;
- the invoice belongs to a Benelux client;
- Bill may view but not download an invoice at a given clearance level;
- a residency constraint prevents an EU resident from accessing a China-resident
  record.

Platform performs the common sequence and honors the final allow/deny result.
It does not decide what an accountant, region, clearance, residency rule, or
customer-service role means. A future app and its policy adapter own those
rules and the data that substantiates them.

## Boundaries

- `packages/core`: stable, provider-neutral concepts and authorization-question
  shapes.
- `platform/contracts`: app declarations and shared request-context shape.
- `platform/runtime`: context construction only.
- `platform/server`: HTTP sequencing, configuration validation, and safe
  response mapping.
- Apps or product modules: roles, memberships, resource loading, policy facts,
  and policy semantics.
- Provider adapters: any shared future policy-engine or identity translation.
- Infrastructure: databases, regional resources, IAM, secrets, and deployment
  topology.

## Out Of Scope

This plan does not create a tenancy database, group store, policy engine,
application, tenant onboarding flow, provider-specific adapter, AWS resource,
or deployment configuration. It also does not treat the smoke app as a real
business-policy example.
