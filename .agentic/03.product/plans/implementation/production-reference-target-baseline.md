<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.plan.production-reference-target-baseline
version: 11
status: draft
layer: 03.product
domain: platform-reference-target
disciplines:
- architecture
- security
- sre
- requirements
kind: implementation-plan
purpose: Define the initial production reference target and its capability-completeness definition of done before platform implementation is described as production-ready.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.architecture.plan.platform-runtime-implementation
  path: .agentic/03.product/plans/implementation/platform-runtime-implementation.md
- id: product.plan.product-harness-foundation
  path: .agentic/03.product/plans/implementation/product-harness-foundation.md
- id: product.standard.identity-security-baseline.v1
  path: .agentic/03.product/standards/identity-security-baseline.v1.md
- id: harness.architecture.source-material.platform-runtime-enterprise-obligations-v1
  path: docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md
-->
# Production Reference Target Baseline

## Purpose

Define one explicit production reference target for the future Entity Builder
before individual platform modules, AWS adapters, or infrastructure plans are
called complete. This prevents a local TypeScript implementation, a target
profile entry, or a single provider adapter from being mistaken for an
operational production capability.

This is a planning and completeness artifact. It does not authorise AWS
mutation, public DNS, production deployment, collection of sensitive data, or
selection of a cloud resource that has not received its own governed target or
AWS planning slice.

## Why This Plan Exists

The repository has valid local platform work: provider-neutral contracts,
runtime mechanics, server transport controls, a Cognito adapter, and a blocked
AWS deployment-readiness scaffold. Investigating those pieces correctly
revealed further concerns such as shared rate limiting, secret lifecycle,
observability delivery, audit retention, tenant authorisation, and recovery.

Those discoveries are not implementation failures. They demonstrate that a
module-by-module learning sequence is insufficient as the definition of
production readiness. The reference target must instead be assessed through a
complete vertical slice:

```text
capability contract
  -> local/test implementation
  -> selected AWS adapter or host delivery
  -> provisioned infrastructure and target configuration
  -> safe failure and operating model
  -> repeatable evidence
```

The existing platform runtime plan remains the plan for local shell mechanics.
This plan is the authoritative production-completeness view for the initial
reference target. A capability is not described as production-ready for that
target until its required row in this plan has reached `operationally proven`.

## Reference Target Statement

### Target identity

The intended first reference target is a real, public-internet production
environment for the future Entity Builder product, deployed on AWS ECS Fargate.
`eu-west-1` is the initial EU residency target and the first launch is
explicitly EU-only. A UK-residency tenant cannot be hosted by that target
without crossing the declared boundary. UK support is deferred until a
separately planned UK-residency target is affordable, complete, and proven; the
EU target must reject UK-residency onboarding in the meantime. The target is
cost-aware and initially operated by one person, but it must be designed so
that a small, dependable baseline can be upgraded rather than replaced as usage
and reliability requirements grow.

The existing `kanbien/staging` target remains a draft planning/scaffold target.
It must not be relabelled as this production target. A distinct
`<client>/production` target profile, readiness manifest, and governed AWS
plan are required before any production infrastructure action.

### Product and interaction direction

The long-term product is an agentic Entity Builder that creates an end-to-end
entity slice: backend behaviour, front-end screens, and chat/voice interaction
through one governed workflow. A capability must remain independent of its
interaction channel: web, mobile, tablet, desktop, chat, and voice are clients
of the same authenticated, authorised, validated, observable capability—not
independent backends.

The first product release is narrower: public API capability first, profile
image and document support, safe bulk upload/download, then agent workflow.
Chat/voice and additional client surfaces are architectural requirements now,
but are not silently treated as implemented first-release runtime capabilities.

### Security, data, and identity direction

- The target must support the previously discussed full tenant, group,
  permission, and resource-level authorisation model. A valid identity alone
  is never sufficient to access a tenant or resource.
- The product is multi-tenant from its first real release. Tenant identity is
  a verified platform/product fact, not a request parameter or a URL segment;
  isolation is required for data, permissions, objects, jobs, audit records,
  and operational access.
- `PlatformRoot` is a deliberately exceptional product/operator authority, not
  a generic app role or an automatic right to read every tenant's business
  data. The first root identity is securely bootstrapped and root identities
  are invite-only. `PlatformRoot` creates/approves a tenant and appoints its
  tenant root; direct creation by this authorised parent is the approval
  action. Root bootstrap, approval, denial, disablement, recovery, and
  emergency access must be auditable and governed.
- `TenantRoot` is a tenant-scoped administrative authority. It manages that
  tenant's app users and tenant administration, but has no authority over any
  other tenant and cannot create or administer platform roots or tenants. A
  tenant root directly creating an app user is the approval action for that
  lower-scope user; it does not need a second PlatformRoot approval.
- `TenantAppUser` consumes tenant-scoped front-office and back-office business
  capabilities according to the permissions and resource policy assigned to
  that user. It has no tenant-administration or platform-administration power
  merely by using an application.
- These are product-level administrative role concepts, not core platform
  permission names. Roles bundle permissions at a defined scope; a later
  assignment model may deliberately compose administrative and app-user roles,
  but no implied hierarchy may allow a lower scope to administer a higher one.
  An action becomes implicit approval only when the caller holds the explicit
  management permission at the immediate parent scope; an ordinary app user
  cannot gain approval authority merely by invoking a create-user route.

The resulting approval flow is:

```text
PlatformRoot creates/approves tenant + appoints TenantRoot
  -> TenantRoot creates/approves TenantAppUser for that verified tenant
    -> TenantAppUser uses only explicitly granted business capabilities
```

Self-service registration follows the same hierarchy but begins pending: a
request to become a tenant root waits for PlatformRoot action; a request to
become an app user waits for TenantRoot action in the selected, verified tenant.
Direct authorised creation records `created-and-approved` in its audit trail.

The initial launch deliberately does **not** require MFA for `PlatformRoot` or
`TenantRoot`. This is an explicit early-stage risk decision, not a claim that
single-factor privileged authentication is the preferred long-term posture.
The initial human sign-in method is email and password. Before sensitive-data
onboarding or a changed risk posture, the decision must be revisited with the
chosen email-verification, password strength/breach/reuse, credential-reset,
session lifetime, privileged-login rate-limit, safe authentication-alert, and
identity-recovery controls. No plan may describe MFA as enforced until that
future decision is implemented and proven. Medical or other special-category
data must not be accepted until an MFA-capable baseline and target are
available and actually protect the applicable privileged roles.

Every human identity must verify its email before it becomes active; a
self-service signup does so before it can enter the pending approval workflow.
Password reset uses an email link too, but the
link must be purpose-bound (`verify-email` or `reset-password`), one-time,
short-lived, and unusable for any other identity operation. The link token is
credential-like data: it must not be placed in logs, audit payloads, analytics,
or referrer-bearing outbound requests. Passwords are never sent by email. A
successful password reset revokes every active session for that identity and
does not automatically authenticate the reset browser; the identity signs in
normally with the new password and receives a safe post-reset notification that
does not disclose credentials or recovery-token material.

Identity controls are configurable through the approved versioned default
security policy, `identity-security-baseline.v1`, adopted by each tenant.
`PlatformRoot` owns the non-weakenable platform floor, the baseline versions,
and any governed exception path. `TenantRoot` may select an approved baseline
and configure stricter tenant settings. A tenant policy may require available
MFA earlier, increase password strength, shorten session duration, lower
login/reset attempt limits, or add notifications/restrictions; it may not
disable email verification, purpose-bound reset links, reset-session
revocation, required audit evidence, or other platform invariants. A requested
relaxation requires an explicit exception with owner, reason, expiry, and
evidence; it must never be silently applied because a tenant configuration says
so.

The effective policy is the combination of the platform floor, adopted product
baseline, and tenant restriction—every applicable requirement must pass. Each
policy change must be authorised at its scope, versioned, validated, auditable,
and evaluated for its effect on existing sessions and pending signups. Policy
records contain settings and version references, never passwords, reset tokens,
or provider secrets. The detailed approved defaults and implementation evidence
requirements live in `../../standards/identity-security-baseline.v1.md`.

If the only active `PlatformRoot` is unavailable, recovery creates a
replacement root through a governed, one-shot root-recovery migration. It is
not an ordinary automatic schema migration, a normal application route, a
chat/voice tool, or an unrestricted database edit. The recovery operation must
be deliberately invoked through a protected recovery/deployment path, record
the recovery authority and intended replacement identity, verify preconditions
(including the prior root's state), disable/revoke the prior root where
appropriate, be idempotent, and emit durable audit evidence. The exact
bootstrap and recovery procedure remains a bounded design task.
- It is expected to handle personal and medical/sensitive data, classified by
  attribute sensitivity metadata. Sensitive data must not be placed in a
  production target until the applicable privacy, legal, data-processing, and
  operating evidence is explicitly approved; this plan does not make any legal
  compliance claim.
- The first launch accepts only EU-residency tenants. Its residency home
  controls primary data, files, backups, logs, audit records, queues, caches,
  search/indexes, support access, and AI/voice processing. UK residency remains
  a future separate target. Cross-boundary processing is denied by default. A
  future transfer exception requires an explicit governed policy, owner, reason,
  expiry, and evidence; cost pressure alone is not an implicit exception. Any
  global control-plane data must be separately allowlisted and contain no
  sensitive tenant content.
- The first reference target must support human identities and the required
  tenant/group/resource authorisation model. The existing Cognito path is
  machine-to-machine and is useful evidence, but is not sufficient on its own.

### Scale, resilience, and cost direction

- Initial demand may be one operator, with an early target of hundreds of
  concurrent users rather than internet-scale traffic.
- Cost matters because the product has no revenue yet. Managed services and
  conservative capacity are preferred when they reduce security or operational
  burden, but low cost must not become an excuse to omit sensitive-data,
  authentication, backup, or recovery controls.
- Disaster recovery may start with a cost-conscious recovery tier that can be
  upgraded later. The specific recovery point objective (acceptable data loss),
  recovery time objective (acceptable restoration time), backup frequency,
  restore test, and cross-region posture remain required decisions before real
  sensitive data is accepted.

## Boundary: Production Target Is Not A Claim Of Immediate Public Readiness

“Production reference target” means the target for which we will build the
complete default architecture. It does **not** mean that a public service may
be deployed or that medical data may be processed while required capability
rows remain incomplete. Public exposure, cloud mutation, and data onboarding
continue to be separately gated by deployment readiness and the relevant
governed AWS workflow.

## Immediate Execution Boundary: Platform Smoke Proof Only

The current implementation and learning scope is a production-shaped platform
proof using only `apps/platform-smoke`. It may prove packaging, controlled
target deployment, startup, health, configuration, provider-selected
machine-to-machine authentication, request handling, safe failure, and
operational evidence when the relevant deployment gates are approved.

It does **not** authorise building an identity-and-access app, user profiles,
tenant memberships, group assignments, approval workflows, entity persistence,
or any other business/application layer. The human identity, tenant/resource
authorisation, persistence, file, and entity rows remain requirements that
future product work must satisfy before real product data or users are
onboarded.

A successful smoke deployment proves a bounded platform/deployment slice. It
does not mean the Entity Builder is product-ready, human-identity-ready, or
ready to process personal or medical data.

### Existing public website is a separate continuity concern

The existing `kanbien.com` and `www.kanbien.com` public-site DNS boundary must
be retained. At the time of its read-only inspection, the legacy
`service-platform` workload was unavailable because its startup migration
could not connect to an RDS database in
`inaccessible-encryption-credentials` state. It is unrelated to the new
platform shell and must not be treated as a smoke-service candidate.

Restoring or replacing that public site is a separate, continuity-oriented AWS
change. It requires an explicit recovery or cutover plan, dependency and
backup assessment, tested rollback, and current approval. It does not
authorise deleting the shared ALB, legacy service, RDS instance, cache, or DNS
records, and it must not delay or broaden the bounded platform-smoke proof.

## Capability Maturity Vocabulary

Every required row uses one current state. Do not use the unqualified word
“implemented” in a plan or lesson without the state.

| State | Meaning |
| --- | --- |
| `not assessed` | The target need is not yet classified. |
| `requirements captured` | The need is known, but no platform boundary or design is approved. |
| `contract/local proof` | Provider-neutral contract and local/fake implementation are tested. |
| `adapter selected` | A concrete provider or host delivery mechanism is approved and tested at the boundary. |
| `infrastructure planned` | Target resources, IAM, network, encryption, cost, and rollback design are specified without mutation. |
| `target configured` | The target explicitly selects the capability and has non-secret configuration references. |
| `operationally proven` | Target deployment, failure behaviour, monitoring, access, recovery, and required evidence have passed. |

## Required Capability Matrix

The matrix is intentionally a concise completeness map, not a catalogue of
every AWS service. Each row must have a subordinate bounded plan before a
provider or infrastructure choice is made.

| Capability | Initial reference-target requirement | Current evidence | Current state | Production completion gate |
| --- | --- | --- | --- | --- |
| Deployment and supply chain | Repeatable immutable deployment, provenance, vulnerability policy, rollback, and one accountable operator. | Blocked target readiness scaffold and image build/smoke exist. | `infrastructure planned` | Production profile, CI identity, immutable image evidence, deploy/rollback and disaster exercise. |
| Public HTTP edge | TLS, DNS, safe ingress, request bounds, WAF/edge policy, trusted client address, health isolation. | Provider-neutral server transport is locally hardened; existing target remains blocked. | `contract/local proof` | Production ingress/edge design, configured trusted proxy policy, target limits, and deployed negative tests. |
| Human authentication and onboarding | Email/password human sign-in under `identity-security-baseline.v1`; tenant tightening over a non-weakenable floor; mandatory email verification before self-service approval; purpose-bound one-time 15-minute verification/reset links; successful password reset revokes every session and requires ordinary sign-in; a securely bootstrapped invite-only `PlatformRoot`; PlatformRoot approval of tenants/tenant roots; TenantRoot approval of app users; MFA explicitly deferred initially; governed replacement-root recovery migration. | Cognito machine-to-machine adapter and generic JWT verification exist; v1 is a policy, not an implementation. | `requirements captured` | Human identity flow, policy resolver/versioning/change audit, verification/password/reset/session/rate-limit controls, bootstrap/recovery migration, hierarchical approval state machine, scoped assignment model, explicit single-factor compensations, target-selected adapter, safe audit, deployment smoke, monitoring, and recovery. |
| Authentication operations | Key/JWKS behaviour, client-secret lifecycle, revocation/incident response, ownership, alerting. | Cognito operational-readiness requirements are recorded. | `requirements captured` | Target runbook, secret delivery/rotation, safe auth/audit telemetry, tests, and owner. |
| Permission, tenant, and resource authorisation | Verified principal, tenant membership, scoped `PlatformRoot`/`TenantRoot`/`TenantAppUser` grants, regional/resource restrictions, deny-by-default enforcement and no upward privilege escalation. | Core vocabulary and provider-neutral opt-in platform seam have local proof. | `contract/local proof` | Product membership/policy source, reviewed scoped-grant model, tenant resolver/authorizer implementation, denial/isolation/audit evidence. |
| Data classification and residency | Attribute sensitivity, initial EU-only tenant home, default cross-boundary denial, placement controls for logs/backups/support/AI, retention and deletion rules. | Core security classification concepts and the target policy direction are recorded. | `requirements captured` | EU target topology, data inventory, enforcement path, provider-location evidence, legal/privacy approval and cross-boundary exception process. |
| Configuration and secrets | Versioned non-secret config, confidential value delivery, least-privilege access, rotation, no-secret logging. | Environment/config patterns and target references exist. | `requirements captured` | Secret provider/delivery design, target IAM/resource policy, rotation/recovery test, scan and audit evidence. |
| Shared rate limiting and abuse defence | Consistent quota across replicas, route/principal policy, trusted address policy, safe failure decision. | `PlatformRateLimiter` contract and bounded in-memory limiter are tested. | `contract/local proof` | Shared-store adapter, target selection, network/credential design, failure policy, multi-replica proof. |
| Operational observability | Structured redacted logs, metrics, traces where required, collection/export, dashboards, alert ownership, retention/access controls. | Safe record normalisation and platform seams exist. | `contract/local proof` | Selected delivery path, target resources, alert/runbook/access policy, failure and deployed evidence. |
| Audit and security records | Durable, tamper-evident-enough record delivery, allowlisted facts, retention, access, export and review. | Record shape/normalisation direction exists; no durable sink. | `requirements captured` | Audit sink and integrity design, target resources, access/retention policy, verification and retrieval evidence. |
| Relational persistence | Tenant-scoped durable data, migrations, encryption, transactions, backup/restore, access controls. | No selected platform production path. | `not assessed` | Bounded persistence contract/adapter/infra plan and restore proof before any entity data. |
| Object/file storage | Profile images and documents, encryption, tenant isolation, lifecycle/retention, signed access, safe download. | Required by first release; no selected path. | `requirements captured` | Storage design, adapter/host delivery, isolation/retention/access proof. |
| Upload/download safety | Size/type controls, malware/unsafe-content strategy, bulk workflow, quarantine/approval, audit trail. | Required by first release; no selected path. | `requirements captured` | Threat model, ingestion workflow, storage/queue integration, negative tests and operating response. |
| Queue, workers, retry, and DLQ | Bulk operations and later agent workflows require durable execution, idempotency, retry, DLQ, correlation, and controlled recovery. | Worker/job contracts exist; no provider selection. | `contract/local proof` | Queue/DLQ adapter and infrastructure, worker target, replay/poison-message policy, operational evidence. |
| Scheduler | Scheduled agent, maintenance, or bulk work must have durable triggers, idempotency, time-zone and missed-run policy. | Identified in platform plan; no selected service. | `requirements captured` | Chosen scheduler/adapter, target policy, operational proof before scheduled work ships. |
| Agent workflow safety | Untrusted prompts/content, tool permission boundary, consequence confirmation, data minimisation, provider data boundary, evaluation and human escalation. | Security/prompt-injection governance is recorded; no production agent runtime. | `requirements captured` | Agent threat model, approved model/provider/data terms, policy enforcement, evals, audit and incident controls. |
| Chat and voice channels | Verified session identity, same capability authz path, transcript/audio privacy, retention/consent, confirmation and human handoff. | Channel-neutral product-harness direction is recorded. | `requirements captured` | Channel adapter and privacy/security model before a channel is exposed. |
| Recovery and continuity | Cost-aware backup, restore, incident runbook, dependency failure handling, RPO/RTO, upgrade path. | Deployment readiness requires rollback proof; no data recovery implementation. | `requirements captured` | Selected recovery tier, periodic restore exercise, owner/runbook and evidence. |
| Privacy/compliance governance | Data controller/processor decisions, lawful processing, subject rights, policy ownership, supplier review and evidence. | Requirement is now explicit; no compliance claim or operating record. | `requirements captured` | Appropriate expert/legal review and approved operating controls before sensitive production data. |

## Default Adapter And Infrastructure Policy

The initial AWS reference target may establish default adapters, but a default
is a versioned target/profile selection—not an implicit dependency in generic
platform code.

For each required capability:

1. Define or confirm the provider-neutral platform contract.
2. Keep a deterministic local fake or local implementation for development and
   contract tests.
3. Create a provider-specific adapter only after selecting the provider and
   defining failure, configuration, security, and lifecycle behaviour.
4. Place it under
   `platform/adapters/aws/<adapter-type>/<service-name>/` when it is runtime
   translation code.
5. Select it explicitly from a production target composition root/profile.
6. Plan infrastructure, IAM, network, encryption, cost, retention, and
   rollback in a separate governed deployment/AWS slice.
7. Do not mark the row operationally proven until target-level evidence passes.

Infrastructure-hosted delivery does not always need an adapter package. For
example, container log collection or secrets injection may be a target-host
mechanism. It still needs an explicit target selection, failure model, and
evidence; it must never be treated as automatic merely because ECS exists.

## Sequencing

### Phase A — Baseline and decisions

Use this plan to remove ambiguity before expanding code. Reconcile the
existing platform runtime plan, product harness plan, enterprise obligations,
target profile, and readiness manifest against this matrix. No empty adapters
or cloud resources are created in this phase.

### Phase B — Safe public API and sensitive-data foundation

Before the first real entity/data feature, complete the bounded plans for human
authentication, tenant/resource authorisation, data classification/residency,
secrets, public edge controls, shared rate limiting, observability/audit
delivery, persistence, object storage, upload/download safety, recovery, and
deployment evidence.

The first launch is EU-only. It must explicitly refuse UK-residency tenant
onboarding until a separate UK-residency target and every residency-inheriting
service are complete and proven; it must not place UK-residency data in the EU
target as a convenience.

### Phase C — Durable asynchronous work

Before bulk document operations or agent workflows, complete durable queue,
worker, retry/DLQ, scheduling where required, idempotency, and operational
recovery slices.

### Phase D — Agent and additional channels

Before exposing agent, chat, voice, desktop, mobile, or tablet flows, preserve
the one-capability model and complete their specific identity, authorisation,
privacy, data-boundary, consequence-control, accessibility, and observability
requirements.

High availability, multi-region recovery, and higher concurrency targets can
be planned as upgrades after a safe initial recovery tier is proven. They may
not reduce the Phase B requirements for sensitive-data protection, identity,
authorisation, backups, or target observability.

## Open Decisions Required To Turn This Into A Production Target Plan

These are deliberately visible rather than silently assumed:

1. Which selected human-identity provider configuration and adapter will
   implement `identity-security-baseline.v1`, including server-side tenant
   policy resolution, verification, reset, revocation, reauthentication, and
   safe telemetry?
2. Will real personal or medical data be accepted in the first release? If so,
   what privacy/legal review and operating evidence are required before
   onboarding it?
3. Which document types, maximum sizes, volumes, and download/export use cases
   are required; must uploaded content be quarantined/scanned before use?
4. Which AI/voice/model providers may receive data, and may sensitive source
   data, transcripts, or documents leave the selected residency boundary?
5. What low-cost initial recovery objective is acceptable: maximum data loss,
   maximum restoration time, and restore-test cadence?
6. What monthly operating-cost ceiling and alert threshold should guide early
   managed-service choices?

## Definition Of Done

The initial reference target may be called operationally production-ready only
when every capability required by the first release is `operationally proven`,
the corresponding target profile/readiness manifest is `ready`, and a governed
deployment has produced the required evidence. Capabilities needed only by a
future phase remain explicitly `requirements captured` or later; they cannot
be represented as available defaults to the product harness until their row is
complete. A tenant may not be onboarded into a residency home for which the
complete target and its inherited data services are not operationally proven.

## Evidence And Related Artifacts

- `docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md`
  supplies the existing detailed platform/runtime obligation input.
- `.agentic/03.product/plans/implementation/platform-runtime-implementation.md`
  owns local platform shell, server, authentication, and readiness mechanics.
- `.agentic/03.product/plans/implementation/product-harness-foundation.md`
  owns future product-consumption workflow and must publish only capability
  states this plan proves.
- `.agentic/03.product/standards/identity-security-baseline.v1.md` owns the
  approved initial human-identity defaults, tenant-tightening rules, and the
  evidence boundary between policy and implementation.
- `infra/04.deploy/03.product/targets/<client>/<environment>/` owns each
  concrete target profile and readiness manifest.
- `.agentic/aws/workflows/plan-aws-change.md` governs later AWS resource
  planning; `.agentic/aws/workflows/execute-approved-aws-change.md` governs
  approved mutation.
