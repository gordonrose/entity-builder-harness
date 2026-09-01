<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.plan.tenant-resource-authorization-platform-seam
version: 1
status: active
layer: 03.product
domain: identity-access
disciplines:
- architecture
- security
- requirements
kind: implementation-plan
purpose: Plan a provider-neutral platform seam for opt-in tenant context and resource authorization before real tenant-aware applications exist.
portability:
  class: source-only
  targets: []
used_by:
- id: product.workflow.platform-runtime-implementation
  path: .agentic/03.product/workflows/platform-runtime-implementation.md
- id: harness.architecture.plan.platform-runtime-implementation
  path: .agentic/03.product/plans/implementation/platform-runtime-implementation.md
-->
# Tenant And Resource Authorization Platform Seam

## Purpose

Add the smallest safe platform mechanism that lets future apps opt into tenant
context and resource-level authorization without making those concepts required
for today’s apps.

The change must preserve the current permission-only request path when an app
does not declare tenant or resource authorization. When an app does declare a
required control, the server must fail closed rather than silently allow the
request.

## Status

Implemented locally on 2026-09-01. This artifact records the implementation
boundary only; it does not authorize a tenancy database, group storage, a
policy engine, a provider adapter, AWS mutation, or a real tenant-aware
application.

## Baseline

- `packages/core/src/tenancy/index.ts` already defines `TenantId`,
  `TenantContext`, `TenantResolver`, and a nullable `TenantResolution`.
- `packages/core/src/authz/index.ts` already defines resource references,
  relationship and attribute facts, `AuthorizationRequest`, explicit decisions,
  and `Authorizer`.
- `platform/contracts/src/index.ts` already exposes an optional `tenant` on
  `PlatformRuntimeContext`, but route registration does not declare a tenant
  requirement or resource authorization step.
- `platform/runtime/src/index.ts` cannot yet receive a tenant when creating a
  request context.
- `platform/server/src/index.ts` authenticates a request and enforces declared
  route permissions, but does not resolve tenant context or call `Authorizer`
  before a handler runs.
- `apps/platform-smoke` has no tenant or resource-policy requirement and must
  keep its current behaviour.

## Ownership And Invariants

| Concern | Owner in this plan | Explicitly not owned here |
| --- | --- | --- |
| Stable tenant and authorization-question vocabulary | Existing `packages/core` contracts | Membership rows, role vocabulary, policy language, or provider SDKs |
| App opt-in declarations and context shape | `platform/contracts` | App internal structure or business services |
| Context construction | `platform/runtime` | Tenant selection or access decisions |
| HTTP order, startup validation, and denial mapping | `platform/server` | Roles, regions, clearance, residency, or resource semantics |
| Future membership/resource facts and policy | Owning app or product module | Generic platform defaults for business rules |
| Provider implementation, if later justified | A provider adapter and approved composition root | Provider selection in generic server/security code |
| Databases, regions, IAM, secrets, and deployment topology | `04.deploy` / infrastructure | Local platform-contract implementation |

The following invariants are non-negotiable:

1. Authentication identifies a principal; it does not prove tenant membership
   or resource access.
2. A request-body tenant id is untrusted input, never sufficient tenant proof.
3. A route that declares no richer control makes no resolver or authorizer call.
4. A route that declares a required control cannot start without the matching
   mechanism and cannot reach its handler if the check fails.
5. Resource facts, decision evidence, tokens, and provider objects are never
   returned to the client or written to normal request logs without an explicit
   safe logging/audit design.
6. Existing route-level permissions remain app-owned and continue to run before
   any potentially expensive tenant or resource lookup.

## Governance Prerequisite

Resolved before implementation on 2026-09-01. The owner-aligned documentation
migration places ADR 0027 at
`docs/03.product/adrs/0027-use-provider-type-service-adapter-layout.md` and
ADR 0028 at
`docs/04.deploy/adrs/0028-use-client-environment-deployment-target-profiles.md`.
The active platform-runtime workflow now references the canonical owner paths,
so this slice followed that workflow without inventing a replacement ADR.

## Implementation Plan

### 1. Add Opt-In Route Contracts

**Files**

- `platform/contracts/src/index.ts`
- `platform/contracts/tests/platform-contracts-types.test.ts`
- `platform/contracts/tests/platform-contracts-runtime.test.ts`
- `platform/contracts/README.md`

**Change**

Extend authenticated route declarations with an absent-by-default tenant
requirement:

- no declaration means no tenant resolution;
- `optional` means a configured resolver may enrich context, but its absence is
  not an access-control failure;
- `required` means a verified tenant must be present before the handler runs.

Add an optional app-owned resource-authorization contribution. It declares an
app-owned permission and returns provider-neutral resource, relationship,
attribute, and fact inputs. The platform binds the authenticated principal and
resolved tenant; the contribution cannot replace them.

The contract must represent a deliberate resource-not-found outcome separately
from an authorization denial, so an app can choose its resource-disclosure
behaviour without platform guessing.

**Acceptance**

- Existing public and authenticated registrations type-check unchanged.
- Tenant and resource declarations are rejected on public routes.
- The resource contribution cannot supply a different principal or tenant.
- Route permissions referenced by the contribution remain app-declared
  permissions.
- The contracts contain no domain values such as `accountant`, `Benelux`,
  `invoice`, clearance levels, jurisdictions, or identity-provider names.

### 2. Propagate Verified Tenant Context

**Files**

- `platform/runtime/src/index.ts`
- `platform/runtime/tests/platform-runtime-runtime.test.ts`
- `platform/runtime/tests/platform-runtime-types.test.ts`

**Change**

Allow `createPlatformRuntimeRequestContext` to accept an optional
`TenantContext` and copy it unchanged to `PlatformRequestContext.tenant`.

This is a data-flow-only change. It must neither inspect raw request data nor
run tenant policy. The server is responsible for supplying a verified value.

**Acceptance**

- A supplied `TenantContext` reaches the handler context unchanged.
- No supplied tenant leaves the context tenant-free.
- Raw strings or a principal id cannot stand in for a tenant id at compile time.

### 3. Enforce Route Declarations In The Server

**Files**

- `platform/server/src/index.ts`
- `platform/server/tests/platform-server-runtime.test.ts`
- `platform/server/tests/platform-server-types.test.ts`
- `platform/testing/src/index.ts` only if the focused server tests need a
  reusable resolver or authorizer fake.

**Change**

Add an optional `PlatformTenantResolver` server dependency using a
platform-contract-defined input shape containing the matched route, normalized
request data, and authenticated principal. Treat the request data as untrusted;
the resolver must prove membership or authority from trusted sources before it
returns `TenantContext`.

Apply request processing in this order:

1. Match the route and authenticate the caller.
2. Construct a complete provider-neutral principal for an authenticated route.
3. Enforce declared route permissions.
4. Resolve the tenant only when the route opted in.
5. Build the request context with the verified principal and tenant.
6. Validate request input.
7. Resolve app-owned resource facts and invoke `deps.authorizer` when the
   route declares resource authorization.
8. Map the result to a safe response before handler invocation.
9. Invoke the handler only on allow.

At shell creation, validate that every `required` tenant route has a resolver
and every resource-authorization route has an `Authorizer`. Add stable server
error codes for those configuration failures. At request time, map a missing
required tenant or an authorizer deny to a generic `403`; preserve `401` for
missing or invalid identity. Do not expose authorization evidence in the
client response.

**Acceptance**

- Existing `platform-smoke` behaviour and public-route principal absence remain
  unchanged.
- Missing or invalid identity returns `401`.
- A valid principal without the declared route permission returns `403` before
  tenant resolution or the resource contribution runs.
- A required tenant route without a resolver prevents the shell from starting.
- A resolver that returns no verified tenant for a required route returns `403`
  and the handler is not called.
- A resource-authorization route without `Authorizer` prevents the shell from
  starting.
- An `Authorizer` denial returns `403`, with no handler invocation or leaked
  facts/evidence.
- An allow decision delivers the authenticated principal and verified tenant to
  the handler.
- A deliberately not-found resource follows the app-declared disclosure
  outcome and is distinguishable from a policy denial in tests.

### 4. Preserve Tenant Context For Async Work

**Files**

- `platform/runtime/src/index.ts`
- `platform/runtime/tests/platform-runtime-runtime.test.ts`
- `platform/workers/src/index.ts`
- `platform/workers/tests/platform-workers-runtime.test.ts`

**Change**

When a `QueueMessage` already carries `tenantId`, construct the corresponding
`TenantContext` for the job context. A message without `tenantId` remains
tenant-free.

This does not create job-level tenant policy or a queue provider. A future app
that requires a tenant for a particular job must declare and validate that
requirement in its own job contract.

**Acceptance**

- A tenant-tagged queued message reaches its handler with the same tenant
  context.
- A tenantless message remains tenant-free.
- Existing worker retry, dead-letter, idempotency, and logging behaviour pass
  unchanged.

### 5. Keep Documentation And Governed Artifacts Current

**Files**

- `platform/contracts/README.md`
- `.agentic/03.product/plans/implementation/platform-runtime-implementation.md`
- `.agentic/03.product/plans/implementation/tenant-resource-authorization-platform-seam.md`
- `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`
  when governed-artifact regeneration recognizes the new plan

**Change**

Document the opt-in/fail-closed semantics, ownership split, and the distinction
between route permission enforcement and resource authorization. Re-baseline
canonical documentation paths against current `main` before editing the legacy
architecture-plan path, because active governance-path migration work may
replace it.

<!-- deterministic-check: allow reason="whether an implementation reveals a missing policy-neutral invariant requires architecture review; the plan does not prescribe an executable procedure" -->
The existing identity-access and tenancy rules already contain the desired
boundaries. Update them only if the implementation reveals a missing invariant;
do not duplicate product policy into a generic rule.

## Verification Plan

Run the narrowest checks for every changed surface:

- `npm run platform:contracts:check`
- `npm run platform:runtime:check`
- `npm run platform:server:check`
- `npm run platform:workers:check` when the async slice is implemented
- `npm run platform:testing:check` if `platform/testing` changes
- `bash scripts/01.harness/run-governed-script.sh scripts/01.harness/artifact-metadata/check-headers/script.sh --staged-added`
- governed recognition-source generation and its check mode if the generated
  artifact inventory changes
- `git diff --check`

Add focused, in-memory server tests using a synthetic app. Do not add an
invoice application, database, group table, policy engine, or cloud dependency
merely to prove this platform mechanism.

## Stop Conditions

Stop and obtain a separately governed decision if:

- implementation would require a real application, membership store, database,
  provider-specific policy engine, or cloud resource;
- platform code would import app internals rather than receive a public route
  contribution;
- a requirement would force a product-specific role, geography, clearance, or
  residency rule into core or generic platform code;
- a list/query authorization requirement needs database predicates or filtering
  semantics not represented by the single-resource decision contract;
- a target-specific provider, region, account, secret, or deployment decision
  would enter generic platform code.

## Deferred Work

The first real tenant-aware app needs a separate product plan to define:

- membership and tenant-selection data ownership;
- resource loading and not-found disclosure policy;
- roles, groups, relationship meaning, clearance taxonomy, and residency
  constraints;
- list/query authorization and data-layer filtering strategy;
- audit retention and evidence policy for sensitive decisions;
- any shared policy-engine adapter and its deployment configuration.

## Rollback And Compatibility

The contract additions are opt-in. Until an app declares a tenant or resource
authorization requirement, current requests use the existing permission-only
path. If a future app’s integration must be rolled back, remove its opt-in
declaration or injected resolver/authorizer from the composition root; current
apps remain unaffected.
