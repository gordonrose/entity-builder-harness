# Chat Session: 2026-08-31-01-11 product-harness-foundation-plan

<!-- agentic-session
id: 2026-08-31-01-11-teach-the-architecture-list-in-the-supplied-attachment-in-sm
task: Teach the architecture list in the supplied attachment in small, interactive chunks, using the project's terminology and fully annotated code examples.
branch: chat/2026-08-31-01-11-teach-the-architecture-list-in-the-supplied-attachment-in-sm
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-08-31-01-11-teach-the-architecture-list-in-the-supplied-attachment-in-sm-1609907486
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-08-31T00:11:19Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-09-06T11:45:24Z
latest_commit_sha: bf92725
chat_duration: 560045s (06:11:34:05)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

Teach the architecture list in the supplied attachment in small, interactive chunks, using the project's terminology and fully annotated code examples.

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- Can the architecture tutoring session be recorded as a printable Markdown
  handbook and updated as learning continues?
- Should a future, bound platform capability investigate and remediate
  dead-lettered messages while escalating destructive or uncertain actions to
  humans?

## Issues Raised

- This chat branch predates the owner-aligned move of the platform runtime
  plan to `.agentic/03.product/plans/implementation/`. A governed checkpoint
  and refresh from local `main` are required before changing that canonical
  plan.

## Decisions Made

- Create a canonical, printable architecture learning handbook in
  `docs/education/teaching-notes/` and link it from this session log.
- Update the handbook after each completed learning chunk; use this session log
  as the audit trail for the learning activity.
- Treat future DLQ self-healing as a bounded, policy-controlled remediation
  capability: diagnosis and recommendations may be automated, while replay,
  purge, or other consequential actions require explicit allowlists, evidence,
  and human escalation where appropriate.
- Treat each architectural clarification from this learning session as a
  planning-triage item: update its owning implementation/architecture plan in
  the same chunk, or record an explicit no-plan-change rationale. If no plan
  owner exists, identify that gap before creating new planning material.
- Decision: Record RAG knowledge disposition: covered.
  Rationale: The security-module organisation and platform-contract naming
  policy are accompanied by rule-pack, source-material, source-review,
  derivation, projection, retrieval-fixture, and recognition-source evidence.

## Context Hygiene

- The handbook distinguishes current repository evidence from intended
  architecture so incomplete future work is not presented as implemented.
- The canonical runtime plan is on current local `main`; the pending chat
  changes have passed core and rulebook verification before their checkpoint.
- The chat branch has now refreshed from local `main`; the semantic naming
  material was reconciled into canonical `03.product` paths before the
  deferred DLQ remediation entry was added.


- Summary: Four reviewable commits are planned: policy/evidence; contracts plus runtime registry namespace enforcement and source organisation; security source organisation; and the architecture learning/planning record. Generated rulebook outputs remain with their governing sources. The runtime split is coupled to the namespace migration because its registry is the enforcement boundary.
  Durable evidence: The checked source, tests, package maps, plan, handbook, and session log in this chat-owned worktree are the durable evidence; no provider, deployment, or product behaviour was added.

## Activity Log

### 2026-08-31T00:11:19Z - Session started

Initial intent: Teach the architecture list in the supplied attachment in small, interactive chunks, using the project's terminology and fully annotated code examples.

### 2026-09-01T20:34:55Z - Architecture learning handbook created

Created the canonical printable study note at
`docs/education/teaching-notes/0002-architecture-learning-handbook.md`.
It records completed lessons, repository evidence, misconceptions, study
questions, and a protocol for appending later lesson chunks.

### 2026-09-01T20:49:57Z - Platform-contract topic grouping studied

Classified the current `platform/contracts` surface into proposed natural
topics: errors, names, feature flags, contexts, permissions, routes, jobs,
registry, and app definition. Recorded the proposal in the handbook without
moving any source files.

### 2026-09-01T20:52:06Z - Platform-contract groupings explained

Added a first-time-learner explanation of each proposed platform-contract
topic to the handbook, including what each owns, why it is separate, common
misconceptions, and a route-to-authorization study question. No source files
were changed.

### 2026-09-01T20:55:59Z - Platform-contract dependency direction studied

Added the proposed one-way dependency map for platform contract topics to the
handbook. The lesson explains the distinction between source dependencies and
runtime order, uses an invoice route as an example, and records why cycles are
harmful. No source files were changed.

### 2026-09-01T20:59:58Z - Semantic nomenclature proposal studied

Recorded a proposed semantic naming profile for app-owned routes, jobs, flags,
health checks, and permissions. The proposal keeps tenant, group, role,
provider, and version facts out of stable permission names and identifies the
registry/runtime mount boundary as the place to enforce app ownership prefixes.
No rule or source files were changed.

### 2026-09-01T21:03:11Z - Cross-codebase scanability assessed

Recorded the strongest candidates for semantic scanability beyond platform
contracts, including platform security, runtime, server, and selected core
capabilities. Captured security, operational, compatibility, and over-splitting
risks plus a staged adoption sequence. No source files were changed.

### 2026-09-01T21:40:41Z - Identifier category-prefix convention studied

Recorded the rule of thumb that files, TypeScript types, and explicit fields
should state an identifier's functional category; identifier values should
state stable owner and capability. Configuration keys and error codes need
clear subsystem/subject names in flat operational contexts, but generally do
not need redundant `config` or `error` prefixes. No rule or source files were
changed.

### 2026-09-01T21:45:24Z - Naming-policy home and adoption sequence studied

Identified the existing `platform.contracts-are-the-app-boundary` rule in
`docs/03.product/rules/platform/layers/platform.yml` as the future home for
the semantic naming profile. Recorded why this is a platform-contract standard
rather than core, product-harness, security, or tenancy policy, plus a
document-first and validator-second adoption sequence. No rule or source files
were changed.

### 2026-09-01T21:58:33Z - Platform-contract naming policy codified

Added a source-reviewed semantic identifier naming policy to the existing
platform layer rule. The complete evidence chain includes the source-material
addition, an accepted two-iteration OKF review record, updated derivation
report, refreshed source provenance, and a focused retrieval-selector fixture.
Source projection, coverage, source-review, derivation-report, provenance,
selector, index, chunk, recognition, and diff checks passed. No runtime code or
identifier values were changed; registry-level enforcement remains a future
compatibility-preserving implementation slice.

### 2026-09-01T22:02:31Z - App mount and registry studied

Added a handbook lesson that traces app declarations through the runtime
registry and into the server and worker shells. It distinguishes local
registration checks from cross-declaration validation, explains the
startup-failure boundary, and connects the deferred app-ownership naming check
to the mount context. No runtime source files were changed.

### 2026-09-01T22:09:43Z - Registered jobs and workers studied

Added a handbook lesson that follows a registered job through queue dispatch,
payload validation, optional idempotency, job context, successful execution,
retry, and dead-letter handling. It also records the current in-memory queue's
delayed-delivery limitation and the distinct roles of tenant context and
end-user authorization. No runtime source files were changed.


### 2026-09-01T22:23:13Z - Commit recorded

Commit: `86e0c5a`

Message: feat(core): organize security contracts and platform guidance

Summary: Checkpointed the core security module split, product-harness foundation plan, source-reviewed platform naming standard, and printable architecture handbook before the governed main refresh.

ADR impact: No new ADR; the naming policy extends an existing platform rule.


### 2026-09-01T22:25:57Z - Main refresh conflict recorded

Path: `.agentic/02.rag-rulebook/derivation-reports/03.product.platform/2026-07-07-platform-runtime-enterprise-obligations-v1.yml`

Type: `normal-repo-conflict`

Mode: stopped

Action: Stopped before reconciliation; a later approved resolution must retain canonical owner paths and migrate the naming-policy evidence.


### 2026-09-01T22:25:57Z - Main refresh conflict recorded

Path: `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`

Type: `normal-repo-conflict`

Mode: stopped

Action: Stopped before regeneration; regenerate only after the source-path and rule-content conflicts are resolved.


### 2026-09-01T22:25:57Z - Main refresh conflict recorded

Path: `docs/03.product/rules/platform/layers/platform.yml`

Type: `normal-repo-conflict`

Mode: stopped

Action: Stopped before reconciliation; a later approved resolution must keep the canonical 03.product rule path and migrate the naming-policy rule with refreshed provenance.


### 2026-09-01T22:33:28Z - Main refresh conflict recorded

Path: `.agentic/02.rag-rulebook/derivation-reports/03.product.platform/2026-07-07-platform-runtime-enterprise-obligations-v1.yml`

Type: `normal-repo-conflict`

Mode: manual

Action: Kept canonical 03.product paths, migrated semantic-naming claims and review evidence, and validated the reconciled report.


### 2026-09-01T22:33:34Z - Main refresh conflict recorded

Path: `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`

Type: `normal-repo-conflict`

Mode: manual

Action: Resolved source evidence first, then regenerated artifacts.yml and verified it is current.


### 2026-09-01T22:33:39Z - Main refresh conflict recorded

Path: `docs/03.product/rules/platform/layers/platform.yml`

Type: `normal-repo-conflict`

Mode: manual

Action: Kept the canonical 03.product rule, preserved the semantic identifier rule, and refreshed source provenance from the migrated source material.


### 2026-09-01T22:35:52Z - Dead-letter remediation deferred and studied

Added a bounded future capability to the canonical platform runtime plan and
the printable handbook. It begins with redacted, read-only diagnosis and
supervised recommendations; any later automated replay must be explicitly
allowlisted, idempotent, tenant-safe, audited, rate-limited, and stoppable.
Queue-wide purge, payload repair, and access-policy changes remain
approval-controlled. No runtime source files were changed.


### 2026-09-01T22:35:52Z - Platform server request entry studied

Added the first server lesson to the printable handbook. It explains startup
validation, request preparation, method/path matching, and why a matched route
is only a candidate handler rather than proof of authorization. No runtime
source files were changed.


### 2026-09-01T22:35:52Z - Authentication status boundary studied

Added the next handbook lesson. It explains why an absent or invalid identity
returns 401, why an authenticated principal without the route's permission
returns 403, and why neither case invokes the protected app handler. No runtime
source files were changed.


### 2026-09-01T22:35:52Z - Tenant and resource authorization studied

Added the next handbook lesson. It explains the difference between a broad
permission and a decision over a specific tenant and resource, including
fail-closed tenant resolution, relevant authorization facts, and deliberate
403 versus 404 disclosure. No runtime source files were changed.


### 2026-09-01T22:35:52Z - Request completion boundary studied

Added the next handbook lesson. It explains route-shape validation, safe 400
and 500 error responses, app-handler responsibility, and the shared request
logging and metrics trail. No runtime source files were changed.


### 2026-09-01T22:35:52Z - Server lifecycle studied

Added the next handbook lesson at a slower, more detailed pace. It explains
pre-listen validation, liveness versus readiness, health endpoint exposure,
and the ordered graceful-shutdown lifecycle. No runtime source files were
changed.

### 2026-09-01T22:54:01Z - Worker lifecycle studied

Added the next handbook lesson at the same slower pace. It compares server
request-response delivery with queued-message delivery; traces worker startup,
dispatch, tenant context, idempotency, retry, dead letter, readiness, and
shutdown; and keeps the current in-memory worker shell separate from the
future provider polling, acknowledgement, and in-flight drain work. No runtime
source files were changed.

### 2026-09-01T23:02:29Z - Request and queued-job authority studied

Added the next handbook lesson at the same slower pace. It contrasts the
verified human principal, route permissions, tenant resolver, and
resource-authorizer path with the current worker's tenant-scoped message
context, which carries no principal and performs no worker-side group, role,
permission, or resource authorization. It records the safe handoff pattern and
the product-policy decision about work that executes after a human's access
changes. No runtime source files were changed.

### 2026-09-01T23:07:10Z - Platform adapters studied

Added the next handbook lesson at the same slower pace. It explains adapters as
narrow provider translators, traces the implemented Cognito adapter through
generic platform security into the Kanbien target entrypoint, distinguishes
provider claim vocabulary from group-to-permission policy, and records that
the other AWS adapter paths are conventions rather than implemented packages.
No runtime source files were changed.

### 2026-09-02T18:28:19Z - Scheduler and CLI targets deferred in platform plan

Updated the canonical platform runtime implementation plan with a dedicated
deferred milestone for scheduler and product/operator CLI targets. It records
their different trigger models, layer ownership, authority and tenant-safety
requirements, target composition and deployment prerequisites, acceptance
proof, and explicit non-goals. No runtime source files or cloud resources were
changed.

### 2026-09-02T18:44:29Z - Platform security boundary studied

Added the next handbook lesson at the slower teaching pace. It separates the
provider-neutral security mechanisms (authentication hook, JWT/JWKS
verification, claim-to-permission mapping, CORS, headers, rate limiting, and
stable failure shapes) from app/product tenant, group, role, region, and
resource policy. It also records the current single-file responsibility map as
study material only; no source files were moved or runtime behaviour changed.

### 2026-09-02T19:02:58Z - Package documentation policy codified

Created the product-wide package documentation source material and its
canonical concern rule. Core, platform, and app layer rules now reference that
single policy rather than carrying competing README conventions. The change
also includes accepted source-review and derivation records, an active source
projection, refreshed recognition sources, and a passing retrieval selector
fixture. The policy applies to new and materially reorganised package
boundaries; it deliberately does not claim a completed repository-wide README
rollout.

### 2026-09-02T19:10:26Z - JWT authentication path studied

Added the next handbook lesson at the slower teaching pace. It traces bearer
extraction, JWT shape, signing-key lookup, signature verification, issuer and
purpose checks, time and subject checks, provider-neutral authentication
results, and core-principal creation. It distinguishes generic JWT mechanics
from Cognito adapter facts, and records the current difference between an
invalid token (generic 401) and a JWKS dependency failure (outer safe 500
path). No runtime source files were changed.

### 2026-09-02T19:20:08Z - JWT signature and permission mapping studied

Extended the JWT lesson with a first-time-learner illustration of private
signing keys, public JWKS keys, `kid`, exact-token-content verification, and
key rotation. Added the next lesson on claims-to-permissions mapping: provider
claims translate through target configuration into stable route permissions,
while tenant and resource policy remain later decisions. It also records the
startup-time configured-permission validation and the valid-identity `403`
path. No runtime source files were changed.

### 2026-09-02T21:55:47Z - Browser boundary and request-pressure security studied

Added the next handbook lesson at the slower teaching pace. It separates exact
origin CORS, JSON API security headers, and the current in-memory rate-limit
baseline from authentication, authorization, TLS, and distributed availability
controls. It also records current boundaries: no explicit `OPTIONS` preflight
handling, rate limiting before authentication, and per-process counters. No
runtime source files were changed.

### 2026-09-02T22:11:33Z - Untrusted-input and bounded-agent safety policy codified

Created a product-wide, source-reviewed concern for code-injection resistance
and bounded agent capabilities. It establishes untrusted-content treatment,
typed execution boundaries, least-privilege tools, independent tool-side
authorization, permission-scoped retrieval, consequential-action approval, and
adversarial proof requirements. Added the focused product workflow, core/
platform/app layer references, source projection, review and derivation
records, retrieval fixture, and refreshed recognition coverage. This is a
governance and proof slice only; it does not claim a general agent runtime,
approval service, static scanner, or provider implementation.

### 2026-09-02T23:12:46Z - Security assessment depth studied

Added one deliberately small handbook lesson to clarify when changes need a
baseline check, a focused security assessment, or a deep assessment. The
lesson uses trust boundaries and blast radius rather than changed-line count,
and applies the distinction to Bill's invoice route, bulk export, and future
dead-letter remediation agent. No runtime source files were changed.

### 2026-09-02T23:26:42Z - Focused security assessment studied

Added one short handbook lesson defining the reusable five-part focused
security assessment: change, risk, controls, proof, and outcome. It uses a
single invoice-read route to distinguish a permitted happy path from the
required denial proof, without revisiting unrelated shared controls. No runtime
source files were changed.

### 2026-09-02T23:37:19Z - Security assessment lifecycle studied

Added one handbook lesson showing when assessment questions are asked, how
answers are tied to controls and independently checked evidence, and why policy,
per-change evidence, repository posture, and runtime audit events must remain
separate records. It marks the assessment schema, durable evidence store, and
generated posture index as planned rather than implemented. No runtime source
files were changed.

### 2026-09-03T12:14:18Z - Focused assessment record studied

Added one handbook lesson that walks through a focused security-assessment
record for Bill's invoice-export feature. It explains each record field, the
reviewer's evidence-led questions, the relationship between permission and
resource scope, and why the record cannot itself guarantee security. No
runtime source files were changed.

### 2026-09-03T13:21:52Z - Security review-depth triage studied

Added one handbook lesson on how an author proposes assessment depth, defined
signals set a predictable minimum, and an independent reviewer confirms or
raises the decision. It makes the feature-builder classifier and merge gates
explicitly future work while retaining the current bounded-agent workflow's
focused triggers. No runtime source files were changed.

### 2026-09-04T15:47:46Z - Security records studied

Added one handbook lesson separating security logs, formal audit events, and
operational observability. It uses Bill's invoice export to show their distinct
questions, audiences, and data-minimisation needs, while explicitly marking the
full audit and observability implementation as future platform work. No runtime
source files were changed.

### 2026-09-04T15:52:10Z - Security record ownership clarified

Extended the handbook lesson with the platform ownership map: Core contracts,
platform observability and future audit runtime, provider adapters, deployment
resources, and app-owned product decisions. It explicitly avoids collapsing
audit, logging, security, and diagnostics into one module. No runtime source
files were changed.

### 2026-09-04T15:56:13Z - Security record implementation boundary corrected

Corrected the handbook after distinguishing existing contracts and helper
functions from absent runtime record emitters, durable audit storage, and
provider adapters. The revised map gives distinct future writing paths for
security logs, audit events, and operational records; it also records that
Core diagnostics is vocabulary, not a platform diagnostic service. No runtime
source files were changed.

### 2026-09-04T15:56:13Z - Deferred security record pipelines planned

Updated the platform runtime implementation plan with a deliberately deferred
security-record pipeline milestone. It distinguishes current security
decisions, audit contracts, operational helpers, and diagnostic vocabulary from
their missing emitters, recorders, provider adapters, durable stores, and
infrastructure resources. The plan captures ownership, non-goals, preconditions,
and acceptance criteria for a future bounded vertical slice; no runtime code,
provider, or infrastructure resource was selected or created.

### 2026-09-04T16:11:59Z - Multi-channel feature-harness direction recorded

Updated the product-harness foundation plan so the current web/API-oriented
pipeline is explicitly a first consumer rather than a universal feature shape.
The plan now requires future web, chat, and voice channels to consume the same
capability, identity, tenant, authorization, validation, audit, and
consequence-control boundary. It records chat/voice as planning-only and
defers all provider, session, transcript/audio, retention/residency, and
repository-layout decisions until a bounded first consumer is selected. No
runtime code, provider, or infrastructure resource was selected or created.

### 2026-09-04T16:24:36Z - Audit-integrity lesson studied

Added one handbook lesson explaining append-oriented audit history,
tamper-resistant versus tamper-evident controls, corrections as new accountable
facts, and the distinction between Git/change history, ordinary operational
logs, and a future durable runtime audit store. No runtime source files were
changed.

### 2026-09-04T16:39:58Z - Audit tamper-proofing explained

Extended the audit lesson with the layered practical model for detecting and
resisting tampering: separate access, immutable retention, hashes, signatures,
chained or externally anchored digests, and scheduled verification. It
explicitly records why a hash stored next to an event is insufficient. No
runtime source files were changed.

### 2026-09-04T16:41:25Z - Audit integrity and blockchain distinguished

Added a handbook comparison clarifying that signed audit-integrity chains use a
blockchain-like hash-linking technique but do not require distributed consensus,
cryptocurrency, proof-of-work, or a public ledger. No runtime source files were
changed.

### 2026-09-04T16:53:33Z - Audit-policy lesson studied

Added one handbook lesson on selecting meaningful accountable actions without
turning audit into indiscriminate telemetry. It covers the risk-based test,
Bill's invoice examples, product/tenant/platform ownership, and the distinction
between successful, denied, and ordinary operational actions. No runtime source
files were changed.

### 2026-09-04T20:15:28Z - Audit retention clarified

Extended the audit-integrity lesson to distinguish durable from permanent
retention. It records policy-controlled retention by record class, purpose,
access, region, expiry operation, and legal hold rather than assuming a fixed
two-week or perpetual period. No runtime source files were changed.

### 2026-09-04T20:18:22Z - Denied and failed action records studied

Added one handbook lesson on deciding independently whether a denied or failed
action needs audit evidence, a security signal, operational telemetry, more
than one of these, or no durable individual record. It uses four invoice-export
cases and records the missing current runtime emitters explicitly. No runtime
source files were changed.

### 2026-09-04T20:33:34Z - Audit data minimisation studied

Added one handbook lesson on retaining enough accountability context without
turning audit into a duplicate sensitive-data store. It identifies safe export
facts, prohibited default metadata, pre-storage minimisation, ownership, and
the current unimplemented field-taxonomy/recorder boundary. No runtime source
files were changed.

### 2026-09-04T20:44:12Z - Unsafe audit values explained

Extended the audit-data-minimisation lesson with the individual risk and safer
alternative for credentials, invoice/customer data, raw request/response bodies,
diagnostic payloads, chat/voice content, and signed download URLs. No runtime
source files were changed.

### 2026-09-04T20:57:10Z - Standard audit-event profiles explained

Extended the handbook with the proposed reusable standard: fixed audit envelope
plus a small versioned action profile that allowlists additional facts. It
records field-level purpose, classification, bounds, and validation before
persistence, and marks the profile registry/unknown-key rejection as future
platform work. No runtime source files were changed.

### 2026-09-04T21:01:23Z - Capability record profiles separated

Extended the handbook to distinguish per-capability audit, operational
observability, and security-log profiles. It records that they share only safe
stable references for correlation and must not copy full durable audit metadata
into logs or metrics. No runtime source files were changed.

### 2026-09-04T21:05:14Z - Audit actor and target anchors studied

Added one handbook lesson grounded in the current Core audit contract. It
explains actor types, bounded target/parent-target choices, tenant and scope
context, bulk-action representation, and why delegated agent/worker authority
needs an explicit future contract rather than unstructured metadata. No runtime
source files were changed.

### 2026-09-04T21:41:19Z - Proposed audit taxonomy studied

Added a handbook proposal for a versioned audit taxonomy: app/resource/verb
event types, Core actor and outcome values, separate interaction and execution
dimensions, target context, and a controlled verb vocabulary. The proposal is
explicitly not yet a repository rule or runtime validator. No runtime source
files were changed.

### 2026-09-04T22:06:23Z - Deferred record-pipeline plan reconciled

Reconciled the deferred security, audit, and operational-record milestone with
the completed lessons. The plan now requires a minimum provider-neutral
observability seam before security signals emit; separate audit, operational,
and security profiles per capability; fixed audit envelopes with versioned
allowlisted action profiles; explicit tenant, target, delegation, and taxonomy
decisions; and risk-appropriate integrity-verification and retention schedules.
Chat and voice interaction design remains owned by the product-harness plan;
this platform milestone records only safe optional audit dimensions. No runtime
code, provider, or infrastructure resource was selected or created.

### 2026-09-04T22:08:21Z - Correlation and causation studied

Added the next handbook lesson, using Bill's queued invoice export to separate
one logical workflow from each direct parent-child record relationship. It
clarifies retries, delivery attempts, and idempotency; distinguishes tracing
from authority; and records the current implementation boundary: Core events
and queue messages name both IDs, while the worker currently propagates only
the queue message's correlation ID into its job context. The deferred
record-pipeline plan now requires governed correlation/causation propagation
and proof when a real consumer needs it. No runtime code was changed.

### 2026-09-04T22:10:45Z - Retry causation clarified

Extended the correlation-and-causation lesson to show a failed delivery attempt
causing a retry-scheduled record, which then causes the next attempt. It keeps
the logical workflow correlation, queue-message identity, direct causal parent,
and idempotency decision distinct. No runtime source files were changed.

### 2026-09-04T22:14:38Z - Learning-to-plan triage rule established

Updated the handbook continuation protocol and session decisions so an
architectural rule, clarification, boundary, ownership decision, or deferred
obligation from a lesson cannot live only in the handbook/session log. Each
such item now updates its owning implementation or architecture plan in the
same learning chunk, or records an explicit no-plan-change rationale; a missing
plan owner is surfaced rather than invented. Applied the rule to retry
causation: the platform worker-shell acceptance now requires stable workflow
correlation, distinct delivery attempts, and a direct prior-failure link for
emitted retry facts. No runtime source files were changed.

### 2026-09-04T22:28:54Z - Worker reliability distinctions studied

Added the retry, delivery-attempt, and idempotency lesson to the handbook. It
uses a lost provider response during Bill's export to show why retry protects
against lost work while idempotency protects against duplicate effects. Planning
triage identified a new future-worker requirement, which is now in the platform
runtime plan: jobs with repeatable external effects must define their scoped
idempotency key, durable state/claim, concurrent-worker behaviour,
expiry/reconciliation, and atomicity boundary. The current in-memory
post-success hook is explicitly not presented as exactly-once processing. No
runtime source files were changed.

### 2026-09-04T22:34:29Z - Platform contracts refresher studied

Added a handbook refresher defining `platform/contracts` as the stable app-to-
platform integration socket. It separates portable Core vocabulary, app-facing
contract declarations, generic runtime mechanics, and app-owned product
meaning; it also explains why topic grouping must precede the source-file
split. Planning triage: no plan change, because this confirms the existing
public-mount and contract-boundary direction rather than creating a new
obligation. No runtime source files were changed.

### 2026-09-04T22:41:54Z - Capability declaration gap planned

Answered the distinction between current app runtime registrations and the
broader information a real capability needs to declare. The product-harness
plan now includes a deferred, versioned capability-declaration profile: stable
purpose and ownership; references to schemas, interfaces, policies, data, and
dependencies; separate safe audit/security/observability profiles; and bounded
non-authoritative LLM/agent discovery metadata. It deliberately leaves exact
file location and schema to a first real consumer, and does not expand generic
`platform/contracts` into product-policy storage. No runtime source files were
changed.

### 2026-09-04T22:52:16Z - Capability record-profile linkage clarified

Revisited the earlier audit/security/operational record discussion and closed a
product-harness gap: a future capability declaration must reference separate
record profiles whose field allowlists also state purpose, data classification,
permitted values, bounds/cardinality, audience, and retention/residency
justification. This complements the existing platform record-pipeline plan;
the capability declares approved use, while the future platform validates and
writes the records. No runtime source files were changed.

### 2026-09-04T22:59:55Z - Platform contract topic map confirmed

Inspected the current 565-line `platform/contracts` public entry point and
confirmed its natural source topics: errors, identifiers, feature flags,
contexts, routes, jobs, app mounting/registration, and validation. The
platform-runtime plan now records the file map, one-way dependency direction,
barrel-only public import rule, and compatibility/README proof required for the
later split. No source file has moved or changed behaviour.

### 2026-09-04T23:02:26Z - Platform contract boundary clarified

Clarified that the `platform/contracts` topic map describes current
app-to-runtime registrations rather than every architecture concern discussed
in the session. The platform plan now explicitly keeps Core vocabulary,
security/audit/operational record pipelines, future capability declarations and
LLM discovery metadata, tenant/product policy, and provider/infrastructure
choices in their owning layers. No source file has moved or changed behaviour.

### 2026-09-04T23:13:57Z - Platform contracts source split implemented

Completed the Milestone 2 source-organisation slice in
`platform/contracts`. The existing public package import remains
`@kanbien/platform-contracts`; `src/index.ts` is now a deliberate barrel over
the error, identifier, flag, context, route, job, app-mount, and validation
topics. No app, provider, deployment, or public contract behaviour changed.

Updated `platform/contracts/README.md` with the responsibility map and
verification route, and added the concise local `platform/contracts/src/README.md`
source map required for the multi-file capability module. Updated the owning
platform-runtime plan to record the implemented source-organisation status.
`npm run platform:contracts:check`
passed (type check, declaration build, runtime tests, and import-boundary
test); `git diff --check` passed. Header metadata validation is recorded after
the final documentation update: it passed for 829 artifacts. No ADR is needed: this implements the existing
source-organisation decision without changing the platform boundary.

### 2026-09-05T00:33:30Z - Platform contracts source map expanded

Expanded `platform/contracts/src/README.md` after its summary table with
learner-focused descriptions, responsibility boundaries, and fully annotated
TypeScript illustrations for every topic file. No plan change is required:
this explains the already implemented source organisation and existing public
contract rather than adding a new responsibility, rule, or deferred obligation.
No runtime source or public API changed.

### 2026-09-05T00:53:34Z - Startup registry and compatibility boundary clarified

Clarified that each future server or worker process builds and validates its
own registry during startup; an invalid registry blocks the new process from
becoming ready rather than mutating a running process. The platform-runtime
plan now distinguishes this process-integrity check from deployment-owned
traffic retention, health-based cutover, and rollback. It also records the
required cross-version migration sequence for contract values: add compatible
acceptance, deploy dual-capable consumers, produce/grant the new form, migrate
callers or mappings, confirm old-form inactivity, and retire the old form
deliberately. Added the corresponding handbook lesson. `git diff --check` and
artifact metadata validation passed; no runtime source or public API changed.

### 2026-09-05T01:28:11Z - Registry namespace-test gap recorded

Inspected the current repository before answering whether namespace tests are
needed. `platform/runtime` already has the runtime registry and tests for
duplicate registrations and unknown route permissions; `platform/testing`
already supplies a matching fake registry and mounted-app test seam. Neither
currently carries the mounting app identity into registrations, so namespace
ownership is neither enforced nor tested. The platform-runtime plan and
handbook now require a later test-first slice for own-namespace route/job/health
registrations, rejected cross-app registrations, preserved duplicates, and an
explicit legacy-permission compatibility decision. Feature flags are not yet
app registrations in the current contract, so they are intentionally outside
this specific test requirement. `git diff --check` and artifact metadata
validation passed; no runtime source or public API changed.

### 2026-09-05T01:33:12Z - Permission migration worked example recorded

Inspected the current permission uses and added a handbook walkthrough of
changing the smoke app's `smoke:read` value to the app-owned target form
`platform-smoke.smoke:read`. The migration inventory includes app declaration,
route requirement, manifest, provider claim/group mappings, tests, and future
product grants or policy references. It also records that route permission
lists are all-required, so listing old and new values would not create an
either/or compatibility alias. No plan change is required: the existing
platform-runtime plan already owns the migration sequence, while the exact
temporary dual-granting or future alias policy depends on a later approved
real-world migration. No runtime source or public API changed.

### 2026-09-05T01:55:54Z - App-namespace enforcement and migration implemented

Implemented the planned compatibility-preserving registry slice. Runtime and
test registries now expose `forApp(appId)` and pass that scoped view to every
app mount. Permission, route, job, and health registrations must begin with
the mounting app ID and otherwise return the stable
`PLATFORM_CONTRACT_NAMESPACE_MISMATCH` contract error. Global duplicate checks
remain intact. Runtime and test-helper contract tests prove accepted owned
registrations, rejected foreign registrations, and a collision between two
correctly named apps.

Migrated the current platform-smoke declaration and affected fixtures from
`smoke:read` to `platform-smoke.smoke:read` (with fixture-local app IDs where
appropriate). This repository has no deployed authorization mapping, durable
grant data, or old/new process overlap, so it deliberately has no temporary
legacy alias. The platform-runtime plan and handbook now record that direct
local-migration decision while retaining the governed compatibility sequence
for a future live migration. The smoke authentication fixture was also brought
up to the current complete-principal contract so its forbidden-path assertion
reaches authorization rather than failing at authentication.

Added or updated package READMEs for `platform/runtime`, `platform/testing`,
and `apps/platform-smoke`, plus the nearest contracts documentation, so the
scoped-mount boundary and verification routes remain discoverable. Verified:
`npm run platform:contracts:test`, `npm run platform:runtime:check`,
`npm run platform:testing:check`, `npm run platform:server:check`,
`npm run platform:adapter:aws:auth:cognito:check`, and
`npm run app:platform-smoke:check`. Final `git diff --check` and
`bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
also passed (829 artifacts). No ADR is required: this implements the existing
runtime-plan decision rather than changing the approved platform boundary.

### 2026-09-05T02:01:00Z - Security source-organisation status clarified

Confirmed the distinction between two layers that share the word “security.”
`packages/core/src/security/` is already split into classification, secrets,
hashing, and policy topics behind its public barrel. In contrast,
`platform/security/src/index.ts` remains a single 663-line provider-neutral
mechanism module for authentication, JWT/JWKS verification, permission mapping,
CORS/security headers, and rate limiting. Its structural refactor was deferred
to avoid moving security-sensitive behaviour before its seams and test baseline
were understood; it was not forgotten or completed incidentally by the
contracts refactor.

The platform-runtime plan and handbook now make a focused,
behaviour-preserving `platform/security` organisation slice the next structural
candidate before queue-adapter work. It must preserve the public package
import and current behaviour, prove the moved topics with type/runtime/boundary
tests, and add the nearest package/source documentation. No platform-security
source or security decision changed in this clarification.

### 2026-09-05T13:56:03Z - Platform security source organisation implemented

Implemented the deferred, behaviour-preserving `platform/security` source
split. The unchanged `@kanbien/platform-security` barrel now deliberately
exports six focused topics: `errors.ts`, `authentication.ts`, `jwt.ts`,
`authorization.ts`, `headers.ts`, and `rate-limiting.ts`. JWT/JWKS parsing and
verification remain together; authentication composes JWT verification and
claim-to-permission mapping; rate limiting reuses internal header parsing
without exposing that helper as a new public API. No provider identity system,
product authorization policy, JWT algorithm, CORS rule, or rate-limit
semantics changed.

Added the required `platform/security` package README and local source map,
then updated the platform-runtime plan and handbook to distinguish implemented
Core vocabulary organisation from implemented platform-mechanism organisation.
The baseline and final `npm run platform:security:check` both passed; the final
boundary check covers seven source files. Dependent public-barrel consumers
also passed: `npm run platform:server:check`,
`npm run platform:adapter:aws:auth:cognito:check`, and
`npm run app:platform-smoke:check`. No ADR is required: this preserves an
existing public package boundary and behaviour rather than adopting a new
architecture or security control. Final `git diff --check` and
`bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
also passed (829 artifacts).

### 2026-09-05T14:01:22Z - Platform security source guide expanded

Expanded `platform/security/src/README.md` after its summary table with a
learner-focused guide to every topic file. It now explains each file’s
responsibility, its boundary, the security misconception it prevents, and how
the files cooperate without making internal helpers public. No plan change is
required: this documents the just-implemented source organisation without
altering its responsibility, public API, or runtime behaviour. `git diff
--check` passed.

### 2026-09-05T14:42:32Z - Platform runtime source organisation implemented

Implemented the behaviour-preserving `platform/runtime` source split. The
unchanged `@kanbien/platform-runtime` barrel now deliberately exports focused
`errors.ts`, `registry.ts`, `contexts.ts`, and `lifecycle.ts` topics.
They separately own runtime failure vocabulary, full-catalogue registration and
mounting, request/job context construction, and ordered process lifecycle
control. The runtime remains provider-neutral: it does not add a server,
worker delivery loop, queue provider, global registry, lifecycle phase, or app
service container.

Added the required package responsibility map and local source guide, then
updated the platform-runtime plan and printable handbook. The plan records the
source split as an implemented navigation improvement and explicitly protects
the public barrel and the separation from target/provider/product changes. No
ADR is required because the existing public API and architecture are preserved.

The complete checks passed: `npm run platform:runtime:check` (type, build,
runtime, and boundary proofs), `npm run platform:server:check`, `npm run
platform:workers:check`, and `npm run app:platform-smoke:check`. Final
repository hygiene checks follow this entry.


### 2026-09-05T14:54:50Z - Context hygiene

Summary: Four reviewable commits are planned: policy/evidence; contracts plus runtime registry namespace enforcement and source organisation; security source organisation; and the architecture learning/planning record. Generated rulebook outputs remain with their governing sources. The runtime split is coupled to the namespace migration because its registry is the enforcement boundary.

Durable evidence: The checked source, tests, package maps, plan, handbook, and session log in this chat-owned worktree are the durable evidence; no provider, deployment, or product behaviour was added.


### 2026-09-05T15:03:29Z - Commit recorded

Commit: `57f716e`

Message: docs(product): govern package docs and untrusted input

Summary: Codified the package documentation and untrusted-input/bounded-agent safety policies with their source material, review records, derivation reports, retrieval fixtures, projections, and generated recognition sources.

ADR impact: No ADR: the commit operationalizes existing layer boundaries and governance rather than introducing a new runtime architecture.


### 2026-09-05T15:12:19Z - Commit recorded

Commit: `7c1b66b`

Message: refactor(platform): organize contracts and runtime registry

Summary: Organized app-facing contracts and provider-neutral runtime responsibilities behind stable barrels, enforced app-owned registration namespaces, migrated consumer permission examples, and added focused contract, runtime, testing, server, Cognito, and smoke-app proof.

ADR impact: No ADR: this preserves existing package boundaries while applying the already-recorded source-organisation and semantic namespace direction.


### 2026-09-05T15:19:33Z - Commit recorded

Commit: `174421b`

Message: refactor(platform): organize security mechanisms

Summary: Separated platform security failures, authentication, JWT verification, authorization mapping, headers, and rate limiting behind the unchanged public barrel, with local package/source guides and passing security, server, Cognito, and smoke-app proof.

ADR impact: No ADR: the change preserves existing security mechanism behaviour and public imports; it does not select a provider or introduce a new security control.


### 2026-09-05T15:26:15Z - Commit recorded

Commit: `19f14c4`

Message: docs(architecture): record platform learning direction

Summary: Recorded the product-harness foundation, platform implementation follow-ups, printable learning handbook, and durable session evidence for security, audit, contracts, runtime, workers, adapters, and source organisation decisions.

ADR impact: No ADR: the documentation records existing implementation slices and deferred directions; it does not adopt a new cross-layer runtime architecture.

### 2026-09-05T16:07:18Z - Public navigation and addressing direction recorded

Recorded the learner's clarified public-navigation model in the product-harness
foundation plan and printable handbook. Stable outward-facing product areas,
concepts, resources, views, and workflow steps may form public browser paths;
they are not implementation leaks merely because apps/modules implement them
behind the scenes. The plan now distinguishes public navigation addresses,
backend API routes, and shared capabilities; assigns namespace ownership to
product composition; reserves hosts/DNS/TLS for deployment; and defers concrete
tenant-addressing, hostname, router, and declaration-schema choices until the
first real web consumer.

No runtime, frontend, API, or deployment behaviour changed. The future web
playbook must define the versioned navigation declaration, collision and
reserved-path validation, safe query/identifier rules, redirect compatibility,
tenant-addressing model, and proof that navigation cannot bypass shared
identity, tenant, authorization, validation, confirmation, audit, or
consequence controls. No ADR is required: this refines the already deferred
capability-first channel direction without adopting a concrete web architecture.

### 2026-09-05T16:09:11Z - Platform server request-envelope lesson recorded

Added the first request-time server lesson to the handbook. It traces the
current early pipeline: request/correlation ID, bounded request outcome
logging, exact-origin CORS, security headers, rate limiting, and the early
health-endpoint branch before ordinary authentication and app-handler work.
It distinguishes the in-memory test handle from the Node HTTP adapter and
records why early rate limiting protects downstream identity and application
capacity. No plan change is required: this lesson explains the already
implemented server pipeline without altering its ownership, public contract,
or behaviour.

### 2026-09-05T16:14:08Z - Platform server identity, permission, and tenant lesson recorded

Added the next server-pipeline lesson to the handbook. It separates route
matching from access, 401 authentication failure from 403 broad-permission
denial, trusted tenant resolution from caller-provided URL facts, and later
resource-policy authorization. It records the current fail-closed startup
guard for routes requiring a tenant resolver, as well as the proof that a
broad permission denial does not invoke tenant, resource, or app-handler work.
No plan change is required: this teaches existing provider-neutral sequencing
and introduces no tenant model, role/group policy engine, or route contract.

### 2026-09-05T16:20:07Z - Platform server validation and resource-policy lesson recorded

Added the final request-time server lesson to the handbook. It distinguishes
boundary request validation from business validation, resource resolution from
authorization, deliberate 403 versus 404 disclosure, app-handler invocation,
safe 500 mapping, and the common bounded finish record. No plan change is
required: it explains existing contract and platform seams without implementing
a live product policy engine, audit pipeline, or new runtime behaviour.

### 2026-09-05T17:19:35Z - HTTP transport hardening implemented and recorded

Implemented the provider-neutral HTTP transport hardening identified during
the server review. `platform/server` now separates route policy from raw Node
transport adaptation: it validates transport configuration, rejects unknown
methods rather than defaulting them to GET, rate-limits before body parsing,
bounds headers/bodies/time/concurrency/connections, accepts non-empty JSON
bodies only with a JSON media type, maps malformed input through safe response
handling, and propagates cancellation into the request context. It explicitly
handles CORS preflight and `Vary: Origin`, generates valid request IDs, preserves
valid upstream IDs, prevents app headers from replacing platform-owned headers,
and drains listener work after lifecycle readiness becomes false.

A follow-up listener-level edge-case test found and closed a timeout accounting
hole during the same slice: when a handler ignores cancellation after a 504,
it now retains its in-flight concurrency slot until it actually settles. This
prevents repeated timeouts from bypassing the configured concurrency bound.

The in-memory rate limiter now bounds its keyspace and uses only a supplied
client address, hashed bearer token, or verified principal key. The generic
Node listener deliberately refuses to trust caller-controlled forwarded-address
headers. `platform/observability` no longer emits arbitrary `Error.message`
content in its normalized error shape, avoiding a common diagnostic data leak.

Corrected Milestone 5: a target/product composition entrypoint—not a
non-existent `platform/server/mount.ts`—imports the chosen public app modules
and provider adapters. Added server package/source maps and Handbook Lesson 48
to explain the transport gate in small teaching steps. The implementation plan,
Kanbien staging target profile, and readiness verifier now make a shared
rate-limit adapter, trusted-ingress client-address policy, target transport
limits, and edge protection mandatory evidence before an internet-facing target
may become ready. The readiness manifest remains deliberately blocked and now
records this as its eighth explicit blocker.

Validation passed: `platform:server:typecheck`, `platform:server:build`,
`platform:server:boundary`, elevated local-listener `platform:server:test`,
`platform:security:check`, `platform:observability:check`,
`platform:runtime:check`, `platform:server:image-build`,
`app:platform-smoke:check`, `product:kanbien-platform:check`, blocked-mode
deploy-readiness validation, and `git diff --check`. The product runtime test
also exposed and corrected a fake authenticated subject that omitted the
complete principal facts now correctly required by the server. Local Docker
image smoke could not run because the Docker daemon is unavailable; no image
was published and no cloud, DNS, secret, or deployment state was changed.

ADR impact: No ADR. The slice implements bounded provider-neutral server
mechanics and corrects plan/target readiness evidence. It deliberately does
not select a shared limiter provider, a proxy trust list, an edge/WAF product,
or infrastructure resources; those require a separate target/adapter decision.

### 2026-09-05T20:08:51Z - Target composition scope clarified for the learning record

Recorded the next architecture-learning clarification in the handbook and the
Platform Runtime Implementation Plan. A target composition entrypoint is an
accountability and assembly point for all target-selected capabilities, not an
authentication-only file. The plan now requires a visible capability inventory
for the port/contract, selected adapter or host delivery, composition owner,
infrastructure resource, failure behaviour, and readiness evidence.

The inventory explicitly distinguishes current Cognito selection from gaps
that remain intentionally unselected: external observability/audit delivery,
shared rate limiting and trusted ingress address resolution, queue provider,
and secrets-management delivery. It also records that infrastructure-hosted
facilities such as stdout collection or secret injection need not be forced
into empty TypeScript adapter packages, but must still have an explicit target
decision and evidence. No runtime behaviour changed; no validation beyond the
documentation integrity check is required for this clarification.

### 2026-09-05T20:26:32Z - Cognito operational readiness made explicit

Recorded the distinction between the implemented Cognito adapter and the
operating model required to expose it publicly. The adapter verifies expected
Cognito access tokens and translates approved claims into provider-neutral
facts. Target-profile, readiness, infrastructure, and runbook work must still
govern identity model and ownership, credential/key lifecycle and recovery,
token/JWKS failure behaviour, authorisation-change review, ingress and abuse
controls, safe audit/monitoring, deployed protected-route smoke, and rollback
evidence.

The record also makes clear that the current target is machine-to-machine; it
does not yet implement human tenant/group/resource authorisation such as the
earlier Bill/Benelux example. The existing platform-runtime plan already owns
the relevant readiness milestone, so this clarification extends that plan
rather than creating a separate identity plan. No runtime behaviour changed;
documentation integrity validation remains the appropriate check.

### 2026-09-05T20:48:32Z - Production reference target baseline created from user requirements

Created `.agentic/03.product/plans/implementation/production-reference-target-baseline.md`
as the authoritative completeness map for the first public production Entity
Builder target: AWS ECS Fargate in `eu-west-1`; API-first with image/document
and bulk-transfer support; later agent workflow; full human tenant/group/resource
authorisation; sensitive personal/medical data expectation; EU/UK residency;
hundreds of concurrent users; and a cost-aware single-operator beginning.

The baseline separates first-release requirements from the architectural need
for web, desktop, mobile, tablet, chat, and voice to use the same governed
capability path. It records required capability maturity states from
requirements through operational proof, current evidence, completion gates,
and the explicit decisions still needed before provider/infrastructure
selection. The platform-runtime and product-harness plans now link to this
baseline, preventing local proof from being described as a production default.
No AWS mutation, production target relabelling, cloud resource selection, or
runtime code change occurred. The existing Kanbien staging scaffold remains
planning-only and distinct from a future production target.

### 2026-09-05T20:56:32Z - Multi-tenant root-approval and residency decisions recorded

Updated the production reference target baseline from the user's next decision
set. The first real product is multi-tenant. The first `PlatformRoot` is
securely bootstrapped and root identities are invite-only; self-service
admin/app-user signup creates an inactive request until a verified root grants
approval. The decision explicitly keeps root approval distinct from automatic
read access to every tenant's business data.

Each tenant now has an EU or UK residency home and cross-boundary processing is
denied by default. `eu-west-1` is the initial EU target, so UK-residency
onboarding requires a separately planned/proven UK target covering all
residency-inheriting stores and processing paths. If cost requires it, an
explicit EU-only launch may refuse UK-residency tenants; cost is not an
unrecorded reason to place UK-residency data in the EU target. No cloud service,
provider, or concrete UK region was selected, and no AWS mutation occurred.

### 2026-09-05T21:04:52Z - Initial EU-only launch and administrative scopes recorded

Updated the production reference target baseline with the user's decision to
launch EU-only initially. The `eu-west-1` target must reject UK-residency
onboarding until a separately planned and proven UK-residency target exists.

Recorded three product-level role concepts with non-interchangeable scopes:
`PlatformRoot` administers tenants and tenant roots; `TenantRoot` administers
only its verified tenant's app users and tenant administration; and
`TenantAppUser` consumes authorised tenant business capabilities. The baseline
expressly rejects implied upward privilege escalation and keeps the initial
self-service approval gate with `PlatformRoot`. Whether/when a tenant root may
approve app-user requests is an explicit remaining policy decision. No runtime
code, provider selection, or AWS state changed.

### 2026-09-05T21:10:23Z - Hierarchical approval policy clarified

Recorded the user's parent-scope approval rule in the production reference
target baseline. `PlatformRoot` directly creates/approves a tenant and its
tenant root; `TenantRoot` directly creates/approves a tenant app user. Direct
creation by the authorised immediate parent is implicit approval and must be
audited as one `created-and-approved` action. A self-service request remains
pending until the same parent scope approves it.

The record adds the necessary non-escalation condition: creation counts as
approval only when the actor already holds the explicit management permission
at that parent scope. A normal tenant app user cannot acquire approval power by
calling a create-user endpoint or submitting a chat/voice instruction. No
runtime code, provider selection, or AWS state changed.

### 2026-09-05T21:32:11Z - Initial no-MFA posture and root-recovery migration recorded

Recorded the user's decision that MFA is not required initially for
`PlatformRoot` or `TenantRoot`. The baseline treats this as an explicit
early-stage risk decision, not a production-security recommendation: primary
credential/reset, session, privileged-login rate limit, alerting, and recovery
controls remain visible and MFA must be reconsidered before sensitive-data
onboarding or a changed risk posture.

Root loss recovery is now a governed one-shot replacement-root migration. It
must not be an automatic schema migration, application endpoint, chat/voice
tool, or untracked database edit. The later recovery design must use a protected
invocation path, preconditions, previous-root disposition, idempotence, and
durable audit evidence. No runtime code, provider selection, or AWS state
changed.

### 2026-09-05T21:36:29Z - Email/password initial human sign-in selected

Recorded email/password as the initial human sign-in method in the production
reference target baseline. The existing Cognito machine-to-machine adapter does
not yet prove a human sign-in, verification, reset, session, or approval path,
so the baseline retains email verification, password quality/reuse/breach,
reset, session, privileged-login rate limit, and authentication-alert policy
as explicit required design work while MFA is deferred. No runtime code,
provider selection, or AWS state changed.

### 2026-09-05T21:42:10Z - Mandatory email verification and reset-link policy recorded

Recorded mandatory email verification before a self-service signup can enter
the pending approval workflow. Password reset also uses an email link, but the
baseline makes verification and reset separate purpose-bound, one-time,
short-lived credential flows. Link tokens must not enter logs, audit payloads,
analytics, error reports, or referrer-bearing requests, and passwords are never
sent by email. Reset rate limiting, session invalidation, and post-reset
notification remain explicit design decisions. No runtime code, provider
selection, or AWS state changed.

### 2026-09-05T21:44:45Z - Password-reset session revocation recorded

Recorded the initial reset policy: a successful password reset revokes every
prior session for the identity, permits only the newly reset session to
continue, and sends a safe post-reset notification without credential or token
material. This closes the open reset-session-invalidation and notification
decisions while retaining password quality, session-lifetime, login-rate-limit,
and alerting policy as explicit follow-up work. No runtime code, provider
selection, or AWS state changed.

### 2026-09-05T21:48:43Z - Versioned tenant identity-policy model applied

Recorded the user's decision that identity controls should have implemented
defaults and tenant-level configuration. The baseline now applies the existing
versioned-baseline model: `PlatformRoot` owns non-weakenable invariants and
baseline versions; `TenantRoot` may adopt an approved version and configure
stricter tenant requirements. Email verification, purpose-bound reset links,
reset-session revocation, and required audit evidence cannot be disabled by a
tenant setting. Any relaxation requires an explicit time-bound exception with
owner and evidence. Policy changes are scoped, validated, versioned, and
audited without recording credential material. No runtime code, provider
selection, or AWS state changed.

### 2026-09-05T21:56:59Z - Identity security baseline v1 approved

Recorded the approved `identity-security-baseline.v1` in
`.agentic/03.product/standards/`. It fixes the first human identity defaults:
15-character minimum passwords that remain usable with password managers and
Unicode; contextual/breached-password screening; no routine expiry; mandatory
email verification; distinct one-time 15-minute verification/reset links;
server-side session limits; current-password reauthentication for privileged
changes; progressive abuse controls without permanent automatic lockout; and
separate audit, security-signal, and operational-record duties.

The prior reset wording is superseded: a successful reset revokes every active
session and does **not** create an authenticated reset-browser session. The
user must sign in normally with the new password. The policy also records that
medical/special-category data remains gated on a later MFA-capable baseline and
target for applicable privileged roles.

Updated the production-reference and product-harness plans so the active policy
is findable, tenant settings can only tighten it, and the remaining human
identity adapter/policy-resolver work remains explicitly `requirements
captured`. No runtime code, provider selection, AWS state, or production
identity configuration changed.

### 2026-09-05T22:18:10Z - Platform-smoke proof scope restored

Recorded the user's scope correction: current work is to prove the
production-shaped platform layer through `apps/platform-smoke`, not to start a
human identity, identity-and-access, user-profile, tenant-membership,
group-assignment, approval-workflow, or other business/application app.

The smoke app is a bounded integration probe for mounting, startup, health,
configuration, selected machine authentication, request handling, safe
failure, packaging, target deployment, and operational evidence. A successful
smoke deployment proves that narrow platform/deployment slice only; it does
not prove Entity Builder product readiness, human identity, tenant
authorisation, or suitability for personal/medical data.

Updated the production-reference and platform-runtime plans and the printable
handbook to make the immediate scope and the later application boundary
unambiguous. No runtime code, provider configuration, AWS state, or business
application work changed.

### 2026-09-05T22:32:59Z - Staging platform-shell AWS boundary re-inspected

Performed the governed, read-only AWS inspection using profile `kanbien-dev`,
region `eu-west-1`, and the `kanbien-staging` candidate boundary. The shared
cluster, ALB, immutable/scan-on-push `platform-shell` ECR repository, and
machine-to-machine Cognito client/scope exist. The ECR repository has no
images, and there is no platform-shell ECS task definition, ECS service, ALB
target group, hostname/host rule, log group, alarm, deployed smoke proof, or
rollback exercise.

Updated the AWS inventory, readiness manifest, and handbook to distinguish
selected/planned facts from verified live resources. The next bounded
operational task is an AWS change plan for the minimal server-first platform
shell target. It must cover image provenance, ECS/ALB runtime resources,
safe configuration and machine-secret delivery, ingress/rate-limit controls,
log/alarm delivery, rollback, and smoke proof; it must not add business apps,
human identity, or tenant data. No AWS resource, secret, DNS record, image,
or deployment was changed.

### 2026-09-05T22:48:00Z - Existing public-site boundary and 503 diagnosed

After the decision to retain the `kanbien.com` DNS records, performed a
governed, read-only inspection of the public route and its old workload. The
zone's `kanbien.com`, `www.kanbien.com`, and `rag.kanbien.com` A-alias records
point to the shared public ALB. `kanbien.com` redirects to `www.kanbien.com`,
whose default HTTPS route forwards to the legacy `service-platform` target
group. That group had no registered targets: the service wanted one task, but
every recent task exited with code `1` while its startup migration timed out
connecting to PostgreSQL. The corresponding RDS instance reports
`inaccessible-encryption-credentials`; the available Valkey cache does not
make the unavailable database recoverable. This explains the observed `503`.

Recorded the separation of concerns in the production baseline, AWS inventory,
and handbook: retain the public DNS boundary; do not remove or repurpose the
shared ALB, legacy service, target groups, RDS, cache, certificate, or related
access configuration as part of the platform-smoke work; and plan legacy-site
recovery or replacement as its own governed, reversible change. No AWS
resource, DNS record, data, image, or deployment was changed.

### 2026-09-06T00:15:00Z - Platform-smoke staging deployment planning began

Kept the brochure-site recovery separate and inspected the selected
`kanbien/staging` platform-shell boundary for a new smoke workload. The
wildcard certificate can cover `staging.platform.kanbien.com`, but the shared
ALB has no WAF and no shell runtime resources exist. The local target profile
also had two deployment-stopping configuration defects: it mapped the Cognito
scope to `smoke:read` instead of the smoke app's declared
`platform-smoke.smoke:read`, and it omitted the Cognito identifiers required
when `PLATFORM_AUTH_PROVIDER=cognito` is selected.

Added the bounded initial AWS deployment plan and corrected those declarative
target facts. The plan proposes an isolated Fargate workload, dedicated IAM
and network boundary, host-scoped WAF, DynamoDB-backed shared rate limiter,
trusted-ALB client-address resolver, CloudWatch/SNS delivery, repeatable
CloudFormation, immutable-image promotion, and reversible verification. These
are planning decisions only: the current branch remains uncommitted and ahead
of `origin/main`, no AWS resource, DNS record, secret, image, or deployment
was changed, and explicit approval remains required before any cloud apply.

### 2026-09-05T23:32:53Z - Platform-shell deployable-artifact and infrastructure slice completed locally

Continued the bounded platform-smoke deployment work without touching the
separate brochure-site recovery. A strict public-target startup probe exposed a
real packaging defect: the compiled entrypoint resolved the new AWS adapters
through development workspace TypeScript exports. The image payload now compiles
and shims the Cognito, ECS/Fargate trusted-ingress, and DynamoDB shared-rate-limit
adapters; its final Docker stage receives only the generated payload and
production dependencies. The runtime-payload test hides the workspace package
links and starts the compiled target successfully with non-secret staging
configuration. Docker Desktop WSL integration is unavailable, so the actual
container-engine smoke remains honestly blocked.

Added target-specific CloudFormation foundation and service templates. The
foundation creates new platform-shell roles, ALB-only task security group,
DynamoDB rate-limit table, target group, host route, DNS alias, host-scoped WAF,
log group, SNS alarms, and the narrowly scoped service-stack execution role.
The service template accepts an immutable image digest, runs one 256/512 Fargate
task with a read-only filesystem, and selects the reviewed Cognito, DynamoDB,
trusted-ingress, transport, health, and CORS configuration. Static policy
checks, AWS CloudFormation template validation, and AWS Access Analyzer policy
validation passed.

Read-only AWS checks confirmed listener priority `20` was unused, the ALB alias
zone ID is `Z32O12XQLNTSW2`, no regional WAF ACL currently exists, and the live
GitHub deploy role still has its older policy. The repository now contains a
narrower desired policy and workflow; a separately approved IAM policy update
is required before the repeatable GitHub service deployment path can run.

Updated the target profile, readiness manifest, AWS plan, runtime plan, and
handbook together. No AWS resource, IAM policy, DNS record, secret, ECR image,
change set, stack, task definition, or deployment was created or modified.

The review also retained a cost-control blocker: resource tags do not become
cost evidence automatically. The account must activate the `service` cost
allocation tag and prove the scoped monthly/forecast budget after the tagged
foundation resources exist.


### 2026-09-06T11:32:24Z - Commit recorded

Commit: `7324442`

Message: feat(platform): harden server runtime boundary

Summary: Hardened the provider-neutral HTTP boundary with bounded request transport, trusted client-address injection, safe response handling, rate-limit contract improvements, privacy-safe error logging, lifecycle draining, a reviewed identity-security baseline, and focused runtime tests.

ADR impact: No ADR: this implements the already selected platform boundary and security policy; it does not introduce a new durable architecture decision.


### 2026-09-06T11:41:39Z - Commit recorded

Commit: `b767499`

Message: feat(deploy): define AWS platform shell target

Summary: Added Cognito/DynamoDB/ECS target composition, sealed image packaging proof, validated staging CloudFormation foundation and service templates, narrowly scoped deployment workflow and policy definitions, and static deployment/readiness gates. No AWS resources were changed.

ADR impact: No ADR: this implements the already selected ECS Fargate/Cognito production-reference target and records a governed deployment path; it does not change that target decision.


### 2026-09-06T11:45:24Z - Commit recorded

Commit: `bf92725`

Message: docs(platform): record production shell readiness

Summary: Recorded the production-reference target baseline, implementation/deployment planning, AWS read-only inspection evidence, local container smoke proof, printable learning handbook updates, and regenerated artifact discovery index.

ADR impact: No ADR: these records document and operationalize existing decisions; no new architecture decision was made by the documentation checkpoint.

## Sub-Agent Activity

- None recorded yet.

## Commits



- Commit: `86e0c5a`
  Time UTC: 2026-09-01T22:23:13Z
  Message: feat(core): organize security contracts and platform guidance
  Summary: Checkpointed the core security module split, product-harness foundation plan, source-reviewed platform naming standard, and printable architecture handbook before the governed main refresh.
  ADR impact: No new ADR; the naming policy extends an existing platform rule.


- Commit: `57f716e`
  Time UTC: 2026-09-05T15:03:29Z
  Message: docs(product): govern package docs and untrusted input
  Summary: Codified the package documentation and untrusted-input/bounded-agent safety policies with their source material, review records, derivation reports, retrieval fixtures, projections, and generated recognition sources.
  ADR impact: No ADR: the commit operationalizes existing layer boundaries and governance rather than introducing a new runtime architecture.


- Commit: `7c1b66b`
  Time UTC: 2026-09-05T15:12:19Z
  Message: refactor(platform): organize contracts and runtime registry
  Summary: Organized app-facing contracts and provider-neutral runtime responsibilities behind stable barrels, enforced app-owned registration namespaces, migrated consumer permission examples, and added focused contract, runtime, testing, server, Cognito, and smoke-app proof.
  ADR impact: No ADR: this preserves existing package boundaries while applying the already-recorded source-organisation and semantic namespace direction.


- Commit: `174421b`
  Time UTC: 2026-09-05T15:19:33Z
  Message: refactor(platform): organize security mechanisms
  Summary: Separated platform security failures, authentication, JWT verification, authorization mapping, headers, and rate limiting behind the unchanged public barrel, with local package/source guides and passing security, server, Cognito, and smoke-app proof.
  ADR impact: No ADR: the change preserves existing security mechanism behaviour and public imports; it does not select a provider or introduce a new security control.


- Commit: `19f14c4`
  Time UTC: 2026-09-05T15:26:15Z
  Message: docs(architecture): record platform learning direction
  Summary: Recorded the product-harness foundation, platform implementation follow-ups, printable learning handbook, and durable session evidence for security, audit, contracts, runtime, workers, adapters, and source organisation decisions.
  ADR impact: No ADR: the documentation records existing implementation slices and deferred directions; it does not adopt a new cross-layer runtime architecture.


- Commit: `7324442`
  Time UTC: 2026-09-06T11:32:24Z
  Message: feat(platform): harden server runtime boundary
  Summary: Hardened the provider-neutral HTTP boundary with bounded request transport, trusted client-address injection, safe response handling, rate-limit contract improvements, privacy-safe error logging, lifecycle draining, a reviewed identity-security baseline, and focused runtime tests.
  ADR impact: No ADR: this implements the already selected platform boundary and security policy; it does not introduce a new durable architecture decision.


- Commit: `b767499`
  Time UTC: 2026-09-06T11:41:39Z
  Message: feat(deploy): define AWS platform shell target
  Summary: Added Cognito/DynamoDB/ECS target composition, sealed image packaging proof, validated staging CloudFormation foundation and service templates, narrowly scoped deployment workflow and policy definitions, and static deployment/readiness gates. No AWS resources were changed.
  ADR impact: No ADR: this implements the already selected ECS Fargate/Cognito production-reference target and records a governed deployment path; it does not change that target decision.


- Commit: `bf92725`
  Time UTC: 2026-09-06T11:45:24Z
  Message: docs(platform): record production shell readiness
  Summary: Recorded the production-reference target baseline, implementation/deployment planning, AWS read-only inspection evidence, local container smoke proof, printable learning handbook updates, and regenerated artifact discovery index.
  ADR impact: No ADR: these records document and operationalize existing decisions; no new architecture decision was made by the documentation checkpoint.

## Main Refresh Conflicts



- Path: `.agentic/02.rag-rulebook/derivation-reports/03.product.platform/2026-07-07-platform-runtime-enterprise-obligations-v1.yml`
  Type: `normal-repo-conflict`
  Mode: stopped
  Reason: The classifier found authored derivation-report content with concurrent owner-path migration on main and naming-policy additions on the chat branch.
  Action: Stopped before reconciliation; a later approved resolution must retain canonical owner paths and migrate the naming-policy evidence.
  Preflight branch: `agentic/preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-72242f272710/20260901222515`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-72242f272710-20260901222515`
  Files changed by resolution: derivation report; canonical source/rule paths; naming-policy review and claims
  Checks: refresh preflight; classifier


- Path: `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`
  Type: `normal-repo-conflict`
  Mode: stopped
  Reason: The classifier found the generated artifact conflicted because its independently changed source inventories have not yet been reconciled.
  Action: Stopped before regeneration; regenerate only after the source-path and rule-content conflicts are resolved.
  Preflight branch: `agentic/preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-72242f272710/20260901222515`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-72242f272710-20260901222515`
  Files changed by resolution: generated recognition artifact inventory
  Checks: refresh preflight; classifier


- Path: `docs/03.product/rules/platform/layers/platform.yml`
  Type: `normal-repo-conflict`
  Mode: stopped
  Reason: The classifier found authored platform-rule content where main moved the canonical path and the chat branch added a semantic identifier policy to the legacy path.
  Action: Stopped before reconciliation; a later approved resolution must keep the canonical 03.product rule path and migrate the naming-policy rule with refreshed provenance.
  Preflight branch: `agentic/preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-72242f272710/20260901222515`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-72242f272710-20260901222515`
  Files changed by resolution: platform layer rule; source provenance; semantic identifier rule
  Checks: refresh preflight; classifier


- Path: `.agentic/02.rag-rulebook/derivation-reports/03.product.platform/2026-07-07-platform-runtime-enterprise-obligations-v1.yml`
  Type: `normal-repo-conflict`
  Mode: manual
  Reason: Authored derivation evidence and the owner-path migration changed concurrently.
  Action: Kept canonical 03.product paths, migrated semantic-naming claims and review evidence, and validated the reconciled report.
  Preflight branch: `agentic/preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-a7292ed53093/20260901222711`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-a7292ed53093-20260901222711`
  Files changed by resolution: derivation report; source-material review; naming fixture; canonical source and rule references
  Checks: source projections; coverage; source review; derivation report; derived-rule projection; focused selector fixtures


- Path: `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`
  Type: `normal-repo-conflict`
  Mode: manual
  Reason: The generated inventory reflected incompatible pre-migration and owner-aligned artifact sets.
  Action: Resolved source evidence first, then regenerated artifacts.yml and verified it is current.
  Preflight branch: `agentic/preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-a7292ed53093/20260901222711`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-a7292ed53093-20260901222711`
  Files changed by resolution: generated recognition artifact inventory
  Checks: recognition generation; recognition current check; focused selector fixtures


- Path: `docs/03.product/rules/platform/layers/platform.yml`
  Type: `normal-repo-conflict`
  Mode: manual
  Reason: Main moved the rule to its canonical owner path while the chat branch added the semantic identifier policy.
  Action: Kept the canonical 03.product rule, preserved the semantic identifier rule, and refreshed source provenance from the migrated source material.
  Preflight branch: `agentic/preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-a7292ed53093/20260901222711`
  Preflight worktree: `/tmp/agentic-main-refresh-preflight/chat-2026-08-31-01-11-teach-the-architecture-lis-a7292ed53093-20260901222711`
  Files changed by resolution: platform layer rule; canonical source provenance; semantic identifier rule
  Checks: source projections; derived-rule current check; focused selector fixtures

## ADR Disposition

ADR needed: no
ADR path:
Reason: The checkpoint records focused module organisation, an existing-rule
extension, plans, and educational material. The deferred DLQ remediation idea
will be recorded as a future capability with explicit non-goals, not adopted as
an implemented cross-layer architecture decision in this checkpoint.

## Session Metrics

Raised at UTC: 2026-08-31T00:11:19Z
Latest commit at UTC: 2026-09-06T11:45:24Z
Latest commit SHA: bf92725
Chat duration: 560045s (06:11:34:05)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- Printable study handbook:
  [Architecture Learning Handbook](../../../../../docs/education/teaching-notes/0002-architecture-learning-handbook.md)

## RAG Knowledge Disposition

Status: covered
Reason: The checkpoint changes knowledge-bearing core security contract
organisation and the platform contract naming standard. Both are covered by
updated source material, derived rules, review and derivation evidence,
projection records, selector proof, and generated recognition sources.
Evidence:

- `docs/03.product/rule-packs/core/add-core-module.yml`
- `docs/03.product/rules/core/layers/packages-core.yml`
- `docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md`
- `docs/03.product/rules/platform/layers/platform.yml`
- `.agentic/02.rag-rulebook/source-material-reviews/03.product.platform/2026-09-01-platform-contract-identifier-naming.yml`
- `.agentic/02.rag-rulebook/derivation-reports/03.product.platform/2026-07-07-platform-runtime-enterprise-obligations-v1.yml`
- `.agentic/02.rag-rulebook/source-projections/v1.yml`
- `.agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/platform-contract-identifier-naming.yml`
- `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`

Corpus gaps:

- None.

### 2026-09-06T11:15:40Z - Local platform-shell container smoke passed

After Docker Desktop WSL integration became available, the governed local image
smoke test built the sealed platform-shell image and ran it with a read-only
filesystem, temporary `/tmp`, dropped Linux capabilities, and
`no-new-privileges`. Its `/livez` and `/readyz` checks passed. The staging
readiness record, AWS change plan, runtime plan, and learning handbook now
record this as local container evidence rather than a Docker blocker.

No AWS resource, IAM policy, DNS record, secret, ECR image, change set, stack,
task definition, or deployment was created or modified. The target remains
blocked on the separately governed IAM update, foundation change-set review,
official image provenance, and deployed smoke/rollback proof.
