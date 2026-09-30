<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.iaas-composition-and-release-control-plane
version: 1
status: draft
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- security
- sre
- agentic
kind: implementation-plan
purpose: Replace fragmented target-specific deployment checks with a governed, provider-neutral IaaS composition and release-realization control plane.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: aws.readme
  path: .agentic/aws/README.md
-->
# IaaS composition and release-control-plane implementation plan

## Current progress and fixed remaining backlog

**Active delivery scope, B02:** the user requested an
[MVP and backlog-first intake](../../../../docs/04.deploy/plans/iaas-release-control-mvp.md)
after the full programme proved too expansive. Deliver one controlled
`kanbien/staging` path using existing capabilities. Additional checks are deferred
unless concrete blocker, unsafe-effect or material-drift evidence makes them
necessary now. This supersedes the full-roadmap next-unit sequencing, not its
historical acceptance records or safety/approval rules. B03 accepted the selected
blueprint, exact-image publication handoff and task/passive-preflight components
(U17–U19); B04 accepts U20 selected operation/shared-store source conformance.
Next is the existing candidate lifecycle through durable execution, authenticated
admission and selected-caller integration under the approved source policy.
Whole-estate R1 closure is not the immediate milestone. The broad requirements
below remain the future roadmap and are not relabeled complete or inapplicable.

Use the [progress ledger](../../../../docs/04.deploy/plans/iaas-release-control-progress.md)
for the current accepted-delivery register, stable R1–R8 milestones, remaining
acceptance checkpoints, dependencies and changes between implementation runs.
Baseline B01 records 16 accepted delivery units, including seven since the old
15–20 estimate. B03 adds three scoped MVP components and B04 adds one (20
accepted components in total); all five full MVP milestones still have remaining
criteria. Those units do not close the AWS release programme.

The earlier 15–20 and later 12–17 slice forecasts lacked a fixed decomposition
and are superseded as progress measures. Future batches report against ledger
IDs and named unmet criteria, with explicit scope/estimate changes. Requirements
and approval boundaries below remain unchanged. The dated delivery entries and
Section 8 retain historical sequencing; the ledger owns the current next queue.

## 1. Outcome

Make a release a **reviewed realization of one declared environment**, not a
sequence of scripts that discovers prerequisites while mutating a live target.

When this programme is complete, a deployable component can be traced from its
source and final artifact, through its required cloud resources and identity,
to its live operational proof and recovery evidence. A missing executable,
secret binding, sidecar, permission, deployment prerequisite, or proof is a
machine-visible failure before a mutation begins.

The initial reference target is `kanbien/staging` on AWS. The model is
provider-neutral: AWS adapters describe CloudFormation, ECS, RDS, IAM, ECR,
CloudWatch and SQS semantics; they do not become the generic contract.

The control plane consumes shared data-governance decisions—classification,
residency, encryption, retention, legal hold and permitted observability
fields—from their owning platform contracts. It applies those decisions to a
target; it does not create a competing data-governance taxonomy in deployment
YAML.

## 2. Why this is needed

The repository has valuable checks already: image build and smoke validation,
CloudFormation validation, target reconciliation, IAM contracts, controlled
live smokes, and readiness manifests. Their weakness is structural rather than
individual quality: the facts they need are repeated across templates, target
profiles, workflows, scripts, Python expected-value dictionaries and docs.

That makes it possible for a server to be proved while an administrative job,
provider-shaped secret, task command, or recovery prerequisite remains
unproved. Adding a new one-off script for each discovery would increase that
risk. This plan therefore consolidates existing capability surfaces behind one
model and one controlled operation protocol.

## 3. Scope, constraints and non-goals

### In scope

- All supported repository-owned build, artifact, deployment, runtime,
  provisioning, migration, reconciliation, verification, recovery and
  scheduled operational paths.
- A provider-neutral composition model, release state machine, evidence
  contract, discovery/coverage verifier and provider adapters.
- Migration of current AWS `kanbien/staging` deployment controls, followed by
  AWS qualification in isolated, reviewed steps.
- A durable path for future provider adapters without guessing that providers
  share lifecycle semantics.

### Fixed safety constraints

- No legacy-site, DNS, default-ALB-routing, non-staging, or stored-secret
  change is implied by this plan.
- An external mutation needs explicit approval scoped to its provider, identity,
  resources, effects and cost. AWS mutations additionally follow
  `.agentic/aws/workflows/execute-approved-aws-change.md`; that workflow does
  not grant authority over another provider or an externally owned dependency.
- The control plane records secret *references and schemas*, never values,
  tokens, request bodies, raw provider responses, task IDs or customer data.
- Release operations fail closed on unresolved coverage, changed source/artifact
  identity, unsafe scope, stale evidence, missing rollback, or uncertain
  external outcome.
- A normal release may never use a break-glass exception. An emergency action
  has an independently auditable, time-bounded exception record and mandatory
  post-incident review; it cannot silently become the normal deployment path.
- New recurring and disposable costs across every selected provider must be
  estimated and approved before creation. Initial source work requires no
  provider access or external mutation.

### Explicit non-goals

- Replacing CloudFormation, GitHub Actions, or AWS CLIs with a generic cloud
  framework.
- Claiming all providers are qualified because a provider-neutral schema exists.
- Retrofitting business-feature semantics into deployment records. Features
  declare their platform-consumption decisions separately; this model binds
  their executable deployment requirements.
- Retrying PostgreSQL Stage 6 under the old procedure. It remains paused until
  the relevant phases below have passed.

## 4. Target architecture

The implementation has four records with different lifecycles. They must never
be collapsed into one mutable target YAML file.

| Record | Changes when | Owns | May it mutate cloud state? |
| --- | --- | --- | --- |
| **Target composition** | Environment architecture changes | Components, resources, dependency edges, identity boundaries, budget, configuration/secret *schemas*, supported operation profiles and recovery contracts | No |
| **Release definition** | A candidate is prepared | Immutable source revision, artifact digest, selected composition revision, intended changes, bounded operation graph and required proofs | No |
| **Observed-state record** | A verifier runs | Safe current facts, target fingerprint, drift/reconciliation result and freshness | No |
| **Evidence record** | A proof phase completes | Bound assertion, adequate environment, result, receipt/integrity metadata, expiry, cleanup state and invalidation dependencies | No |

The controller is the only component allowed to progress a release through:

```text
planned → validated → prepared → authorised → executing → observing
       → succeeded → cleanup-verified → closed
```

It also represents `failed`, `unknown`, `cleanup-required`, `compensating`, and
`design-reopened`. Resource state and controller state are separate: an exited
task or a lost provider response does not prove whether a cloud mutation
happened.

### Required composition graph nodes

The compiler will model, where applicable: source/build units; final artifacts;
services and finite jobs; sidecars; workflows and scheduled triggers;
infrastructure resources; configurations and secret schemas; identities and
authority contracts; storage/queues/databases; network, TLS and DNS; telemetry
and alerting; deployment artifact stores; recovery/restore units; and evidence
stores. Each target also declares account/region guardrails, service quotas,
network-address and capacity limits, resource lifecycle and retention/
decommissioning obligations, and its consumed data-governance contract
revision. Edges declare the phase, effect, dependency, completion predicate,
proof obligations and invalidation conditions.

### Provider and resource ownership boundaries

Every resource and dependency binding identifies its provider/service boundary,
provider namespace (such as account/tenant and region where meaningful), logical
resource reference, accountable owner, acting identity, allowed effects and
inspection capability. A target may contain several providers; a target-level
provider name is never sufficient authority for every resource below it.

Bindings distinguish release-managed resources from externally owned
consume-only or inspect-only dependencies. Consumption permits only the named
application actions; inspection permits only declared safe reads. Neither
permits provisioning, policy changes, replacement, teardown or deletion of the
external resource. Cleanup may close this release's client/session or remove
separately declared disposable resources within its authority. It cannot infer
ownership of the external dependency from that dependency's inclusion in the
graph. Missing authority, inspection capability or ownership stays unresolved.

An empty category is allowed only when independent discovery confirms it. An
unsupported dynamic launch or configuration edge remains an explicit
unresolved obligation, not a silent exemption.

## 5. Step-by-step implementation plan

Each phase has a machine-checkable exit gate. No phase authorises a production
mutation merely because its source has been committed.

### Mandatory release acceptance matrix

Every release definition contains one ordered, machine-readable instance of
this matrix. It is the authoritative answer to “may this release advance?”;
the phases below describe how the repository obtains the capability to answer
each row.

<!-- deterministic-check: allow reason="This acceptance invariant is enforced by the release compiler and ordered execution gates; it is not a manual procedure." -->
Each generated row must bind: the release and target-composition revisions;
the accountable owner and acting identity; the selected operation profile and
command/adapter; required safe evidence; evidence expiry/invalidation
dependencies; failure state; and recovery/cleanup route. A later row cannot
run when an earlier mandatory row is missing, failed, stale, invalidated or
`unknown`. An approved break-glass record may select only its declared limited
emergency profile; it cannot mark unrelated rows as passed.

The **reference baseline** column preserves the PostgreSQL Stage 6 assessment
that motivated this programme. It is historical planning input, not current
cloud-state evidence: every future release must obtain fresh evidence through
the named gate.

| # | Mandatory question and required safe evidence | Profile / implementation location | Failure and recovery rule | Reference baseline |
| --- | --- | --- | --- | --- |
| 1 | **Scope and risk:** what changes, who can be harmed, what must never change, and what is the recovery model? Evidence: approved effect boundary, protected resources, rollback/forward-repair and cleanup contract. | Release definition; Phase 0 handoff; Phase 1 lifecycle/exception contracts. | Reject unbounded effects, missing recovery, unowned resource or expired exception. Reconcile and revise design before planning. | Mostly defined: isolated target, no legacy/DNS/default-route changes, harmless synthetic work. |
| 2 | **Acceptance contract:** which deployable executables exist and what exact evidence must each produce? Evidence: independently discovered inventory reconciled to the selected graph and profile-specific proof matrix. | Phase 1 profiles/evidence matrix; Phase 2 collectors and coverage compiler. | Reject unknown, undeclared or unqualified executable, sidecar, binding or caller. Add/review the graph before release. | Missing as one exhaustive matrix. |
| 3 | **Source contracts:** are configuration and secret schemas, permissions, data lifecycle/governance, telemetry, timeouts and failure categories explicit? Evidence: validated versioned contracts and negative fixtures. | Phase 1 contracts; Phase 4 diagnostics; consumed data-governance revision. | Reject an implicit configuration/secret shape, authority edge, governance decision or unclassified failure. Reopen design and add a contract. | Partial: managed-master secret shape was initially missed. |
| 4 | **Unit and contract tests:** do functions reject invalid input and preserve safe semantics? Evidence: deterministic positive, negative, boundary, concurrency and mutation tests for each contract. | Phase 1 exit gate and Phase 2 mutation tests; generated test obligations per profile. | Reject uncovered behavior or a failing invariant. Fix source/contract; do not substitute a live test for a deterministic unit defect. | Stronger coverage exists for persistence and source policies; needs exhaustive generated obligations. |
| 5 | **Integration tests:** do actual dependency engines behave correctly in a disposable adequate environment? Evidence: profile-specific integration receipt, isolated inputs and cleanup result. | Phase 5 adapter conformance and disposable qualification targets. | Reject fixture-only claims where a real engine/provider behavior is required. Repair integration or use a reviewed disposable qualification environment. | Local PostgreSQL adapter integration exists; full ECS/RDS task execution does not. |
| 6 | **Exact-artifact tests:** does each actual command or versioned provider-native definition behave correctly in its immutable final artifact under its execution constraints? Evidence: digest/revision, exact command/definition, identity, semantic result and shutdown/cleanup receipt; container profiles also prove user/filesystem/security constraints. | Phase 3 exact-artifact qualification; finite-job profiles. | Reject host-workspace, import-only or server-only substitution. Rebuild and qualify the exact command before publication/promotion. | Server: yes. Bootstrap/migration/relay/worker/restore: insufficient. |
| 7 | **Supply-chain proof:** is the artifact immutable, scanned, SBOM/provenance-attested and tied to source? Evidence: verified digest, SBOM, scan policy result, attestation/provenance, base artifact and signature receipt where supported. | Phase 3 supply-chain admission. | Reject unknown, unsigned/unverified, stale, vulnerable beyond policy or source/digest-mismatched artifact. Rebuild from reviewed source. | Present. |
| 8 | **Infrastructure and authority validation:** do rendered resource definitions, authority policies, network, encryption, ownership, alarms, retention and references match target policy? Evidence: rendered-template, policy, schema and negative-test receipts. | Phase 2 discovery; Phase 5 target-composition compiler and AWS adapter fixtures. | Reject invalid template/reference, policy mismatch or unmodelled resource edge. Correct source; do not attempt provider execution. | Largely present; becomes one compiler gate. |
| 9 | **Provider effect-plan review:** does the provider's reviewed change plan or equivalent bounded effect description contain only allowed changes? Evidence: immutable safe change summary bound to release, target fingerprint, permissions/cost delta and reviewed rollback. | Provider-specific planning profile (AWS reference: CloudFormation change set); Phase 6 `plan`. | Reject replacement/destructive/broader-scope/unexpected-cost change. Revise composition or create a separately reviewed recovery plan. | Present and working. |
| 10 | **Drift and dependency preflight:** are provider namespace, target fingerprint, quotas, capacity, cost boundary, resources and dependency state expected? Evidence: fresh normalized observed-state record. | Phase 0 inspection; Phase 5 capacity/limit adapter checks; Phase 8 candidate entry. | Reject stale/mismatched provider namespace or target, drift, insufficient capacity, unavailable quota or unapproved cost. Reconcile or safely remediate before a new plan. | Present for reviewed boundaries; must become one readiness contract. |
| 11 | **Candidate runtime proof:** can the immutable artifact execute safely within the candidate boundary? Evidence: profile-specific candidate receipt for service or job, including provider, actual identity, artifact, command/definition and observation route. | Phase 3 exact artifact; Phase 4 non-mutating candidate mode; Phase 8 qualification. | Reject server-only proof for a finite task, old-revision health, or candidate with no observable terminal result. Fix candidate prerequisites before live operation. | Present for the HTTP server only. |
| 12 | **Per-task live preflight:** can every selected task use its real provider authority, injected secret schema, network, TLS and logging/evidence paths without writing business state? Evidence: no-effect preflight receipt per task/profile. | Phase 4.6; Phase 8.2. | Reject any missing command, identity, input, network/TLS or observation capability. Reopen design; do not use a state-changing run as diagnosis. | Missing; decisive Stage 6 gap. |
| 13 | **Controlled state change:** can bootstrap/migration/relay/worker run once, idempotently and within a bounded blast radius? Evidence: operation journal, semantic completion, effect receipt, fence/idempotency proof and cleanup. | Phase 4 controller; Phase 8.3 ordered operation graph. | Stop on unknown outcome, duplicate ownership, non-idempotent effect or budget breach. Reconcile journal before retrying; use declared compensation/forward repair. | Not proven because bootstrap has not passed. |
| 14 | **Post-change verification:** are health, authorization, queue/database invariants, telemetry, alarms, cost and steady state correct? Evidence: bound profile-specific verification receipts. | Phase 8.4–5; observability and target-policy adapters. | Reject partial health as full success. Quarantine/recover through the operation graph, then re-observe after cleanup. | Partly designed; end-to-end proof has not run. |
| 15 | **Rollback and recovery:** can service rollback, forward repair, restore and cleanup be demonstrated safely? Evidence: executed recovery receipt, restoration invariant and declared post-recovery state. | Phase 1 lifecycle; Phase 6 lifecycle gates; Phase 8 controlled recovery proof. | Reject theoretical-only restore/rollback. Use an isolated rehearsal; data, retention or cleanup policy violations block recovery qualification. | Service rollback approach exists; relational restore is designed but not live-proven. |
| 16 | **Evidence retention:** is safe evidence durable, queryable, digest-bound and free of secrets/raw provider data? Evidence: verified receipt/journal storage, access policy, expiry/invalidation and redaction checks. | §4 records; Phase 4 journal; Phase 6 evidence upload; Phase 9 dashboard. | Reject terminal-only, unbound, untrusted, replayed, stale or sensitive evidence. Re-run the affected proof after secure evidence storage is available. | Partial: some evidence is transient terminal output. |
| 17 | **Continuous operation:** are SLOs, alerts, telemetry-loss detection, patching, cost controls, expiry and recovery rehearsals operating? Evidence: scheduled-control history over required windows and alert-delivery/rehearsal receipts. | Phase 9 continuous assurance; supply-chain admission drives patch/requalification. | Alert and open a recoverable operation for missed control, expired proof, unsupported dependency, budget breach or failed rehearsal. A one-time release proof cannot satisfy this row. | Observability baseline exists; long-window SLO and relational periodic rehearsal remain incomplete. |

### Assertion subjects and generated applicability

Keep all 17 ordered gates. Within a gate, an assertion identifies its subject
scope: **release**, **artifact**, **operation**, **resource** or **dependency**.
It binds the subject ID/revision, provider boundary when relevant, owner,
operation profile, expected predicate, evidence kind and adequate environment,
identity/effect boundary, invalidation dependencies and recovery/cleanup route.
A shared artifact proof may support several operations only through explicit
bindings; one operation's completion cannot stand in for a sibling operation.

The compiler derives obligations and applicability per gate and subject from
independent discovery facts, reviewed composition and versioned profile rules.
An applicability result includes the subject, rule ID/version, input-fact
references/digests and reason code. It cannot be supplied as free text or by
calling a path `test-only`. Unsupported facts/profile mappings remain unresolved
and block progression. A whole row may be `not-applicable` only if every expected
subject has a supported result and the risk policy permits that aggregate;
no row is removed. Humans review generated results and safe evidence.

The first compiler unit deliberately requires every declared operation at all
17 gates and rejects all `not-applicable` claims. Retain that conservative
compatibility behavior until generated subject obligations can be validated
against independent coverage. Historical schema identifiers such as
`exact-image` remain compatibility aliases; they do not justify omitting a
provider-native executable. Such an executable requires an equivalent exact
versioned-definition proof or remains unsupported and blocking.

### Mixed-provider acceptance example

Use synthetic source fixtures for an AWS-hosted query service and finite loading
job consuming an externally owned warehouse (for example a proposed Snowflake
integration). This example makes no claim about a provider's implemented
capabilities. Product/runtime connectors under `platform/adapters/` implement
query/load behavior; release-control deployment adapters inspect and qualify
provider facts within declared authority. Neither supplies the other's proof.

The service and loader have separate commands, identities, artifact bindings,
completion predicates and recovery routes. Artifact-scoped checks qualify their
actual packaged commands; operation-scoped evidence separately establishes
service readiness and terminal loader completion. Resource/dependency checks
bind the warehouse's provider, ownership, approved consumption and safe
inspection method. Release-scoped checks aggregate approved effects and costs
across both providers. No warehouse provisioning or deletion is implied.

Conformance tests must reject: deleting an external resource through a
consume-only binding; evidence from the wrong provider or identity; HTTP health
as finite-job completion; a container command falsely labelled provider-native
to evade artifact tests; omitted dependencies or unsupported applicability; and
success when cleanup remains failed or unknown. Provider-native definitions,
if later supported, need their own immutable artifact and semantic proofs.
Local fixtures prove these checking rules only; live authority, behavior and
cleanup require later adapter qualification and evidence verification.

### Required cross-cutting control contracts

The following contracts are mandatory input to the matrix. They are not
optional architecture notes, and a release cannot use a generic “covered by
platform” claim in place of one.

| Contract | Mandatory content | Matrix gates it controls |
| --- | --- | --- |
| **Risk tier** | A machine-readable tier based on effects, data classification, privilege, reversibility, target exposure and cost. The tier selects the minimum non-waivable gate set, independent-review depth, qualification environment and recovery proof. A lower tier can add gates but cannot omit its mandatory gates. | 1, 2, 5, 9, 13–15, 17 |
| **Environment contract** | Per-resource provider/service and namespace, target fingerprint, identities, network paths, certificates/domains, external dependencies, database/queue/storage bindings, quotas, capacity and cost ceilings. Each binding has ownership mode, allowed effects, owner, source, expiry and safe inspection method; consume/inspect-only dependencies exclude lifecycle mutation. | 1, 3, 8, 10–12, 14 |
| **Configuration lifecycle** | Versioned schema, defaults and override precedence, compatibility range, secret reference shape, rotation, revocation, expiry, rollout and rollback rules. Validation occurs before any candidate starts. | 3, 4, 6, 11–13 |
| **Compatibility contract** | Backward/forward compatibility for API versions, queue envelopes, database schema, cache values, feature flags and rolling deployments. It states mixed-version duration, upgrade order, safe rollback point and incompatibility detection. | 2–6, 11–15 |
| **Data-migration safety** | Explicit `expand → migrate → backfill → validate → contract → retention/purge` phases; data invariants, resumability, idempotency, forward repair, backup/restore point and irreversible-change approval. | 1–6, 12–15 |
| **Capacity and resilience** | Load envelope, timeouts, rate limits, connection-pool limits, autoscaling/fixed-scale bounds, dependency degradation, service quotas, regional failure posture, budget ceiling and overload behavior. | 1, 5, 8, 10–14, 17 |
| **Failure-injection matrix** | Profile-appropriate controlled faults: dependency loss, rotated/expired secret, denied permission, network/TLS failure, task restart, queue redelivery, telemetry loss, rollback/recovery and cleanup failure. It declares safe fault mechanism, bounds, expected signal and restoration. | 4, 5, 11–17 |
| **Telemetry-health contract** | Expected logs/metrics/traces, collector/exporter dependency, signal freshness, cardinality bounds, redaction rule, missing-telemetry detector, alert route and false-green prevention. Missing telemetry is a failed control, never a successful SLO. | 3, 10–11, 14, 16–17 |
| **Break-glass diagnostic policy** | Restricted diagnostic categories, accountable operator, permitted secure location, time-bounded access, redaction, retention/destruction, audit receipt and escalation when safe categories cannot diagnose a failure. It never permits secrets/raw bodies into Git, terminal evidence or commit logs. | 1, 3, 12–16 |
| **Cleanup and expiry contract** | Every disposable task, restore instance, artifact, temporary role/client, synthetic resource and evidence lease has an owner, effect boundary, cleanup action, deadline, verification, cost check and escalation path. Cleanup cannot mutate an externally owned dependency; failed/unknown cleanup blocks successful closure. | 1, 5, 9, 13–17 |
| **Continuous reconciliation contract** | Scheduled checks for declared resources, provider authority, network, certificate expiry, image vulnerability/patch state, budget, backup status, alarm delivery, telemetry health, restore readiness and evidence expiry. It defines cadence, owner, alert and recovery operation. | 10, 14, 16–17 |
| **Exception contract** | Time-bounded risk owner, affected gates, justified impossibility, compensating control, approved scope, expiry, follow-up deadline, closure evidence and escalation. An exception cannot conceal a failed gate or bypass target/data/secret safety rules. | Every gate |
| **Harness self-verification** | Tests for manifest parsing, composition coverage, profile applicability, state transitions, locks/fences, idempotency, evidence redaction/invalidation, adapter conformance and refusal of unsafe/unapproved actions. Negative fixtures must prove each control fails closed. | Every gate |

The compiler expands these contracts into the individual matrix rows for the
selected risk tier and operation profiles. A missing, incompatible, expired or
unverifiable contract is a `validated: failed` result, not a documentation
warning.

### Implementation-readiness decisions and fixed migration order

The following are hard prerequisites for implementation, not items to discover
while running a relational proof. They become a small set of ADRs, schemas and
checklists; the broad plan remains an index, not the sole source of truth.

1. **Durable control-plane stores.** Define a provider-neutral lock/journal/
   evidence-store interface, retention class, encryption, access boundary,
   backup and recovery rule. The initial AWS reference may use conditional
   DynamoDB records for cross-host lock/fencing and operation journal state,
   with encrypted/versioned S3 for immutable safe evidence and artifacts, only
   after its cost, IAM, lifecycle and restore design passes review. No receipt
   may be treated as durable merely because it appeared in terminal output.
2. **Bootstrap trust.** Define a one-time source-first bootstrap profile for
   introducing the controller. It uses the already governed image/build and
   change-set path, static/self-verification and a narrow read-only/candidate
   operation. It cannot claim full target qualification. The next controller
   release must use the controller itself; bootstrap authority then expires.
3. **Supported-estate boundary.** Time-box independent inventory and require
   each path to be `migrate`, `retire`, `temporary-compatible` with an expiry,
   or `historical` with caller/build proof. No unclassified path may quietly
   expand the programme indefinitely or bypass the new system.
4. **Profile governance.** Begin with the fixed profile set: static artifact,
   inspection, service rollout, finite job, queue consumer, infrastructure
   change, migration, restore and scheduled control. A new profile needs an
   ADR, adapter conformance contract, failure model and matrix applicability;
   a provider-specific lifecycle cannot be hidden under a vague generic name.
5. **Quantified objectives.** Before target qualification, the target contract
   must set risk-tier-specific RPO, RTO, maximum attempt/time budget, evidence
   retention, backup/restore rehearsal cadence, operational-observation window
   and monthly recurring/disposable cost ceilings. Absent values fail planning.
6. **Governance dependency baseline.** Until the shared data-governance module
   is implemented, release compilation consumes a versioned, reviewed interim
   baseline containing only required classification/residency/encryption/
   retention/logging decisions. Its retirement/migration condition is the
   published platform data-governance contract—not an informal replacement.
7. **Human and bounded-agent accountability.** The target contract names a
   human accountable owner, normal/high-risk approver, alert destination,
   incident handoff procedure and permitted automation. Agents may inspect,
   compile, execute preapproved bounded operations and recover only through a
   declared profile; destructive, scope-expanding or break-glass actions remain
   human-approved.
8. **Qualification cost policy.** Every disposable environment and rehearsal
   declares resource inventory, estimated one-time/monthly cost, absolute
   expiry, cleanup verifier and budget alarm. The controller refuses a new
   disposable operation if prior cleanup is unresolved or the declared ceiling
   would be exceeded.

The migration order is fixed to prevent parallel replacement frameworks:

1. preserve handoff state and inventory the supported estate;
2. publish schemas, contracts, risk tiers and harness self-verification;
3. implement compiler/coverage and exact-artifact qualification;
4. implement durable journal, lock/fencing, evidence and bootstrap profile;
5. implement read-only AWS adapter and environment/capacity preflight;
6. implement candidate and per-task no-effect preflight;
7. implement controlled service, finite-job, migration, relay/worker and
   restore profiles with failure-injection/recovery proof;
8. migrate existing scripts one profile family at a time with equivalence
   evidence and compatibility wrappers;
9. retire wrappers only after caller-proof and adoption-ledger closure; and
10. qualify `kanbien/staging`, then activate continuous controls and the
    required observation window.

PostgreSQL Stage 6 remains paused until steps 1–6 are complete and its
bootstrap, migration, relay, worker and restore graph has passing candidate and
no-effect preflight evidence.

### Phase 0 — preserve state and establish ownership

1. Create a terminal handoff record for each active deployment/recovery stream:
   source and artifact revisions, logical operation state, safe diagnostics,
   target facts observed, cleanup state, evidence produced, outstanding actions
   and released ownership.
2. Reconcile `kanbien/staging` read-only before treating prior chat output as
   current state. Do not infer that a stopped local process stopped a remote
   operation.
3. Record an adoption ledger for every supported path: active, dormant but
   supported, test-only, historical or retired. A path is retired only after
   its callers and replacement evidence are proved.
4. Freeze new target-specific deployment scripts except for a time-critical
   safety repair. A repair must be recorded as a temporary adapter candidate.
5. Record the target lifecycle state, account/region boundaries, resource
   owners, cost controls, quotas, capacity ceilings, provider limits and
   applicable data-governance revision. Unknown limits are explicit design
   assumptions with a bounded verification experiment.

**Exit gate:** a source-controlled handoff and independently generated
inventory exist; every supported path has an owner and a disposition.

### Phase 1 — define the contracts before implementation

1. Add versioned schemas for the four records in Section 4 and an explicit
   schema migration policy.
   Include the generated 17-row release acceptance matrix above; individual
   releases must not choose an ad-hoc subset of mandatory gates.
2. Define operation profiles: static artifact, service rollout, finite job,
   queue consumer, migration, backup/restore, scheduled operation,
   infrastructure change and inspection-only. Each profile defines its own
   completion, timeout, retry, cleanup and evidence rules.
3. Define a provider-adapter interface with `inspect`, `plan`, `execute`,
   `observe`, `classify`, `reconcile_unknown_outcome`, and `cleanup` methods.
   Each method consumes a validated, immutable request and emits only safe
   normalized facts.
4. Define an evidence compatibility matrix using the assertion scopes above.
   For example, a healthy service cannot satisfy a finite-job proof; a fixture
   cannot satisfy a managed-RDS proof; provider acceptance cannot satisfy a
   semantic migration completion. Bind provider, subject, artifact and identity;
   include the mixed-provider negative examples in harness conformance tests.
5. Define identity and policy bindings: every operation names the acting
   identity, exact provider actions/resources, justification, and an
   authority-expiry rule. Resource ownership and permitted effects constrain
   every adapter action, including cleanup; consume/inspect-only resources can
   never inherit managed-resource authority. A generic adapter may not invent
   permissions.
6. Define interruption behavior: lease, fencing, idempotency keys, operation
   journal, retry classification, fixed cumulative limits, and recovery paths.
7. Define an exception and break-glass contract. It requires a severity/reason,
   target and effect boundary, named accountable owner, independent approver
   where practicable, maximum expiry, immutable safe receipt, restoration of
   normal controls and post-incident review. It cannot waive data handling,
   secret-exposure, target-scope or destructive-action safeguards.
8. Define a target lifecycle contract for provision, operate, drain, retain,
   restore, decommission and delete. It names dependency checks, data
   retention/legal-hold constraints, backup/restore requirements, cleanup,
   cost verification and terminal evidence for each transition.
9. Define the data-governance input boundary and versioned resolver. Release
   compilation fails if a selected resource, telemetry channel, artifact store
   or recovery operation lacks an applicable classification, residency,
   encryption or retention decision.
10. Define the risk-tier, environment, configuration-lifecycle, compatibility,
    data-migration, capacity/resilience, telemetry-health, cleanup/expiry and
    continuous-reconciliation schemas described above. Bind each to its matrix
    rows and fail on missing applicability/ownership/expiry.
11. Define the failure-injection matrix and break-glass diagnostic policy. Both
    use least-privilege, time-bounded mechanisms and record only safe evidence.
12. Define the exception record as a distinct state-machine input with an
    explicit compensating control, closure deadline and automatic expiry. It
    cannot mark a failed technical proof as passed.
13. Define harness self-verification as a release-engine requirement, not a
    developer convention. It must include malformed/ambiguous manifests,
    unauthorized mutations, lock races, evidence leaks/replay, adapter
    mismatch, stale approval and failed-cleanup counterexamples.

**Exit gate:** schemas, profiles, evidence rules, error taxonomy, lifecycle,
data-governance and exception contracts have positive and deliberately-invalid
fixture tests. Independent review has traced success, partial completion,
duplicate execution, loss of controller, stale evidence, cleanup failure,
emergency expiry, diagnostic escalation, mixed-version compatibility,
data-migration recovery, capacity exhaustion and decommissioning dependencies.

### Phase 2 — discover the actual estate and compile coverage

1. Build independent collectors for package/workspace commands, source exports
   and process entrypoints, final-image metadata, rendered IaC, GitHub workflow
   invocations, task definitions, container commands, sidecars, injected
   configuration/secret references and supported script entrypoints.
2. Make collectors emit observations, not a maintainer-authored expected list.
   Declare supported source roots/formats and scan them independently of the
   composition's paths. Bind observations to source digests and collector/rule
   versions. Parse failures, symlinks, dynamic process launches and unsupported
   formats become unresolved findings, never an empty successful inventory.
3. Reconcile discovered observations against composition declarations. Reject
   undeclared executable units, bindings, sidecars, artifacts, identity edges,
   operational effects, callers or required proofs. Generate scoped subject
   obligations and applicability as defined above; retain unsupported mappings
   as blocking findings. A bounded source scan cannot claim final-artifact or
   live-estate closure while those collectors or evidence remain absent.
4. Implement mutation tests that introduce an unlisted command, hidden sidecar,
   missing secret binding and false `test-only` label. Include the mixed-provider
   ownership, evidence-binding and false-exemption cases. The coverage gate must
   fail each case; scopes awaiting later collectors have explicit blocking tests.
5. Generate an adoption matrix mapping every existing `scripts/04.deploy/`
   capability, workflow and target operation to its replacement controller
   profile or deliberate retirement plan.
6. Add harness self-verification tests for every contract parser, matrix
   expansion, state transition, lock/fence rule, evidence redaction rule and
   provider-adapter response. Each test must include a counterexample which is
   rejected before a mutating operation can begin.

**Exit gate:** all supported source paths and caller relationships are accounted
for in the declared graph, with no unresolved source-coverage gap or undocumented
exclusion. Every later artifact/provider obligation has a subject, owner, evidence
requirement and blocking gate. Recording such an obligation is not satisfying
it: final-artifact behavior belongs to Phase 3, provider qualification to Phase
5 and target qualification to Phase 8. Those gates remain blocked until their
evidence exists. Negative coverage tests must reject hidden callers and false
exemptions. A scoped source delivery unit does not close this whole-estate gate.

### Phase 3 — make build and artifact proof exact

1. Derive the build/dependency/export closure from workspace manifests and
   compiler emission instead of duplicated workspace maps or runtime fallback
   to TypeScript sources.
2. Build once into private output/dependency directories; pin/verify toolchain,
   lockfile, base artifact, target platform and produced digest.
3. For each executable profile, run the final artifact with its actual
   entrypoint/command, user, working directory, assets, environment shape and
   shutdown constraints. Test one-shot task definitions separately from server
   readiness. A supported provider-native profile qualifies its immutable
   versioned definition and semantic completion under the equivalent artifact
   rules; changing its label cannot exempt a packaged container command.
4. Add provider-shaped input fixtures, including managed-secret schemas and
   configuration versioning. Fixtures validate parser behavior; they are never
   evidence of managed-provider authorization.
5. Publish/promote the exact digest that passed qualification. Any source,
   generated output, base image or command change invalidates affected proof.
6. Produce and verify a software bill of materials (SBOM), vulnerability scan,
   build provenance/attestation, resolved base-artifact identity and, where the
   chosen registry supports it, signature policy. Thresholds, accepted
   exceptions, scanner versions and expiry are governed release input; an
   unsigned or unverified candidate cannot be promoted merely because it runs.
7. Execute the selected compatibility and data-migration tests against the
   supported mixed-version boundaries. An irreversible schema/data operation
   cannot pass without its expand/contract and forward-repair/restore proof.

**Exit gate:** the release definition names final digests, exact commands and
verified supply-chain receipts; each discovered executable has an appropriate
final-artifact proof; mutation tests prove stale outputs and workspace fallback
cannot produce a pass.

### Phase 4 — implement the controlled operation engine

1. Refactor the existing `operational-realization-gate` into the single public
   operation engine. Preserve its provider-free protocol; do not create a
   parallel controller.
2. Add a durable operation journal. It records immutable intent before effects,
   per-phase safe observations, terminal semantic result, cleanup result and
   evidence receipt. It makes resumption/reconciliation possible after a lost
   response or controller crash.
3. Add target/resource lease and fencing. Controllers must atomically claim an
   operation, reject stale owners, and reconcile an uncertain provider outcome
   before another attempt.
4. Add phase, call and whole-operation deadlines. Only predeclared transient
   classes retry, with bounded exponential backoff/jitter and a cumulative
   attempt/time budget. Unknown failures open `design-reopened` rather than
   silently retrying.
5. Add generic safe diagnostic categories for loader/startup, configuration,
   identity, network/TLS, provider request, timeout, semantic failure,
   interruption, evidence and cleanup. Provider adapters retain details only
   in approved secure runtime logs, not source evidence.
6. Add a non-mutating preflight mode for every execution profile. It verifies
   final artifact, validated input shape, resolved target/resource/identity,
   current release lock, authority and observation path before a candidate
   operation begins.
7. Add a controlled failure-injection executor. It accepts only a reviewed
   fault from the selected matrix, proves restoration/cleanup, and refuses an
   effect beyond the declared risk tier or target boundary.

**Exit gate:** local and CI conformance tests cover normal success, lost
response, concurrent owner, stale fence, timeout, unsupported retry,
interrupted cleanup and evidence-store failure. Existing controller callers
can invoke the public engine through compatibility wrappers.

### Phase 5 — integrate AWS as an adapter, not as special-case generic code

1. Implement normalized AWS operations for CloudFormation change sets and
   stack completion; ECR artifact inspection; ECS service rollout and finite
   task result; IAM policy/identity inspection; RDS lifecycle and restore;
   SQS/queue settlement; CloudWatch/SNS telemetry and alert delivery.
2. For each operation, record documented IAM action, resource constraint,
   unavoidable wildcard exception, expected eventual-consistency behavior and
   safe observation query. Keep the AWS vocabulary inside the adapter and its
   target binding.
3. Extend existing reconciliation, image build, image smoke, candidate
   preflight, PostgreSQL smoke and restore commands as adapter-backed profiles.
   During migration, retain current command names as wrappers; prove behavior
   equivalence before retiring old implementation paths.
4. Compile `kanbien/staging` target composition from the existing target
   profile, CloudFormation fragments, IAM contracts, workflow configuration,
   deploy readiness, budget/alert configuration and safe resource-read
   contracts. The compilation also binds applicable data-governance decisions,
   resource lifecycle obligations and account/region/quota/capacity controls.
   Remove a duplicated fact only after the compiler verifies its projection.
5. Add CloudFormation and AWS-adapter conformance fixtures plus disposable
   synthetic-data qualification targets. Their cost ceiling, resource list,
   retention and teardown method must be reviewed before they are created.
6. Implement AWS inspection profiles for account identity and region, service
   quotas, requested-versus-available capacity, VPC/subnet address capacity,
   required encryption posture and relevant provider service limits. Preflight
   fails before mutation when the intended graph cannot fit safely.
7. Implement AWS environment-contract inspections for certificate/domain,
   route/network, dependency endpoint, backup/restore and configuration/secret
   lifecycle prerequisites. An adapter returns safe normalized facts only.

**Exit gate:** no active AWS execution command bypasses a declared operation
profile; AWS adapter conformance tests pass; a generated/verified target
composition identifies all current `kanbien/staging` components, resources,
identities, final commands, operation dependencies, lifecycle obligations,
consumed governance decisions, and capacity/limit prerequisites.

### Phase 6 — introduce release orchestration and policy gates

1. Provide one supported command surface, for example:

   ```text
   npm run platform:release -- --target kanbien/staging \
     --release <immutable-release-id> --phase validate|plan|realize|verify
   ```

   The final command name is a design decision; all variants must execute the
   same compiler and controller, locally and in GitHub Actions.
2. Compile a release definition from a target composition revision, source
   revision, final artifact digest and selected bounded operation graph. The
   compiler generates the ordered acceptance matrix and fails when a mandatory
   row lacks an owner, profile, evidence rule, recovery route or applicability
   result.
3. `validate` runs coverage, exact-artifact, policy, authority, cost and
   recovery checks. `plan` emits a safe immutable change/operation summary.
   `realize` requires the existing current-chat or protected-environment
   approval. `verify` binds live observations and cleanup to the release.
4. Enforce a release lock and state ledger. Concurrent deploys, manually
   repeated operations and stale evidence cannot cross a target boundary.
5. Connect GitHub Actions to the same release definition. The workflow must
   prove its protected-environment rules, commit/digest binding, OIDC identity,
   required checks and result/evidence upload; YAML presence alone is not
   evidence.
6. Add policy gates for least privilege, sensitive-data output, region,
   residency, network exposure, budget, allowed destructive actions, evidence
   freshness, recovery readiness and target scope.
   Apply the selected risk tier, environment, configuration, compatibility,
   migration, capacity, telemetry, cleanup, exception and reconciliation
   contracts as non-waivable release inputs.
7. Add exception handling to the state machine. A break-glass release has a
   distinct state, cannot use normal promotion evidence as approval, expires
   automatically, triggers post-incident reconciliation and blocks ordinary
   releases until the exception is closed or replaced by reviewed design.
8. Add lifecycle transition gates. A target or resource cannot be drained,
   decommissioned or deleted until dependency, retention/legal-hold, backup,
   restore, data-governance, cost and evidence obligations are satisfied.

**Exit gate:** a release cannot reach `realize` when any required discovered
unit lacks a passing profile-specific proof, current authority, rollback plan,
approved cost, target lock, supply-chain receipt, applicable governance
decision, capacity/quotas, safe observation method or closed exception state.

### Phase 7 — migrate all existing paths and retire duplication

1. Migrate one profile family at a time: static/source checks; image/server;
   finite tasks; CloudFormation; scheduled checks; persistence/outbox; restore
   and recovery; legacy supported targets.
2. For each migration, run old and new paths against the same safe fixtures or
   target facts; compare normalized result and scope. Differences require a
   design update, not a silent behavior change.
3. Update runbooks, package commands, target READMEs, workflows and commit-log
   templates to point to the release command and authoritative records.
4. Remove compatibility wrappers, duplicated expected-value dictionaries and
   incident-specific controller logic only after no supported caller remains
   and the coverage gate proves retirement.
5. Treat every new deployable component as a composition-model addition with a
   required profile, target binding, proof matrix and lifecycle policy from its
   first implementation slice.
6. Migrate existing release documentation and incident procedures to the
   exception/break-glass contract. Retire informal emergency commands only
   after an equivalent bounded operation profile and audit trail exist.

**Exit gate:** adoption ledger is closed for every supported path; no script or
workflow has an undocumented independent mutation route; old paths are retired
with caller-proof and historical evidence is retained safely.

### Phase 8 — qualify the Kanbien staging reference target

1. Reconcile current cloud state read-only and inspect cost, resource scope,
   identity policy, supply-chain receipts, consumed governance decisions,
   quota/capacity headroom and drift before approving a candidate.
2. Run candidate preflight for every selected unit—server, bootstrap/migration,
   relay, worker, restore—not merely the server.
3. Execute only a reviewed, immutable release operation graph. Capture safe
   evidence after each phase; continue automatically only after the prior phase
   satisfies its profile-specific predicate.
4. Prove normal and controlled negative/recovery paths: wrong-scope denial,
   rate limiting, routing/WAF, alert receipt, operation interruption,
   duplicate request/idempotency, relay/worker settlement, restore, rollback
   and cleanup. A finite task must emit/produce its terminal receipt before it
   is cleaned up.
5. Return the target to declared steady state, including worker scale and
   disposable resources. Reconcile again and record cost/alert observations,
   lifecycle state, resource ownership and any exception closure.
6. Keep 28-day SLOs as an operational-observation milestone; do not call them
   proven on the basis of a one-time release rehearsal.

**Exit gate:** target-specific qualification has passing safe evidence for each
required profile and recovery case, no unowned resource/effect, verified final
steady state and approved ongoing cost. PostgreSQL Stage 6 may resume only as
one release graph under this gate.

### Phase 9 — continuous assurance

1. Schedule read-only composition/reconciliation/evidence-freshness checks and
   bounded synthetics through the controller.
2. Add periodic safe recovery rehearsals and evidence-expiry requalification.
3. Alert on missing telemetry, evidence expiry, failed reconciliation, drift,
   failed scheduled control, budget breach, unclosed operation or cleanup
   failure, expiring break-glass exception, capacity/quota exhaustion or
   lifecycle-policy breach—not just application error rate.
4. Review provider/SDK/runtime upgrades and target-profile changes as evidence
   invalidators. Re-run only affected proofs through the dependency graph.
5. Publish a safe repository-wide operational dashboard/summary from the
   evidence ledger, without copying sensitive raw provider payloads into Git.
6. Run the continuous-reconciliation contract on its declared cadence,
   including IAM, network, certificate, image-patch/vulnerability, budget,
   backup, alarm-delivery, telemetry-health and restore-readiness checks.

**Exit gate:** the reference target remains operationally observed over its
defined window and any failed control becomes a classified, recoverable
operation rather than a fresh ad-hoc investigation.

## 6. Intended repository layout and ownership

The end-state deliberately has one generic controller and provider/profile
modules beneath it. Existing target-specific commands migrate into compatible
wrappers and are retired only after equivalence and caller coverage prove it is
safe. Do not create one Python module per incident, target, or release.

```text
.agentic/
├── 01.harness/
│   └── standards/
│       └── engineering-completeness.v1.md
└── aws/
    ├── standards/
    │   └── release-control-plane.v1.md
    ├── workflows/
    │   └── execute-governed-release.md
    └── checklists/
        └── release-readiness.v1.md

infra/04.deploy/
├── contracts/release-control/v1/
│   ├── target-composition.schema.yml
│   ├── release-definition.schema.yml
│   ├── acceptance-matrix.schema.yml
│   ├── evidence-record.schema.yml
│   ├── operation-state.schema.yml
│   └── provider-capability.schema.yml
└── 03.product/targets/kanbien/staging/
    ├── target-profile.yml
    ├── deploy-readiness.yml
    ├── composition.yml
    ├── operational-profiles.yml
    ├── cloudformation/
    ├── iam/
    └── release-blueprints/
        └── platform-shell-relational-stage6.yml

scripts/04.deploy/
├── release-control/
│   ├── cli.py
│   ├── compiler.py
│   ├── controller.py
│   ├── journal.py
│   ├── evidence.py
│   ├── policy.py
│   ├── discovery/
│   ├── profiles/
│   ├── adapters/aws/
│   └── tests/
└── existing-commands/
    └── compatibility-wrappers-during-migration

docs/04.deploy/
├── adrs/
├── plans/
└── runbooks/
    └── kanbien-staging-relational-reference.md
```

`platform-shell-relational-stage6.yml` is source-controlled declarative data:
it selects generic service, finite-job, migration, relay, worker and restore
profiles and their dependency edges. It does not contain target-specific
orchestration code. The compiler creates the immutable per-run release
definition, operation journal and safe evidence records; those live in the
approved evidence store and are referenced from commit logs, never repeatedly
edited in Git.

| Surface | Owns after the refactor | Do not put here |
| --- | --- | --- |
| `.agentic/01.harness/` | Generic engineering-completeness standard, design/review and evidence rules | AWS API details or application business policy |
| `.agentic/aws/` | Deploy-specific standard, workflows, checklist and this plan | Provider SDK implementation or product feature behavior |
| `infra/04.deploy/contracts/release-control/` | Machine-readable portable release-control schemas | Human-only duplicate contracts or provider credentials |
| `infra/04.deploy/03.product/targets/...` | Target composition, provider bindings, CloudFormation/IAM source and declarative release blueprints | Controller state, evidence payloads or secret values |
| `scripts/04.deploy/release-control/` | Shared controller, independent collectors, compiler, profile modules, AWS adapters and tests | Per-release or per-incident orchestration module |
| `scripts/04.deploy/existing-commands/` | Temporary compatibility wrappers with a retirement owner and deadline | A second implementation of the release algorithm |
| `.github/workflows/` | Invocation of the approved release command and GitHub/OIDC boundary | A separate deployment algorithm |
| `docs/04.deploy/` | ADRs, plans, human runbooks and links to safe evidence | A duplicate deployment standard, mutable operational state or provider payloads |
| `commitLogs/` | Chat/commit lineage and references to immutable safe evidence | Secrets, logs, messages or raw provider responses |
| Platform data-governance contracts | Classification, residency, encryption, retention, legal hold and logging policy inputs | Target-specific resource IDs, provider credentials or cloud-operation control flow |

## 7. Completion criteria

The programme is not complete because a plan, a healthy server or one
successful AWS run exists. It is complete when:

1. the independently discovered estate is fully reconciled with the reviewed
   composition graph, or each retired path has caller-proof;
2. all supported deployment/recovery paths use the shared controller and
   profile-specific evidence rules;
3. existing one-off scripts have either become verified adapters/wrappers or
   have been retired with equivalence/caller evidence;
4. a final artifact and actual command are qualified for every deployable
   execution profile;
5. AWS is qualified through provider-specific, scoped live evidence without
   leaking data or silently broadening permissions, and with passing
   supply-chain, governance and capacity/limit preflight;
6. release, operation and evidence state are durable, traceable, locked and
   safely recoverable;
7. the `kanbien/staging` target passes its full operation graph and returns to
   steady state; and
8. continuous controls have generated the observations required by their
   declared SLO/rehearsal windows.
9. every emergency exception is expired/closed, its normal-control restoration
   is verified, and target/resource lifecycle records have no orphaned
   dependencies, costs or retained data contrary to policy.

## 8. Immediate next slice

Implementation proceeds under the `source-batch` envelope in
`.agentic/01.harness/standards/autonomous-delivery-envelope.v1.md`: each
delivery unit includes contract, source, focused tests, documentation,
verification and the next queued unit. Routine local failures and Git
housekeeping are repaired internally rather than treated as handoff points.

The explicitly scoped first source delivery unit is complete (2026-09-28):
versioned release-definition and seventeen-stage acceptance-matrix schemas,
immutable bindings, full per-stage operation coverage, normalized compilation,
compatibility with the existing Operational Realization Gate, fixtures, focused
positive/negative tests and documentation. The existing command now accepts
`--release` with `--contract`; see
[`scripts/04.deploy/operational-realization-gate/README.md`](../../../../scripts/04.deploy/operational-realization-gate/README.md).
The combined `deployment:realization:check` passed: 29 release tests, existing
gate smoke tests and artifact metadata checks. Safe compilation is not target
qualification or authority: all stages remain `not-started`, all unsupported
applicability claims are rejected, and output always has `authorized: false`.

The follow-up request authorizes plan refinement followed directly by the next
source delivery unit: **independent discovery and composition coverage**.
Complete this bounded unit before proceeding to its explicitly recorded queue:

1. Load versioned composition, discovery/coverage and adoption-ledger schemas
   with closed fields, stable subject IDs, provider/ownership/effect boundaries
   and safe normalized output.
2. Independently scan documented supported source roots/formats; reconcile
   discovered paths, commands and bindings with composition and the adoption
   ledger. Unsupported/dynamic sources, parse failures and ambiguous ownership
   remain explicit blocking findings. Ledger dispositions require evidence;
   a declaration alone cannot hide an executable or establish retirement.
3. Generate profile obligations and applicability per gate/subject using
   versioned rules and discovery facts. Preserve the first compiler's strict
   behavior through compatibility; source-only output remains unauthorized and
   cannot claim execution evidence or complete live-estate qualification.
4. Add positive fixtures and negative/mutation tests for missing/hidden paths,
   stale facts, false disposition/applicability, mismatched bindings and the
   supported mixed-provider ownership boundaries. Clearly identify later
   evidence-admission/cleanup executor obligations instead of claiming fixtures
   execute them.
5. Extend the existing Operational Realization Gate command and documentation;
   run focused verification and record exact results, limitations, changed files
   and the next delivery unit in the session log.

A completed source delivery unit means its declared collector boundary and
failure behavior are tested; Phase 2's full-estate exit gate stays open until
all supported paths are reconciled. Queue additional collector coverage before
claiming estate closure, then exact-artifact qualification. AWS adapters,
durable AWS stores, PostgreSQL Stage 6 and live target qualification are later
units; no source batch authorizes their external effects. Preserve the
PostgreSQL handoff and do not attempt deployment until migration step 6 can
enumerate and validate every finite task in the proposed operation graph.

### Second source delivery unit evidence — 2026-09-28

The bounded independent discovery/composition-coverage unit is complete and
uncommitted. The existing gate now provides `--discover` and `--coverage`, loads
three additional closed versioned schemas, reconciles fresh source inventory
with composition and adoption, and generates seventeen scoped obligation rows.
The first release compiler's strict matrix remains compatible. Every successful
source coverage result remains `authorized: false`; generated applicability
waives only a scoped managed-effect assertion, never an entire stage or external
access-authority requirement.

`npm run deployment:realization:check` passed, exit 0: 29 release tests, 34 coverage
tests, 32 collector tests, existing smoke cases, boundary scans and metadata
checks. Mutation/review cases caught and repaired omitted dependency consumers,
collapsed containers, swapped artifacts, false provider-native labels, unknown
executable resource types, dynamic commands and unbound package target bytes.

The [pending source adoption plan](../../../../docs/04.deploy/plans/release-control-source-adoption/README.md)
records 273 sources, 1,054 observations and 169 unresolved findings. Its ledger
contains 273 pending review entries. Actual discovery correctly exited 1;
opaque execution, unsupported resource/image grammar and other unresolved
source semantics have not been approved away. The next unit must account for
and route these findings; it must not claim that static parsing alone resolves
the later artifact/provider evidence. They are not evidence of estate coverage.

Next delivery unit: additional collector/caller coverage and reviewed adoption
for the actual source estate, including arbitrary import/default entrypoint
coverage, explicit profile classification and production/test caller proof.
Phase 2 remains open. Runtime profile suitability, final artifact provenance,
authenticated authority and live provider ownership still require later
qualification. Exact-artifact proof may be implemented once its own source
inputs and callers are accounted for; it must not wait for its own future
receipts to close source discovery. Release eligibility still requires every
applicable coverage and evidence gate. External adapters/stores, PostgreSQL
Stage 6 and live target qualification remain later.

### Third source delivery unit — finding triage and staging callers

The user authorized this bounded continuation on 2026-09-29. First clarify the
phase boundary above, then extend the existing capability with closed contracts
for finding triage and independently discovered caller accounting. Preserve the
first two units and their unresolved evidence; do not create a second controller.

1. Bind every finding to its source/collector identity, intake owner, next action
   and required phase/gate. Triage cannot mark a source resolved, grant a reviewed
   adoption disposition, or suppress a coverage finding. Preserve the recorded
   169-finding baseline and distinguish a fresh inventory from it.
2. Select the staging image-publication command family, starting with its
   workflow, package commands and repository script invocations. This workflow
   publishes an artifact; source inspection must not misclassify it as an ECS
   rollout. Discover invocations independently of the reviewed caller list.
3. Support a bounded literal invocation grammar with source-bound caller edges.
   Account explicitly for npm lifecycle callers, working directories, wrapper
   arguments and external/dynamic execution boundaries; unsupported semantics
   stay blocking. Never execute an inspected command to discover its effects.
4. Reconcile all selected subjects/edges with reviewed operation profiles and
   required later evidence. A complete source accounting report can retain
   unresolved behavior; it must distinguish accounting from coverage or release
   qualification. Only existing evidence rules may establish stage success.
5. Add positive, negative and mutation tests for missing commands/callers,
   stale source, false test-only exclusions, dynamic shell, alias/cycle/unsafe
   parsing and safe normalized output. Extend existing CLI/docs/checks, record
   exact local results and publish the selected family's reviewable source map.

The delivery exit is tested triage plus complete accounting within this declared
invocation boundary and explicit blocking obligations for every opaque terminal.
Phase 2 estate closure remains open. Next units broaden supported caller/import
coverage and adoption for other operation families, then prove exact artifacts;
AWS stores/adapters, PostgreSQL Stage 6 and live operations remain later work.

### Third source delivery unit evidence — 2026-09-29

This bounded source unit is complete, verified locally and uncommitted. The
existing gate now accepts `--triage` and `--callers`; three closed schemas,
finding assignment, independent caller discovery, reviewed subject/edge
reconciliation, focused fixtures/tests and documentation are present. Classified
findings stay open. Caller accounting cannot grant release qualification or
authority, suppress the earlier source inventory, or approve adoption exclusions.

The [dated triage and staging source map](../../../../docs/04.deploy/plans/release-control-source-adoption/2026-09-29-triage-and-callers/README.md)
preserves all 169 baseline findings (164 Phase 2, five Phase 3). The fresh source
snapshot contains 282 files and 175 findings; the six additional findings are
new analysis/test modules. All current findings have open intake assignments:
170 Phase 2, five Phase 3, none assigned to live provider proof. Classification
is complete while source coverage remains blocked.

The selected image-publication graph independently discovers 23 workflow steps,
14 package commands, nine script subjects and seven tool subjects, plus its
workflow root: 54 subjects, 53 edges and 11 bound source files. Reviewed profiles
account for every subject/edge; qualification remains blocked by 38 explicit
opaque command/script/tool/action boundaries. Four production-reachable files
under test directories are bound rather than excluded. No ECS rollout is claimed.

`npm run deployment:realization:check` passed, exit 0: 174 tests (29 release,
34 source coverage, 32 source collector, 23 triage, 25 caller accounting and
31 caller collector), legacy smoke cases, provider/network boundary checks and
metadata validation. Independent adversarial review found and verified repairs
for cwd-changing shell builtins, npm configuration, Git environment selectors
and explicit source targets outside normal analysis roots. The actual public
CLI validated both current triage and caller review, exit 0, with coverage or
qualification still explicitly blocked and `authorized: false`.

Next delivery unit: source contracts and caller/profile/argument coverage for
the nine selected script terminals and external workflow actions, with build/
import closure and mutation tests. Resolve relevant Phase 2 findings through
supported semantics or evidenced adoption decisions; retain later artifact and
provider obligations at their blocking gates. Then address other supported
operation families and exact-artifact proof as their source inputs become known.
Phase 2 whole-estate closure remains open. No real stop condition is present;
no external operation, inspected deployment command, commit or push occurred.

### Fourth source delivery unit — repeatable validation and result consumption

The user authorized this reliability slice on 2026-09-29, before resuming
caller-semantic expansion. Keep the first three units' source-only boundaries
and historical snapshots intact.

1. Pin the supported validation runtime and the complete Python dependency
   closure with verified artifact hashes. A fresh, isolated environment must run
   the same public local check, without relying on globally installed packages.
2. Add a separate validation-only workflow with read-only repository permission.
   It must run the clean check on source changes without obtaining deployment
   credentials or invoking publication. Preparing workflow source is authorized;
   publishing it and enabling a required repository check are separate actions.
3. Include the delivery envelope, sustained workflow, this implementation plan
   and source-adoption documentation in the ordinary metadata check. These
   checks must no longer depend on remembering an extra manual invocation.
4. Define a closed source-result consumption decision. Accept successful source
   analysis only when it matches a fresh local recomputation of the same inputs.
   Source compilation, coverage, triage and caller-accounting results cannot
   establish release eligibility or operation authorization, even when their
   analysis command exits zero. Preserve those useful producer exit statuses.
5. Test clean-environment failures, unsafe CI changes, stale/forged results and
   attempts to consume successful analysis as authority. Refresh affected source
   review snapshots as a new dated candidate, retaining all historical evidence.

The exit is a locally verified reliability unit with contracts, code, fixtures,
negative tests, documentation and session evidence. This adds no runtime
evidence-admission engine and closes no opaque source or provider finding.
After this unit, resume source contracts and caller/profile/argument coverage
for the selected nine script terminals and external workflow actions, followed
by wider adoption and exact-artifact proof. Phases 2 and 6 remain open; AWS
adapters/stores, PostgreSQL Stage 6 and live target qualification remain later.

### Fourth source delivery unit evidence — 2026-09-29

The authorized reliability slice is complete, locally verified and uncommitted.
The existing gate now has a hash-locked eight-wheel Python dependency closure,
a fresh-environment verification wrapper, a closed source-result consumption
contract and public guarded consumption mode. The ordinary check includes all
five previously omitted governance/planning documents. A separate validation-only
workflow is prepared with read-only repository permissions and pinned actions.
It enters the wrapper directly and does not invoke artifact publication.

The clean wrapper passed with CPython 3.14.4/Linux x86_64, installing only the
verified locked wheels into a new virtual environment. The canonical
`deployment:realization:check` then passed, exit 0: **262 tests** (174 existing
and 88 new), legacy smoke cases, provider/network boundary scans and metadata
validation for 28 files. Real installer negatives rejected a changed wheel hash
and omitted transitive dependency. Independent review found a possible false
success through npm configuration; the repaired wrapper isolates npm config,
rejects project `.npmrc` and preserves failure through nested commands. CI
enters the wrapper directly so this safeguard cannot be skipped by outer npm.

Fresh public-command tests accepted valid current source analysis and rejected
both release-eligibility and operation-authorization use, including otherwise
successful triage and caller accounting. They also rejected stale historical
review inputs. This guard compares normalized producer output; it is not signed
evidence admission and does not authenticate intake owners or live authority.

The [new dated review candidate](../../../../docs/04.deploy/plans/release-control-source-adoption/2026-09-29-source-validation/README.md)
preserves the historical snapshots. It records 293 sources, 1,093 observations
and 185 open findings: 180 Phase 2 and five Phase 3. The staging graph still has
54 subjects, 53 edges and 38 unresolved boundaries. Only its package-manifest
source binding changed; subjects, edges and findings were compared before
retaining the previous declared profiles. Accounting remains complete,
qualification blocked and authorization false.

Next delivery unit: source contracts and caller/profile/argument semantics,
with build/import closure, for the nine selected script terminals and external
workflow actions. Then expand supported families/adoption and exact-artifact
proof. Phase 2 estate closure and Phase 6 evidence/authorization remain open.
The workflow has not been published or run on GitHub; required-check enforcement
has not been enabled. No real stop condition exists within this completed source
slice. No external resource mutation or Git publication occurred.


### Fifth source delivery unit — selected operation contracts and dependencies

The user authorized this next bounded source unit on 2026-09-29. Extend the
existing gate's independently discovered staging callers with explicit operation
contracts for nine script subjects, nine external action instances and the seven
reachable build-tool invocations. Preserve all earlier source interfaces and
historical review snapshots. Do not execute inspected commands or fetch remote
action implementations to infer their behavior.

1. Independently bind each subject's current callers and argument variants.
   Require a reviewed owner/profile consistent with the existing caller review,
   an exact observed-variant boundary, failure/recovery requirements and later
   source, artifact, supply-chain, authority and recovery evidence obligations.
2. Enumerate and content-bind supported literal imports, local source references,
   reachable build configurations and their source-file membership. Added or
   changed members invalidate review. Declare the bounded grammar; unsupported
   language/configuration features, generated artifacts and dynamic enumeration
   remain explicit unresolved findings. Literal reference extraction cannot
   establish complete arbitrary-program behavior or whole-estate import closure.
3. Account separately for each external action instance, its exact reference,
   explicit inputs, condition, upstream output references and inherited execution
   context. Mutable references, action defaults and remote implementation remain
   unresolved. A pinned reference alone never proves action behavior or authority.
4. Reconcile every discovered subject, invocation, observation and dependency
   against a closed versioned contract. Generated bindings remain pending.
   Contract completion means exact source accounting; source closure and runtime
   qualification remain blocked until independent evidence can establish them.
5. Add safe CLI modes, guarded source-result consumption, positive/negative
   fixtures, mutation tests, documentation and a new dated review candidate.
   Run focused tests and the established clean-environment verification command.

This unit makes the selected arguments and dependency declarations checkable; it
does not silently resolve the existing opaque script/tool/action findings.
In particular, generated package shims and dynamically selected built tests need
exact-artifact proof, and conditional publication does not reduce inherited
workflow permissions. The complete seventeen-stage release matrix remains the
authority for later gates.

Next unit: supported semantic coverage for the remaining dynamic/script/action
boundaries and build/import resolution, followed by exact-artifact qualification
for the selected image-publication family as its inputs become known. Broader
source adoption, evidence admission and provider/live qualification stay open.

### Fifth source delivery unit evidence — 2026-09-29

The selected operation input-accounting unit is complete, locally verified and
uncommitted. Two closed schemas, independent operation/action collectors,
generic contract reconciliation, public `--operations` commands, guarded result
consumption, inert fixtures, tests and documentation extend the existing gate.
No selected deployment script, action reference or workflow behavior was changed.

The [dated source review candidate](../../../../docs/04.deploy/plans/release-control-source-adoption/2026-09-29-operation-contracts/README.md)
accounts for nine scripts, nine action instances and seven build-tool subjects:
25 incoming variants, 1,495 observations and 731 dependency relationships across
238 bound source records. Current caller ownership/profiles and exact observed
inputs are acknowledged in reviewed source contracts. The selected caller graph
is unchanged from the fourth unit. All 148 combined caller/operation findings
remain visible; contracts are complete while source closure and qualification
remain blocked and authorization false.

The bounded collector binds supported literal references and build membership;
it does not prove arbitrary language behavior, TypeScript emission, generated
runtime membership or remote action implementation/defaults. All nine action
instances still use mutable tags. Conditions do not reduce inherited declared
permissions. The full seventeen-stage matrix remains required; supplementary
obligations reference stages 3, 6, 7, 8 and 15 without waiving other gates.

The clean-environment wrapper passed, exit 0: **390 tests** (262 prior and 128
new), legacy smoke cases, generic provider/network checks and metadata validation
for 33 files. Actual public commands accepted the fresh operation contracts and
their saved result for source analysis; both release-eligibility and operation-
authorization consumption were rejected. Independent review verified repairs
for unbound competing import candidates, stale empty caller graphs, private
dotenv variants and inconsistent discovery schema validation. Hard resource
limits reject truncated collection. Only the internal inventory node budget
was enlarged explicitly; ordinary file byte/node limits remain unchanged.

The fresh estate snapshot contains 303 sources, 1,111 observations and 193 open
findings: 188 Phase 2 and five Phase 3. The eight new implementation/test modules
account for the additional findings. No earlier finding or adoption obligation
was silently closed. Earlier dated snapshots remain intact.

Next delivery unit: workspace-aware build/import resolution for the seven
selected TypeScript invocations, followed by binding generated shim/runtime-test
membership to exact emitted artifacts. Keep arbitrary script behavior and remote
action implementation obligations explicit; extend them through supported
semantics or later evidence, not declarations. Broader adoption, authenticated
evidence/authority and provider/live qualification remain open. No real stop
condition exists within this completed bounded slice; no external mutation,
deployment execution or Git publication occurred.

### Sixth source delivery unit — workspace build resolution and artifact accounting

The user authorized the recorded next source unit. Extend the existing public
gate with independent discovery for the seven selected build invocations:
workspace manifests/exports, local compiler inheritance, bounded aliases,
literal imports and predicted output membership. Bind source bytes and collector
versions; ambiguous or unsupported semantics remain explicit findings.

Keep no-emission checks, declaration builds and JavaScript builds distinct.
Do not equate all emitted test files with tests selected by a runtime runner.
Observe generated package forwarding targets and selected test membership using
a declared bounded grammar; unsupported generators cannot qualify by declaration.

An optional read-only local artifact comparison may bind actual file bytes to
the current predictions. It must reject missing/extra outputs, invalid forwarding
targets, source fallback, unsafe paths and stale supplied identities. Local
membership accounting cannot establish compiler provenance, runtime behavior,
supply-chain admission, release eligibility or operation authority. Preserve
those blocked states even when a fixture's file accounting is complete.

No application/TypeScript dependency installation or legacy deployment-script
execution is needed for this source unit. This worktree has no installed TypeScript
compiler or actual output tree; final-artifact evidence therefore remains open.
The next unit must introduce a reviewed isolated build/provenance path and actual
artifact execution proof, alongside deeper semantics and wider source adoption.

### Sixth source delivery unit evidence — 2026-09-29

The workspace build resolution and local artifact-accounting unit is complete,
locally verified and uncommitted. Two closed schemas, two independent collectors,
a schema/reference validator, public `--builds` mode, inert fixtures, focused
tests and documentation extend the existing realization gate. The existing
staging workflow, selected build scripts and caller graph are unchanged.

The [dated workspace build review](../../../../docs/04.deploy/plans/release-control-source-adoption/2026-09-29-workspace-builds/README.md)
records seven builds across 209 sources, 6,596 bindings and 3,958 dependency edges,
with 46 explicit unresolved findings. Two no-emission checks and the server
runtime-test build have bounded source predictions. Four builds retain unresolved
resolution/emission conditions. All seven still require compiler/toolchain and
exact-artifact proof; neither a predicted member nor a source finding is a
runtime result.

Optional read-only artifact comparison binds actual bytes and membership to
fresh source observations, recognized package forwarding files and selected
runtime-test membership. The supported image/server-test/product-test generators
describe 35/21/26 export forwards. Exact audited helper/scaffold identities
bound that grammar. Only synthetic fixtures were compared: no actual compiler,
generator, runtime-test runner or deployment program was executed. Accounting
success retains unproven provenance, blocked qualification and false authority.

Final isolated clean verification returned **exit 0: 508 tests**, comprising
390 previous tests and 118 new tests (49 build collector, 50 artifact binder,
19 public CLI), plus legacy smoke, provider/network boundaries and metadata
headers for 36 files. The initial clean run passed 507 tests but identified two
missing fixture metadata headers; these and one additional malformed-unused-
mapping regression were resolved before the final complete run. Whitespace and
final documentation metadata checks passed.

Fresh public commands reproduced the saved build inventory (expected exit 1
with unresolved findings), the estate intake (exit 0, classification complete,
coverage blocked) and synthetic artifact result (exit 0, local accounting only).
The current estate record has 312 sources and 200 open findings: 195 assigned
to Phase 2, five to Phase 3. Seven added implementation/test modules explain
the seven additional findings; no previous obligation was waived.

Independent review and regression tests cover omitted/missing inputs, dotted
extensionless imports, long named imports, scoped-name diagnostics, legitimate
`secrets.ts` code versus excluded private directories, malformed unused path
mappings and generator changes that could otherwise hide shim obligations.
Large observation arrays use explicit linear identity checks instead of
quadratic schema uniqueness checks.

Next delivery unit: introduce a reviewed isolated locked TypeScript build path,
reconcile real compiler resolution/emission with source predictions, bind genuine
output to source/lock/toolchain identities, and exercise exact artifact commands
and selected tests. Deeper script/action semantics and wider adoption remain
open, followed by authenticated evidence/authority, provider integration and
approved live qualification. PostgreSQL Stage 6 stays later.

No real stop condition exists within this completed bounded unit. No external
mutation, live deployment, Git publication, commit, reset, discard or other
worktree change occurred.


### Seventh source delivery unit — locked local build and execution evidence

The six source units were checkpointed at `094d6418`, with session bookkeeping
at `27d81529`. A WSL restart cleared the original memory-backed worktree; the
branch and all 112 foundation file objects survived verified hash checks. The
authorized recovery restored the same branch into persistent ext4 storage.
Historical unit statements about uncommitted work are superseded by this record.

This unit extends the existing realization capability with a pinned Node/npm/
TypeScript dependency closure and real compiler observations for the seven
selected configurations. Actual compiler bytes, module resolutions and outputs
are bound to selected source and lock identities. Generated runtime forwarding
packages and the two existing selected test runners are exercised in disposable
source-free environments, with network namespaces and read-only inputs. Image
shim generation does not constitute a Docker build or final-container proof.

The execution wrapper requires persistent scratch storage, never a RAM-backed
`/tmp` build tree. Public dependency acquisition is a separate explicit step;
installation and execution are offline. Closed versioned contracts, adversarial
fixtures and exact byte checks reject stale or inconsistent local observations.
All successful local results keep source closure, release qualification and
authority blocked. A diagnostic single-configuration run identifies its subset;
delivery acceptance includes all seven configurations and the required runtime
receipts, followed by the complete source validation suite.

Completion evidence will record the actual results, any ordinary source repairs,
changed inventory identities and precise gaps. Next acceptance work is final
container construction/exact-command qualification and the first hosted source
check after separately approved publication. Broader Phase 2 adoption, remote
action semantics, authenticated evidence admission, durable operation controls,
provider adapters and live qualification remain open.

### Seventh source delivery unit evidence — 2026-09-29

The locked local build/execution unit is complete and verified after recovery.
The [dated locked-build review](../../../../docs/04.deploy/plans/release-control-source-adoption/2026-09-29-locked-builds/README.md)
contains the actual all-seven result and a compact verification summary. Four
closed schemas, a verified Node 22.23.3/npm 10.9.9/TypeScript 5.9.3 closure,
offline sandboxed build wrapper, real compiler observer, runtime receipt binding,
fixtures and tests extend the existing capability. No application/configuration
repair or deployment-workflow replacement was needed.

Final clean verification passed 677 tests in 21 suites, legacy smoke, core
provider/network boundaries and 39 metadata headers (exit 0). Real compiler
fixtures passed 33 additional tests with zero skips (exit 0): 710 distinct tests.
All seven real compiler invocations passed; both existing selected runtime-test
runners and image shim generation passed. The exact selected test files, source,
lock, implementation, compiler input/resolution/output and artifact identities
are preserved. An actual isolation probe confirmed protected inputs, blocked
external routes and available private loopback.

The accepted result is `sha256:4724812c2efbf86e344519ec90ef1633b19402d360cf9571758f297aa342fcb9`.
Two extra incremental build-information files are recorded; no predicted output
is absent. Four source predictions remain unresolved. Compilation and the two
selected test files do not imply whole-estate source closure, complete action
semantics, a constructed container, startup qualification, hosted validation or
provider proof. These unsigned local observations retain blocked release
eligibility/operation authority and are rejected by the common result consumer.

Ordinary recovery repairs included draft runtime interface/binding corrections,
verified partial-cache resume and a compiler-observer fix for Node10/baseUrl
existence probes. Unsafe explicit reads/writes remain blocked. The dated review
records failed initial attempts and their successful replacement evidence.

Next delivery unit: isolated final-container construction and exact-command
qualification, binding base image, build inputs, image digest and startup/runtime
receipts under the common authority boundary. The first hosted source-validation
run remains separately pending approved publication. Wider Phase 2 adoption and
action semantics, authenticated evidence admission, durable operation controls,
provider adapters/stores and live qualification remain open; PostgreSQL Stage 6
stays later. Earlier dated estate counts remain historical. No local stop
condition remains, and no external mutation or deployment was performed.

### Eighth source delivery unit — exact local container evidence

The user authorized continued implementation after clarifying the distinction
between server startup and database bootstrap. Extend the existing image build
and smoke wrappers with controlled local qualification in the operational-
realization capability. Reuse the locked image compiler/generator output and
production dependency closure, and the existing Dockerfile's shared final
runtime recipe, with an explicitly pinned runtime base and isolated context.

<!-- deterministic-check: allow reason="This acceptance invariant is enforced by local_container.py and local_container_contracts.py; the prose documents the implemented gate." -->
The selected local image must contain exactly the verified payload and run its
default server command under restricted local conditions. Require both health
checks, graceful shutdown, owned-container cleanup and safe image-bound evidence.
Keep every declared AWS task and sidecar as a separate pending obligation;
server health cannot qualify bootstrap, migration, worker, relay or restore.
The original workflow build path remains compatible and unqualified by this
new mode's receipts. Later adoption must promote the exact tested image rather
than rebuilding it and reusing earlier evidence.

This unit does not provide real database initialization, IAM/secret/network
proof, source-estate closure, full supply-chain admission, trusted evidence
storage or release authority. The next unit must qualify the packaged finite
commands separately against disposable dependencies before later AWS preflight
and controlled target execution. PostgreSQL Stage 6 remains paused. Completion
requires the real image run, focused positive/negative tests, clean local
verification, durable safe evidence and a session record.

### Eighth source delivery unit evidence — 2026-09-29

The exact local container unit is complete. The [dated container review](../../../../docs/04.deploy/plans/release-control-source-adoption/2026-09-29-local-containers/README.md)
preserves the full accepted public-wrapper result and verification summary.
Two closed schemas, an immutable runtime lock, engine/payload/profile helpers,
fixtures, wrappers and focused tests extend the existing realization capability
and shared Dockerfile. Legacy workflow behavior remains compatible; its images
cannot inherit the new mode's proof.

Canonical clean validation exited 0: 933 tests in 26 suites, legacy smoke,
provider/network core boundaries and 41 metadata headers passed. A fresh genuine
image compilation/generation/build and exact-image inventory/run exited 0.
All 3,902 payload files (19,405,615 bytes) and 57 production packages matched;
both health checks passed, SIGTERM exited 0 and owned cleanup verified. Only the
local image-default profile passed; 13 separate task/sidecar obligations remain
pending. Compiler Node 22.23.3 and runtime Node v22.22.0 are recorded separately.

Result identity: `sha256:0194119d38fc994e060f681de8b2c0da0ecc5884a99b52a9499d2b29759d14b7`.
Image identity: `sha256:5c4f1e9164a260bf26169a19957a6bec6d19c52a2c20fc9602d519bb813b891d`.
The receipt binds the actual source/helper bytes and records the pre-checkpoint
HEAD as a label. It is unsigned local evidence with all release/operation
permissions blocked. Docker/host versions are observed, not fully pinned;
build-step network isolation does not claim daemon registry-metadata isolation.

Acceptance repaired a remaining legacy certificate-stage dependency and the
Docker configuration-ID/manifest-ID distinction; bounded metadata binding and
negative regressions precede the successful complete rerun. No AWS, hosted
workflow, live database or application source change occurred.

Explicit next delivery unit: qualify packaged finite commands separately against
disposable dependencies, then later AWS preflight and controlled target work.
PostgreSQL Stage 6 stays paused. Hosted validation after approved publication,
wider adoption/action semantics, authenticated admission, durable controls and
provider adapters/stores remain open. No local stop condition exists.

### Ninth source delivery unit — reusable finite execution conformance

The user clarified that PostgreSQL readiness was a scheduling question, not a
request for a PostgreSQL implementation slice, then authorized continuation.
The IaaS programme remains primary. The eighth-unit queue wording about packaged
finite commands is refined: first establish reusable finite-execution protocol
conformance in the existing realization engine, using inert packaged fixtures.
No PostgreSQL, AWS adapter or product task implementation is part of this unit.

Closed profile/result contracts bind image, payload, command, schema revision,
fresh attempt, output/deadline limits, terminal checks and cleanup. Real fixture
execution exercises completion and refusal paths through the existing smoke
wrapper. Terminal claims remain semantic-unverified; product-profile updates
stay empty and release authority stays blocked. This unit cannot close Phase 3
or promote the thirteen pending target-task/sidecar obligations.

The next Phase 3 unit is reusable independent effect/dependency verification
and required artifact admission, retaining all actual command-specific proof
obligations. Source coverage gaps remain open. Durable operation journal/lease/
fencing, AWS integration and per-task preflight, followed by controlled target
qualification, retain their later gates. PostgreSQL Stage 6 is a readiness
milestone within that programme and stays paused. Completion evidence follows
a frozen conformance run and canonical source verification.

### Ninth source delivery unit evidence — 2026-09-29

The reusable finite-execution conformance unit is complete. The dated review at
`docs/04.deploy/plans/release-control-source-adoption/2026-09-29-finite-jobs/`
contains exact public conformance output, safe product-server compatibility
observations, the verification summary and scope limitations. Two versioned
schemas, contracts, the shared engine extension, the existing smoke wrapper,
inert fixtures and focused tests extend the IaaS capability. PostgreSQL/product
source, AWS resources and deployment workflows were not changed.

Final canonical clean verification exited 0: 1,165 tests in 29 suites, legacy
smoke, provider/network boundaries and 44 metadata headers passed. The 232 new
tests cover contracts (102), engine behavior (45) and CLI/conformance (85).
The final real fixture run exited 0 in 64 seconds: two completed executions,
eight expected failures and one expected timeout, with eleven unique attempts
and eleven verified cleanups. The previously qualified immutable product image
also passed both server health checks, graceful shutdown and cleanup using the
final extended runner. That observation is compatibility evidence only.

Review found and repaired a concrete alternate-source-root binding defect:
supplied helper/schema bytes now have to match the actual executing modules and
loaded schemas before building. Four mismatch negatives and an identical-copy
case cover it. A fresh complete clean run and real conformance rerun passed
following repair. Earlier 1,160-test verification and uncommitted review
artifacts remain historical; superseded review files were preserved outside Git.

Independent final review matched current source/schema/lock/head/profile
bindings, reproduced all four refusals and checked all thirty-six consumer
rejections. Result: `sha256:19e6ce477cb6d3585895610a15e3de175d1be5a1ff14e4742541f2df69efa5bd`.
Image: `sha256:e93bfa52c2f33375b3e9c5daad2a76f10bf3e91a1a98beec155085e103ccd4c4`.
Runner: `sha256:f0406d0621586365f8f4a9ab6dca2257ffd26d8298d6d18c32d70c9bb97e36b4`.

Every job's semantic effect remains unverified and all release/operation
permissions remain blocked. Product-profile updates are empty; the thirteen
pending target-task/sidecar obligations stay pending. A completed protocol is
not independent business-state verification or durable execution authority.

Explicit next unit: continue Phase 3 reusable independent effect/dependency
verification and required artifact admission, retaining actual command-specific
proof obligations and open source-coverage gaps. Durable operation controls,
AWS adapters/per-task preflight, hosted validation after approved publication,
and target qualification remain later. PostgreSQL Stage 6 stays paused as a
readiness milestone in the IaaS programme. No local stop condition exists; no
provider mutation, publication, push, merge, reset or other-worktree change
occurred. The local checkpoint is authorized under the continuing source batch.

### Continued full-programme source batch — 2026-09-29

The user chose to retain the existing full IaaS plan after considering a narrower
AWS/PostgreSQL milestone, and authorized progressing through multiple delivery
units per batch. No target-scoped exception or prerequisite reduction is adopted.
The requested 2026-10-03 completion date is a delivery target, not a promise or
permission to omit acceptance work. The 28-day observation milestone necessarily
extends beyond that date. External provider mutation, publication and hosted
activation retain their existing separate approval boundaries.

Execute independent source work in parallel where file ownership and contracts
permit it; accept each delivery unit independently with contract, implementation,
focused positive/negative tests, public wrapper, documentation, local evidence,
session record and next queue entry. Do not count multiple internal tasks as
additional completed delivery units. The previously discussed 15–20 remaining
slices is a planning estimate, not an approved fixed decomposition.

Current queue: independent finite-job effect/dependency verification and artifact
admission; remaining source coverage/contracts; durable execution/journal/locking
and evidence; AWS adapters and per-task preflight; orchestration/adoption; approved
target qualification and ongoing assurance. Preserve the existing engine and all
open actual-command, whole-estate and provider proof obligations. PostgreSQL Stage
6 remains a readiness milestone under the unchanged plan. No new external action
is authorized by this batch declaration.

### Tenth through twelfth source delivery units — accepted batch

The three independently bounded source units are complete: packaged dependency
side-effect verification; pinned offline cryptographic artifact-evidence
admission conformance; and CloudFormation structural reference coverage. Their
schemas, implementations, focused positive/negative tests, existing public
wrappers, fixtures and dated review receipts are included in this checkpoint.
These units extend the existing realization gate; they do not complete Phase 2,
Phase 3 or the full release-control programme.

Final frozen-source clean verification exited 0: **1,455 tests in 38 suites**,
legacy smoke, provider/network boundaries and **51 metadata headers** passed.
The complete local log hash is
`b1f0c2cc9645deb1b1c973aec4c42c8d7fb35f4e165f0402457043e75a0e69b2`.
Dated review directories under
`docs/04.deploy/plans/release-control-source-adoption/` retain safe normalized
receipts and verification summaries for dependency effects, artifact admission
and infrastructure references. Raw credentials, raw dependency logs and private
scratch databases are excluded.

The final fresh dependency run passed nine packaged command cases (four success,
five expected failure), ten independent effect assertions and owned cleanup.
All 3,902 payload files and the full upstream build receipt were retained and
independently matched to current source, schema, lock and runner bytes. The
qualified local image is
`sha256:03432806c5bf2b4e39ea43a52b8722346b1d4e223eb9b9c2fc021c8d785ad512`.
Bootstrap and migration effects include verified TLS/password authentication,
roles/schema/history, runtime DDL refusal, transactional DML, repeated-operation
stability and four deliberately revoked privileges. The production RDS CA
remains the default; staging descriptors reject local qualification overrides.
All actual relay/worker/restore and other target-task/sidecar obligations remain
open. This is disposable IaaS proof, not live PostgreSQL Stage 6.

The pinned offline verifier passed twelve real cryptographic cases: one authentic
public signature accepted and eleven mutations refused. Production publisher
materials, signed scans and owner-reviewed scanner assurance/freshness remain
open. SBOM shape/subject checks do not establish independent component completeness.
All nine checked source-result consumer uses of effect, build and cryptographic
conformance receipts were refused, including release and operation authority.

Same-source comparison covered 376 files in both collectors. Current inventory
has 1,813 observations and 223 findings, compared with 1,235 and 244. Exactly 23
unsupported template findings were resolved structurally; all other 221 baseline
findings remain, and two new findings expose seven provider-resolved parameter
dependencies. The graph contains 442 reference edges and 129 symbols. This is
precise supported syntax coverage, not whole-estate closure or provider proof.

Acceptance preserved failed attempts and repaired initializer socket handling,
non-resource imports, provider-resolved parameters and safe upstream diagnostics.
The first clean attempt failed metadata after 1,423 tests; an intermediate 1,439
test pass preceded later repairs. The third attempt overlapped test authoring and
failed twelve test-helper errors. Only the frozen fourth run above is final
canonical evidence. An earlier dependency refresh returned a generic error whose
underlying cause was not retained; reviewed fixed-code diagnostics now preserve
known upstream failures and redact all unknown/private values. Final real build
and clean verification ran sequentially and passed without relaxing deadlines.

ADR disposition: this batch implements the accepted plan and existing ADR 0038
boundaries; it introduces no provider authority or production policy decision.
Explicit next units: provider-neutral local durable journal/lease/fencing/evidence
conformance; existing-caller/lifecycle coverage and adoption delta; then durable
finite-engine interruption reconciliation. Scratch preparation is underway in
parallel; repository integration follows this checkpoint. AWS adapters, production
artifact producers, orchestrator/caller adoption, hosted validation and approved
target qualification remain queued. PostgreSQL Stage 6 stays paused. No real
local stop condition exists; no external provider mutation, publication, push,
merge or other-worktree change occurred.

### Resumed delivery batch — implementation and focused verification

Local durable operation-control contracts, journal/lease/fencing/evidence store,
existing-gate CLI, fixtures, documentation and ADR 0039 are integrated. The known
test API typo was corrected; 82 tests initially passed. Independent review found
that conformance did not bind the public wrapper bytes. Seven helper/wrapper
files are now bound, with one new mutation test: 83 registered focused tests;
12 conformance and 20 CLI cases passed after the change. Fresh public conformance
passed ten cases, seven real subprocesses and three deliberate kills with exit 0
and empty stderr. Safe normalized evidence is retained in the 2026-09-30 control
store review. Full canonical acceptance remains pending.

The reviewed aggregate-caller draft was integrated only after exact base and
source hash checks: twelve additions and one compiler modification. It has 66
focused cases and independent review, plus selected-workflow compatibility. The
existing public coverage mode now supplies its current root for fresh internal
reconciliation; all 34 source-coverage compatibility tests passed. Public new-mode
and result-consumer integration is being completed. Adoption results deliberately
remain pending proposals and cannot be consumed as authority or approved review.
Final same-snapshot inventory/reconciliation/adoption evidence is still pending.

Finite-engine recovery remains isolated draft work. Review found a real ordering
defect: unresolved cleanup could be followed by start using an earlier created
observation. That must be repaired and independently retested before integration.
An automatic approval review briefly misclassified the owned scratch directory
as another worktree. Read-only ownership/Git checks established it is a plain
same-owner directory; the narrowed reviewed source action was then approved.
No other worktree was changed. Real Docker interruption proof, exact identity
reconciliation and bounded cleanup remain required acceptance work.

Next: accept and checkpoint durable controls plus caller coverage after frozen
canonical verification, then complete and integrate the existing finite-engine
recovery unit. Provider adapters/stores, actual artifact producer/scanner policy,
remaining source coverage, orchestration and approved live qualification remain
open. No current external mutation or policy boundary blocks this local batch.

### Thirteenth and fourteenth source delivery units — accepted batch

Local durable operation controls and aggregate repository caller coverage are
complete within their declared source-only boundaries. Schemas, implementations,
positive/negative fixtures and tests, existing-gate public modes, documentation,
ADR 0039 and dated normalized review evidence are included. Final frozen clean
verification exited 0: **1,645 tests / 46 suites**, legacy smoke, provider/network
boundaries and **56 metadata headers** passed. Full log SHA-256:
`2e90981daf46dbc6edd31b57b1b6362570e0ab6dd13241af96c42ad710bcb986`.

The durable-store unit has 83 focused tests. Fresh public conformance passed ten
cases, seven subprocesses and three deliberate kills with exit 0/empty stderr.
Receipt: `sha256:669ca23d3884042cf8a412371cbe7e1c24029e877bee632d1981ab243cb6d080`.
Intent, scope conflicts across releases, fences, journal/evidence checks, lease
expiry and cleanup persist across tested process interruption. Seven helper and
public wrapper files are bound. This local reference does not prove host reboot,
power loss, distributed operation, independent authenticity or production policy.
All three common consumer purposes refuse the conformance receipt.

The caller unit has 66 collector/reconciliation/migration tests, 24 public tests,
45 consumer and 19 consumer-CLI tests, including existing compatibility cases.
Existing coverage (34 tests) and selected workflow callers (31) also passed.
Independent review accepted closed output validation and fresh recomputation.
Final same-source public outputs matched independent recomputation: 403 sources,
175 roots, 602 nodes, 522 edges and 188 structural observations. Of 240 raw source
findings, exactly 20 resolve structurally and 220 remain. Another 350 graph boundary
findings have different scope and are not an additive source-defect count.
Inventory: `sha256:f02f8c06bf4a6d96a0d0c7bc46585bade9d8dcecd6eb40949c47df57f0e81356`.
All 403 adoption rows remain pending (130 added, 21 changed, 252 unchanged, zero
removed). The historical ledger is unchanged. Both actual public modes return 1,
as required for unresolved coverage and pending adoption; they confer no authority.

The existing finite-engine recovery draft independently passed 70 focused tests,
108 shared-engine regressions and eight real interruption cases. It remains outside
the repository and unaccepted until public integration and fresh integrated proof.
An unresolved reserved create correctly remains unknown without blind retry.
The explicit next delivery unit is that recovery integration. Remaining package
and action semantics, production artifact evidence, durable provider stores, AWS
adapters/preflight, orchestration/adoption and approved target qualification remain
open. PostgreSQL Stage 6 stays paused. There is no current local stop condition;
no provider mutation, publication, push, merge or other-worktree change occurred.

### Fifteenth source unit — integrated recovery proof

Copied only nineteen manifest-listed recovery source paths after exact source and
base hash checks, then connected the existing gate dispatch, seven versioned
schemas, five canonical suites and documentation. Ninety focused recovery/public
boundary tests and 108 existing Engine regressions passed together: 198 tests,
78.803 seconds. Independent final public review passed 31 tests in 2.295 seconds.
Output is revalidated against the closed schema, self-digest and current runtime
binding; shell/Python wrappers are included. All consumer purposes refuse aggregate
and per-attempt recovery receipts; source recomputation cannot dispatch this mode.

Fresh frozen integrated conformance exited 0 with empty stderr. Eight actual
Docker scenarios passed, including seven killed/reopened private processes.
Seven operations closed with verified owned cleanup. An unconfirmed consumed
create stayed unknown without replay; every scenario independently proved exact
owned container absence. Receipt:
`sha256:74f7d69142ee6e23da31ae52d6df42c3e2ff2feb23a4c4db722c592057c3d319`.
Runner: `sha256:1c1bdbe8a6e953f10a52659446e2ddf2d5cda0ca01eece118634586c3c1c991b`.
The image is the existing qualified inert fixture; no image pull/build or provider
operation occurred. The complete clean verifier is running against frozen source.
This unit remains pending canonical acceptance; older scratch passes are historical.

The next source unit is compiler-backed package-export reconciliation. Read-only
assessment found twenty opaque export-target findings for thirty-eight declarations
across twenty manifests, and three handwritten runtime maps. The image map omits
three declared core exports and retains a server main alias required by an existing
entrypoint. Independent scratch work will derive mappings from manifests and actual
TypeScript emission, preserving that alias through explicit source-bound compatibility.
No unfinished scratch files are integrated. Production evidence/stores, AWS adapters,
release orchestration/adoption and approved target qualification remain open.
No current local stop condition exists; PostgreSQL Stage 6 remains paused.

### Fifteenth source delivery unit — accepted

Durable local finite-engine recovery is complete within the reviewed inert-fixture
boundary. Final clean verification exited 0: **1,735 tests / 51 suites**, legacy
smoke, provider/network boundaries and **58 metadata headers** passed. Log SHA-256:
`52020da926dc277b62f52a63e6c24cccba35de4b2a2b4765c8b3e5666b20be0c`.
The preceding full attempt passed all tests but failed one missing README used_by
metadata link. That documentation-only omission was repaired; both the exact
metadata command and the complete clean wrapper passed afterward. No functional
source or real receipt binding changed during the repair. Earlier failure evidence
is preserved instead of relabeled.

The retained real receipt still matches the exact final runtime binding and records
eight passed cases, seven killed/reopened processes, seven safely closed operations
and one deliberately unknown consumed-create operation. Every exact owned fixture
resource was independently absent. Schemas, immutable action journals, shared Engine
transport, controller, public gate mode, fixtures/tests, README and normalized review
evidence are included. ADR 0039 covers the local reference boundary. No provider,
product semantic, distributed/power-loss or production authority claim is made.

Next delivery unit: compiler-backed package-export reconciliation. Its two owned
scratch drafts extend actual TypeScript emission observations and replace three
handwritten runtime maps with source-bound projections. They are unaccepted until
integration, independent review, genuine locked build/runtime proof and canonical
verification. All future production evidence, stores, adapters, orchestration and
approved target work remains queued. PostgreSQL Stage 6 stays paused; no current
local stop condition exists and nothing has been published or pushed.


### Sixteenth source delivery unit — integration in progress

Compiler-backed package-export reconciliation now replaces the three handwritten
runtime maps in the existing image preparation and server/product test runners.
Only 37 reviewed manifest-listed source, schema, test and documentation paths
were integrated after every base and output hash matched. The independent source
collector retains all export declarations and executable/owner obligations. New
versioned emission observations bind actual compiler source-to-output callbacks;
modern runtime receipts bind the exact compiler-plus-generated file union. The
server-main image alias remains explicitly source-bound. Direct generators reject
saved projection arguments and freshly verify current outputs; their stricter
pinned-version/Python prerequisites are documented. The isolated locked path
compiles once and uses a fixed internal driver. All release/operation authority
remains blocked.

Independent review accepted the projection, current declaration joins, safe file
reads, private handoff, exact artifact union and authority boundary. The combined
focused suite is running; fresh all-seven locked compilation/runtime acceptance
and canonical clean verification remain outstanding. Container consumer review
identified a duplicated legacy embedded build schema; a narrow compatibility
amendment is being verified before source freeze. Prior container receipts remain
historical and do not qualify changed output bytes. This unit is not accepted yet.

Next: finish that compatibility amendment and integrated evidence, then reconcile
the next supported caller/action boundary into estate coverage while preserving
owner and executable-behavior blockers. Production artifact evidence, durable
provider stores, AWS adapters/preflight, release orchestration/adoption and approved
target qualification remain open. PostgreSQL Stage 6 stays paused.


### Sixteenth source delivery unit — accepted

Compiler-backed package exports are complete within the local execution scope.
The final all-seven normal wrapper exited 0 with empty stderr: seven compiler
checks, both selected runtime-test runners and image preparation passed. All
38 declarations are accounted for per runtime: server 27 selected/11 outside,
image 37/1 plus its explicit server-main alias, product 38/0. The image now
contains the previously omitted core files/localization/security forwarding
entries. New receipts bind exact compiler/generated membership and preserve
all remaining source, behavior, owner and authority obligations.

Final clean verification exited 0: **1,834 tests / 57 suites**, legacy
smoke and provider/network boundaries, and **61 metadata files** passed. Another
44 genuine compiler fixtures and five direct-command compiler fixtures passed
without skips: **1,883 distinct tests**. Independent current-source receipt
verification passed with 54 consumer refusals and exact 40-file/source/runner/
selected-graph bindings. Result: `sha256:d728989d9ac3c36c3b6ecd43e5c32e683884798405e92a5b33f325b22a207a2b`.
Clean log SHA-256: `7230c1cd8538a3733f7ebb8deb7a954a9009ac78ffa014d73ec2f7a40d48422b`.
Dated normalized evidence is in
`docs/04.deploy/plans/release-control-source-adoption/2026-09-30-workspace-exports/`.

The actual product workspace-resolution refusal and stale payload test path
were repaired and freshly reverified; both first failed attempts remain recorded.
Changed generated artifacts require fresh final-container qualification; older
receipts stay historical. No AWS, GitHub, DNS, secrets, live PostgreSQL, main or
other worktree was changed. Nothing was pushed or published.

Explicit next unit: immutable workflow action material and input/default
reconciliation using the existing collectors/contracts. Production artifact
evidence, durable provider stores, AWS adapters/preflight, orchestration/adoption
and approved target qualification remain queued. PostgreSQL Stage 6 stays paused.
