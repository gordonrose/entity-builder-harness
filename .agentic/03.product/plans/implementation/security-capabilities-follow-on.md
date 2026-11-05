<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.plan.security-capabilities-follow-on
version: 1
status: draft
created_on: "2026-10-28"
updated_on: "2026-10-28"
layer: 03.product
domain: security
disciplines: [architecture, security, sre]
kind: implementation-plan
purpose: Preserve deferred security capability work beyond the existing diagnostics and observability implementation.
portability: {class: source-only, targets: []}
used_by:
- id: product.readme
  path: .agentic/03.product/README.md
- id: shared.plan.governed-diagnostic-coverage
  path: .agentic/shared/plans/implementation/governed-diagnostic-coverage.md
-->
# Deferred security capabilities follow on

## Status and scope

Deferred; implementation has not started under this plan. Resume only when the
user explicitly selects a bounded security workstream. The current diagnostics
and observability work remains governed by the
[diagnostic coverage plan](../../../shared/plans/implementation/governed-diagnostic-coverage.md).
This backlog does not expand that work into identity applications or make new
security capabilities a prerequisite for unrelated observability improvements.

The deferred areas are sessions, cookies, cross-site request forgery (CSRF),
secret lifecycle, tenant isolation and security coverage for future integrations.
Each requires policy, implementation, enforcement and behavior proof in addition
to safe diagnostics. Recording this plan authorizes no runtime changes,
provisioning, credential access, cloud mutation, publication or deployment.

## Reconcile existing owners first

- [Identity Security Baseline v1](../../standards/identity-security-baseline.v1.md)
  already owns approved human sign-in requirements, session limits and rotation,
  reset-driven revocation, reauthentication, tenant tightening and separate audit,
  security-signal and operational evidence. Preserve those requirements rather
  than choosing new defaults in this plan. Its maturity remains requirements
  captured until its implementation and target proof exist.
- The [production reference baseline](production-reference-target-baseline.md)
  owns production identity, tenant boundaries, privileged administration and
  readiness requirements. This backlog neither supersedes it nor declares the
  platform shell production-ready.
- The [platform runtime plan](platform-runtime-implementation.md) limits current
  work to the shell and dummy app. Real identity or tenant applications require
  a separately approved product slice and applicable workflow; the existing
  shell workflow is not blanket authority to build them.
- The [tenant/resource seam plan](tenant-resource-authorization-platform-seam.md)
  records implemented opt-in contracts and enforcement. Extend and test those
  seams; do not replace them or mistake context propagation for complete data
  isolation.
- The [secret dependency standard](../../../04.deploy/00-target-alignment/standards/require-secret-dependency-declaration.md)
  owns secret and workload-identity declarations, access classes, lifecycle and
  safe evidence. Provider bindings and effective-access proof remain separate.
- Existing `platform/security` and the Cognito adapter supply bearer/JWT
  mechanisms and current diagnostic contracts. Preserve their public behavior
  and existing machine/API clients unless an explicit compatibility change is
  approved.

## Ownership

Core owns shared concepts, lifecycle contracts and closed observation reasons.
Platform owns reusable security mechanisms and executable diagnostic definitions.
Apps and products own feature policy, permission vocabulary and adopted baseline
versions. Adapters implement provider-specific operations and translate observed
evidence. Target composition and infrastructure supply concrete bindings,
resources and grants. The harness governs review and proof; it is not the
runtime schema or allowed-value registry.

Paths below are existing owners or candidate additions. New filenames, packages,
app names and target selection must be confirmed when the corresponding slice
is approved; naming a candidate does not approve its architecture.

## First checkpoint browser authentication

Review sessions, cookies and CSRF together before selecting their implementation.
Record an architecture decision covering:

1. The actual browser app, product and deployment target. Do not silently turn
   `apps/platform-smoke` or the persistence proof workload into a human identity
   application.
2. Browser/API origin layout and provider-login flow. Backend-managed sessions
   with server-held provider tokens are a proposal from the walkthrough, not an
   approved choice. The current Cognito machine path is not proof of compliant
   human sign-in or an automatic provider choice for every product.
3. Session storage, shared-instance consistency, renewal and revocation behavior,
   applying the existing baseline limits and policy-version rules. Define the
   effect of logout, password reset, account disablement, privilege changes and
   already-running requests or persistent connections.
4. Cookie scope and lifetime, callback transaction binding, anti-forgery policy,
   permitted authentication methods per route and ambiguous credential handling.
5. Public origin, trusted proxy boundaries, callback/return destinations,
   disclosure rules and application/ingress/browser telemetry treatment.
6. Compatibility, rollout, rollback, remaining requirements and separate live
   proof. Do not describe a partial browser slice as the complete identity
   baseline.

## Deferred backlog

Every item below is not started under this plan. Approve and inventory each
bounded slice before implementation; the browser items depend on the checkpoint
above, while secret and tenant work may be selected independently.

### Sessions

- **Use case:** signed-in access expires, renews and ends consistently across
  server instances and supported session types.
- **Candidate surfaces:** `packages/core/src/authn/`, reusable session mechanisms
  in `platform/security/`, `platform/contracts/src/contexts.ts` and `routes.ts`,
  server authentication/context wiring, an app-owned identity mount, a selected
  session-store adapter and product/target composition.
- **Work:** implement approved creation, identifier rotation, expiry, atomic
  renewal and revocation. Integrate reset and privilege/policy transitions with
  their owning features. Keep provider-token validation distinct from local
  session state and retain the existing bearer path.
- **Proof:** controlled-clock boundary tests; missing versus expired versus
  explicitly revoked state; store outage and uncertain writes; concurrent
  renewal/logout; reset revocation across applicable session types; multi-instance
  enforcement. Cookie deletion alone is not revocation proof.

### Cookies

- **Use case:** browsers receive and return only the cookies required by the
  approved flow, with deliberate security attributes and deletion behavior.
- **Candidate surfaces:** cookie mechanisms in `platform/security/`, typed
  response contracts in `platform/contracts/src/routes.ts`, server response
  adaptation/HTTP serialization and app-owned endpoint responses.
- **Work:** define parsing limits, duplicate/malformed handling, scope, lifetime,
  attributes and safe clearing. Add explicit multiple-cookie response support;
  current string-valued response headers are not a multi-cookie contract.
- **Proof:** actual HTTP header tests and HTTPS browser tests for acceptance,
  scope, script access, replacement and clearing. A missing cookie does not prove
  why a browser omitted it; cookie contents remain excluded from telemetry.

### CSRF

- **Use case:** a third-party site cannot trigger a protected browser action
  through credentials the browser sends automatically.
- **Candidate surfaces:** reusable request-protection mechanisms in
  `platform/security/`, route declarations/validation, server middleware order,
  identity callback handling and the eventual browser client.
- **Work:** assess applicability per authentication flow; select and implement
  anti-forgery and origin checks. Bind login callbacks to their initiating
  transaction. Apply normal protected-action checks before side effects; do not
  assume existing CORS or cookie configuration proves CSRF protection.
- **Proof:** legitimate and hostile origins in real browsers; absent, malformed,
  mismatched and cross-session material; callback replay/binding; missing or null
  origin behavior; no protected handler or mutation on rejection.

### Secret lifecycle

- **Use case:** only authorized workloads obtain and use required credentials,
  including during rotation, revocation, restart and recovery.
- **Candidate surfaces:** `packages/core/src/security/`, `platform/config/`,
  affected adapters and entrypoints, and existing deployment secret/workload-
  identity contracts and validators.
- **Work:** reconcile existing grants, startup injection or identity renewal,
  rotation, established connections and retirement against the owning standard.
  A `SecretString` type label is not encryption or automatic disclosure control.
- **Proof:** missing/invalid material, rejected credentials, denied operations,
  replacement/new-connection behavior, partial rotation and urgent revocation.
  Prove both allowed and forbidden provider operations; declarations alone are
  not effective-access evidence. Never blindly replay an uncertain mutation.

### Tenant isolation

- **Use case:** tenant identity and authorization remain effective across every
  selected request, data operation and background handoff.
- **Candidate surfaces:** existing Core tenancy/authz contracts, platform
  contexts/server/workers, app-owned membership and repositories, persistence,
  cache/file/message adapters and bounded administrative operations.
- **Work:** retain opt-in seam compatibility; establish verified tenant facts
  and enforce them at the relevant data/call boundaries. Do not trust a request
  tenant identifier or equate authentication with membership. Review cache keys,
  jobs, events, files and administrative bypasses as well as HTTP authorization.
- **Proof:** two-tenant negative tests, missing context, spoofed selection,
  cross-tenant reads/writes and asynchronous handoffs, safe not-found/forbidden
  behavior and denial before side effects. A consistency check on two supplied
  identifiers does not prove every query is isolated.

### Future integrations

- **Use case:** each new or changed service/capability has an explicit security
  and failure contract rather than inheriting an unsupported coverage claim.
- **Candidate surfaces:** owning app/platform capability contracts, provider
  adapters, target dependency declarations and registered check definitions.
- **Work:** inventory credentials, destinations, permissions, validation,
  deadlines, cancellation, retries, tenant propagation, sensitive-data handling
  and recovery. Define whether repeated operations can duplicate effects.
- **Proof:** contract and adapter tests, denied access, malformed responses,
  bounded dependency failure, sensitive canaries and uncertain post-send outcomes.
  A timeout after a write was submitted is not proof the provider did no work.
  Reuse existing harness adoption and verification controls; add only justified
  missing checks through their owner, not a parallel registry.

## Diagnostics and security evidence

For every implemented boundary, map the exact predicate to its code-owned
definition and tests. Preserve distinct missing, invalid, denied, expired,
revoked, unavailable and unknown outcomes only where evidence supports them.
For example, a failed session-store read cannot establish an invalid session,
and an uncertain revocation write cannot establish completed logout.

Exclude passwords, session/cookie identifiers and contents, codes, tokens,
anti-forgery material, raw provider payloads and cross-tenant data. Safe logical
references and classifications require their owning schema. Preserve records
through wrappers and verify both internal delivery and public non-disclosure.

Operational diagnostics, durable audit events and security signals remain
separate record classes under their existing owners. The approved identity
baseline's audit and signal obligations are part of future capability acceptance;
existing operational logging does not satisfy them automatically.

## Deployment verification and completion

After a slice is approved, identify affected consumers and exact predicates in
the existing plan/session, implement connected changes, close source review,
prepare artifacts and run focused proof under the
[change-completion standard](../../../shared/standards/require-change-completion.md)
and [diagnostic workflow](../../../shared/workflows/verify-diagnostic-coverage.md).
Use registered reusable checks and complete impact-selected verification.

Future evidence must distinguish type/unit proof, real adapter integration,
actual HTTP and browser behavior, compiled payload/container qualification and
live target proof. Register missing browser/store/target checks before claiming
their boundary is covered. A source-only pass is not browser or deployment proof.

Deployment slices must declare resources, secrets/identity, permitted operations,
health/dependency behavior, retention and recovery under their existing owners.
Qualify compatibility and rollback, including retained sessions and storage
schema versions. Switching a feature off is not proof that every session has
been revoked. Keep old machine/API paths and accepted deployments intact unless
an explicit change is approved.

The [platform-shell workflow](../../workflows/platform-runtime-implementation.md)
does not authorize real product identity features. Select or establish applicable
product workflow coverage before that implementation; provider execution stays
with `04.deploy` and `.agentic/aws/`, requiring its separate approvals.

Completion is per approved workstream and target, with observed evidence and
remaining debt recorded. No single catalog, token test or future-integration
template establishes exhaustive security coverage.
