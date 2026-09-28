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
- A target mutation still needs explicit current-chat approval under
  `.agentic/aws/workflows/execute-approved-aws-change.md`.
- The control plane records secret *references and schemas*, never values,
  tokens, request bodies, raw provider responses, task IDs or customer data.
- Release operations fail closed on unresolved coverage, changed source/artifact
  identity, unsafe scope, stale evidence, missing rollback, or uncertain
  external outcome.
- A normal release may never use a break-glass exception. An emergency action
  has an independently auditable, time-bounded exception record and mandatory
  post-incident review; it cannot silently become the normal deployment path.
- The new recurring AWS cost must be estimated and approved before it is
  created. Initial source work requires no cloud mutation.

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
| 6 | **Exact-image tests:** does every real container command run in its final artifact under actual user/filesystem/security constraints? Evidence: final digest, command, exit/semantic receipt and shutdown/cleanup result. | Phase 3 exact-artifact qualification; finite-job profiles. | Reject host-workspace, import-only or server-only substitution. Rebuild and qualify the exact command before publication/promotion. | Server: yes. Bootstrap/migration/relay/worker/restore: insufficient. |
| 7 | **Supply-chain proof:** is the artifact immutable, scanned, SBOM/provenance-attested and tied to source? Evidence: verified digest, SBOM, scan policy result, attestation/provenance, base artifact and signature receipt where supported. | Phase 3 supply-chain admission. | Reject unknown, unsigned/unverified, stale, vulnerable beyond policy or source/digest-mismatched artifact. Rebuild from reviewed source. | Present. |
| 8 | **IaC static validation:** do rendered templates, IAM, network, encryption, tags, alarms, retention and references match target policy? Evidence: rendered-template, policy, schema and negative-test receipts. | Phase 2 discovery; Phase 5 target-composition compiler and AWS adapter fixtures. | Reject invalid template/reference, policy mismatch or unmodelled resource edge. Correct source; do not attempt provider execution. | Largely present; becomes one compiler gate. |
| 9 | **Change-set review:** does the actual provider plan contain only allowed changes? Evidence: immutable safe change summary bound to release, target fingerprint, permissions/cost delta and reviewed rollback. | AWS CloudFormation change-set operation profile; Phase 6 `plan`. | Reject replacement/destructive/broader-scope/unexpected-cost change. Revise composition or create a separately reviewed recovery plan. | Present and working. |
| 10 | **Drift and dependency preflight:** are account, region, quotas, capacity, cost boundary, resources and stack state expected? Evidence: fresh normalized observed-state record. | Phase 0 inspection; Phase 5 capacity/limit adapter checks; Phase 8 candidate entry. | Reject stale/mismatched account/region, drift, insufficient capacity, unavailable quota or unapproved cost. Reconcile or safely remediate before a new plan. | Present for reviewed boundaries; must become one readiness contract. |
| 11 | **Candidate runtime proof:** can the immutable image start safely without serving production traffic? Evidence: profile-specific candidate receipt for service or job, including actual identity, image, command and observation route. | Phase 3 exact image; Phase 4 non-mutating candidate mode; Phase 8 qualification. | Reject server-only proof for a finite task, old-revision health, or candidate with no observable terminal result. Fix candidate prerequisites before live operation. | Present for the HTTP server only. |
| 12 | **Per-task live preflight:** can every selected task use real IAM, injected secret schema, network, TLS and logging/evidence paths without writing business state? Evidence: no-effect preflight receipt per task/profile. | Phase 4.6; Phase 8.2. | Reject any missing command, identity, input, network/TLS or observation capability. Reopen design; do not use a state-changing run as diagnosis. | Missing; decisive Stage 6 gap. |
| 13 | **Controlled state change:** can bootstrap/migration/relay/worker run once, idempotently and within a bounded blast radius? Evidence: operation journal, semantic completion, effect receipt, fence/idempotency proof and cleanup. | Phase 4 controller; Phase 8.3 ordered operation graph. | Stop on unknown outcome, duplicate ownership, non-idempotent effect or budget breach. Reconcile journal before retrying; use declared compensation/forward repair. | Not proven because bootstrap has not passed. |
| 14 | **Post-change verification:** are health, authorization, queue/database invariants, telemetry, alarms, cost and steady state correct? Evidence: bound profile-specific verification receipts. | Phase 8.4–5; observability and target-policy adapters. | Reject partial health as full success. Quarantine/recover through the operation graph, then re-observe after cleanup. | Partly designed; end-to-end proof has not run. |
| 15 | **Rollback and recovery:** can service rollback, forward repair, restore and cleanup be demonstrated safely? Evidence: executed recovery receipt, restoration invariant and declared post-recovery state. | Phase 1 lifecycle; Phase 6 lifecycle gates; Phase 8 controlled recovery proof. | Reject theoretical-only restore/rollback. Use an isolated rehearsal and fail closed if data, retention or cleanup policy would be violated. | Service rollback approach exists; relational restore is designed but not live-proven. |
| 16 | **Evidence retention:** is safe evidence durable, queryable, digest-bound and free of secrets/raw provider data? Evidence: verified receipt/journal storage, access policy, expiry/invalidation and redaction checks. | §4 records; Phase 4 journal; Phase 6 evidence upload; Phase 9 dashboard. | Reject terminal-only, unbound, untrusted, replayed, stale or sensitive evidence. Re-run the affected proof after secure evidence storage is available. | Partial: some evidence is transient terminal output. |
| 17 | **Continuous operation:** are SLOs, alerts, telemetry-loss detection, patching, cost controls, expiry and recovery rehearsals operating? Evidence: scheduled-control history over required windows and alert-delivery/rehearsal receipts. | Phase 9 continuous assurance; supply-chain admission drives patch/requalification. | Alert and open a recoverable operation for missed control, expired proof, unsupported dependency, budget breach or failed rehearsal. A one-time release proof cannot satisfy this row. | Observability baseline exists; long-window SLO and relational periodic rehearsal remain incomplete. |

The release state ledger records a row as `not-applicable` only when the
composition compiler produces an independently reviewable applicability result
with supporting discovery facts. “Not applicable” is never a free-text
override. The matrix is generated from the composition graph; humans review the
generated result and safe evidence rather than maintaining a second handwritten
checklist.

### Required cross-cutting control contracts

The following contracts are mandatory input to the matrix. They are not
optional architecture notes, and a release cannot use a generic “covered by
platform” claim in place of one.

| Contract | Mandatory content | Matrix gates it controls |
| --- | --- | --- |
| **Risk tier** | A machine-readable tier based on effects, data classification, privilege, reversibility, target exposure and cost. The tier selects the minimum non-waivable gate set, independent-review depth, qualification environment and recovery proof. A lower tier can add gates but cannot omit its mandatory gates. | 1, 2, 5, 9, 13–15, 17 |
| **Environment contract** | Account, region, target fingerprint, identities, network paths, certificates/domains, external dependencies, database/queue/storage bindings, quotas, capacity and cost ceilings. Each binding has an owner, source, expiry and safe inspection method. | 1, 3, 8, 10–12, 14 |
| **Configuration lifecycle** | Versioned schema, defaults and override precedence, compatibility range, secret reference shape, rotation, revocation, expiry, rollout and rollback rules. Validation occurs before any candidate starts. | 3, 4, 6, 11–13 |
| **Compatibility contract** | Backward/forward compatibility for API versions, queue envelopes, database schema, cache values, feature flags and rolling deployments. It states mixed-version duration, upgrade order, safe rollback point and incompatibility detection. | 2–6, 11–15 |
| **Data-migration safety** | Explicit `expand → migrate → backfill → validate → contract → retention/purge` phases; data invariants, resumability, idempotency, forward repair, backup/restore point and irreversible-change approval. | 1–6, 12–15 |
| **Capacity and resilience** | Load envelope, timeouts, rate limits, connection-pool limits, autoscaling/fixed-scale bounds, dependency degradation, service quotas, regional failure posture, budget ceiling and overload behavior. | 1, 5, 8, 10–14, 17 |
| **Failure-injection matrix** | Profile-appropriate controlled faults: dependency loss, rotated/expired secret, denied permission, network/TLS failure, task restart, queue redelivery, telemetry loss, rollback/recovery and cleanup failure. It declares safe fault mechanism, bounds, expected signal and restoration. | 4, 5, 11–17 |
| **Telemetry-health contract** | Expected logs/metrics/traces, collector/exporter dependency, signal freshness, cardinality bounds, redaction rule, missing-telemetry detector, alert route and false-green prevention. Missing telemetry is a failed control, never a successful SLO. | 3, 10–11, 14, 16–17 |
| **Break-glass diagnostic policy** | Restricted diagnostic categories, accountable operator, permitted secure location, time-bounded access, redaction, retention/destruction, audit receipt and escalation when safe categories cannot diagnose a failure. It never permits secrets/raw bodies into Git, terminal evidence or commit logs. | 1, 3, 12–16 |
| **Cleanup and expiry contract** | Every disposable task, restore instance, artifact, temporary role/client, synthetic resource and evidence lease has an owner, effect boundary, cleanup action, deadline, verification, cost check and escalation path. | 1, 5, 9, 13–17 |
| **Continuous reconciliation contract** | Scheduled checks for declared resources, IAM, network, certificate expiry, image vulnerability/patch state, budget, backup status, alarm delivery, telemetry health, restore readiness and evidence expiry. It defines cadence, owner, alert and recovery operation. | 10, 14, 16–17 |
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
4. Define an evidence compatibility matrix. For example, a healthy service
   cannot satisfy a finite-job proof; a fixture cannot satisfy a managed-RDS
   proof; provider acceptance cannot satisfy a semantic migration completion.
5. Define identity and policy bindings: every operation names the acting
   identity, exact provider actions/resources, justification, and an
   authority-expiry rule. A generic adapter may not invent permissions.
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
   Parse failures, symlinks, dynamic process launches and unsupported formats
   become unresolved findings.
3. Reconcile discovered observations against composition declarations. Reject
   undeclared executable units, bindings, sidecars, artifacts, identity edges,
   operational effects, callers or required proofs.
4. Implement mutation tests that introduce an unlisted command, hidden sidecar,
   missing secret binding and false `test-only` label. The coverage gate must
   fail each case.
5. Generate an adoption matrix mapping every existing `scripts/04.deploy/`
   capability, workflow and target operation to its replacement controller
   profile or deliberate retirement plan.
6. Add harness self-verification tests for every contract parser, matrix
   expansion, state transition, lock/fence rule, evidence redaction rule and
   provider-adapter response. Each test must include a counterexample which is
   rejected before a mutating operation can begin.

**Exit gate:** discovered inventory and declared graph reconcile with zero
unresolved supported paths; negative coverage tests pass; the adoption ledger
has no undocumented exclusions.

### Phase 3 — make build and artifact proof exact

1. Derive the build/dependency/export closure from workspace manifests and
   compiler emission instead of duplicated workspace maps or runtime fallback
   to TypeScript sources.
2. Build once into private output/dependency directories; pin/verify toolchain,
   lockfile, base artifact, target platform and produced digest.
3. For each executable profile, run the final artifact with its actual
   entrypoint/command, user, working directory, assets, environment shape and
   shutdown constraints. Test one-shot task definitions separately from server
   readiness.
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

Start with migration steps 1–2 as source-only work: preserve the PostgreSQL
handoff, complete the inventory/adoption ledger, ratify the durable-store and
bootstrap decisions, and publish the four-record, profile/evidence, risk-tier
and self-verification contracts. Do not make another PostgreSQL or AWS
deployment attempt until migration step 6 can enumerate and validate every
finite task involved in the proposed operation graph.
