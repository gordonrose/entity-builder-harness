<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.kanbien-staging-platform-foundation-convergence-v1
version: 2
status: draft
layer: 04.deploy
domain: platform-foundation
disciplines:
- architecture
- security
- sre
kind: implementation-plan
purpose: Converge the data-governance, PostgreSQL, scheduler/time, storage, and observability prerequisites into one staged Kanbien/staging delivery programme with source, identity, change-set, execution, recovery, and evidence gates.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.plan.kanbien-staging-aws-change-reliability-programme
  path: docs/04.deploy/plans/kanbien-staging-aws-change-reliability-programme.md
- id: product.plan.data-governance-foundation-v1
  path: .agentic/03.product/plans/implementation/data-governance-foundation-v1.md
- id: product.plan.postgresql-relational-persistence-reference-v1
  path: .agentic/03.product/plans/implementation/postgresql-relational-persistence-reference-v1.md
- id: product.plan.storage-platform-v1
  path: .agentic/03.product/plans/implementation/storage-platform-v1.md
-->
# Kanbien/Staging Platform Foundation Convergence v1

## Restart preparation — 3 October 2026

Local source reconciliation uses recovery merge `2309e676`, now checked out on
the restart session branch and local `main`. The source positions below replace
the earlier pre-integration snapshot; they are not fresh remote or AWS evidence.
The [restart session record](../../../commitLogs/2026/oct/03/2026-10-03-14-13-platform-restart-preparation/README.md)
records preserved work, the scheduler/date-time investigation, and review limits.

This change prepares source review only. The programme phases and delivery trains
below remain proposals requiring separately bounded scope and approval. Existing
gates remain in force; the [replacement proposal](controlled-recovery-replacement-proposal-2026-10-03.md)
remains unimplemented. Deployment remains paused.
Where source is already preserved, review and reuse that work before proposing
implementation of the corresponding phase below.

## Objective

Deliver one reliable programme—not a sequence of improvised AWS repairs—that
converges the next platform foundations into a reviewable source state and then
executes their selected `kanbien/staging` target work in dependency order.

The programme coordinates:

```text
data-governance policy plane
        │
        ├── persistence / PostgreSQL reference
        ├── storage / future S3 reference
        └── observability policy consumption

scheduler and time foundation ──→ existing queue/worker path

operational-realization gate ──→ every provider mutation and live proof
```

“One go” means one approved, resumable programme with automatic gates and
durable safe checkpoints. It does **not** mean one unreviewed giant change set,
one role with every permission, or continuing after a failed prerequisite.

## Scope

### Included

1. Review the preserved provider-neutral operational-realization gate source.
2. Implement and prove the source stages of Data Governance Foundation v1.
3. Integrate data-governance consumer seams into persistence, storage, and
   observability without turning any consumer into a policy store.
4. Finish the bounded PostgreSQL relational-reference delivery/recovery proof
   through the realization gate.
5. Locate and preserve the scheduler/time draft before proposing its source
   review or integration; a later target plan would select its staging trigger.
6. Implement the provider-neutral storage source, AWS S3 adapter source, and a
   harmless service-controlled S3 reference only after its prerequisites pass.
7. Add the required target observability, cost, rollback, and evidence path for
   each new capability.

### Excluded from this programme

- customer, tenant, medical, document, voice, prompt, or other real business
  data;
- public browser uploads, resumable multipart transfer, bulk transfer, archive
  restore, OCR, AI, media streaming, or a scanner/DLP provider until each has a
  separately selected profile and change plan;
- a claim that a one-time harmless reference proof is continuous production
  operation or a universal persistence/storage choice;
- DNS, legacy-site, default ALB-routing, broad Cognito, or non-staging change;
- unrestricted retries, arbitrary shell/SQL/queue tools, destructive cleanup,
  or source/live IAM broadening as a recovery shortcut.

## Current Starting Position

The following are local source observations at restart preparation, not proof
that a target remains unchanged. Preserved branches and dirty files remain in
the original repository; they have not been imported into the restart clone.

| Area | Known source position | Required treatment |
| --- | --- | --- |
| Operational-realization gate | Gate source is present in the restored baseline. The old `99dc7470` candidate is not a pending integration requirement. | Review the current source and remaining proof gaps before proposing any change; do not promote the old candidate blindly. |
| Data governance / storage | Plans are on the restored baseline. Original branch `agent/data-governance-storage-foundation` preserves one unintegrated commit, `542ca170`, affecting 77 paths. | Review the preserved combined source slice and consumer dependencies before selecting an integration scope. S3 adapter and target work remain deferred. |
| PostgreSQL | Recovery commit `d8270e34` is already in the restored baseline. Stage 6 / recovery-4 remains unfinished in recorded evidence. | Credit existing source; do not replay earlier labels or start a new attempt without current facts, required gates and separate approval. |
| Scheduler/time | The 27 September review recorded 78 uncommitted paths. The original branch remains at base `8052929c`; its worktree is absent. Substantial plan/patch evidence survives in the original transcript, but the final source has not been reconstructed or verified. | Preserve the evidence and establish a verified draft through separately governed recovery before review/rebase. Do not infer source from the branch name or reconstruct it under restart preparation. |
| Tenant execution authority | Original branch `agent/tenant-access-control-operationalization` preserves one unintegrated commit, `e8810937`, affecting 38 paths. | Review opt-in worker/contracts changes and collisions separately; provider/target proof remains deferred. |
| Feature/platform consumption | The original root retains 13 uncommitted planning/governance files matching the recovery archive. | Preserve originals and review the complete draft before any integration; it introduces governing requirements. |
| Observability | Provider-neutral profiles and parts of the staging evidence path exist. | Every new stage must declare safe signals, alert owner, delivery path, retention/access boundary, and truthful SLO-confidence state. |

## The Programme Gates

Each gate has a machine-readable result, safe evidence record, and an explicit
next-state. A gate failure stops the programme at that state. It does not cause
a broad retry, permission expansion, source patch, or destructive cleanup.

| Gate | Question | Required evidence | Automatic stop conditions |
| --- | --- | --- | --- |
| G0: scope and governance | Is the requested work fully governed and within this programme? | Target, region, cost ceiling, no-go resources, rollback owner, approved operation classes. | Missing workflow, unbounded side effect, destructive path, unclear authority. |
| G1: source convergence | Is the exact source revision internally consistent? | Reviewed candidate diff, fresh-main integration, package boundaries, type/runtime/compatibility/negative checks, no unrelated dirty work. | Stale branch ancestry, API drift, unreviewed dependency, provider leak, failed test. |
| G2: realization compilation | Are all execution assumptions explicit and proven for the operating identity? | Valid operational-realization contract, normalized current facts, operation-to-permission contract, artifact identity, dependency graph. | Unknown/stale fact, mismatched identity, unscoped permission, unbounded retry, unsafe evidence field. |
| G3: change-set review | Does the proposed target delta exactly match the reviewed contract? | Per-stack change set, IAM/resource/cost diff, rollback and recovery action, target profile match. | Unexpected replacement/deletion, added public path, broader role, unpriced recurring cost, resource outside scope. |
| G4: ordered execution | Did each dependency converge before its consumer runs? | CloudFormation/service convergence, sealed artifact check, health/readiness, dormant-worker/empty-queue prerequisites. | Unhealthy rollout, non-empty final queue, unrecognised resource, failed migration/recovery, cost or security drift. |
| G5: bounded operational proof | Does the exact harmless flow prove allow, deny, failure, recovery, and safe evidence behaviour? | Aggregate-only proof result, alert/notification result where selected, reconciliation result, rollback/cleanup state. | Sensitive output, false-green telemetry, failed negative control, residual synthetic work, failed restore. |
| G6: closeout | Is the system safely returned to its planned steady state and is evidence complete? | Readiness/evidence record, source/image/contract versions, limits, cost posture, next review. | Missing evidence, temporary scale/task left active, uncertain resource state, uncommitted source/evidence. |

## Source Delivery Phases

### Phase A — establish the execution guardrail

1. Review gate source already present in the restored baseline, including source
   boundaries, fixtures, failure behaviour, package commands and PostgreSQL-plan
   references; distinguish implemented source from remaining operational proof.
2. Propose only any demonstrated remaining source delta against the reviewed
   baseline; the historical `99dc7470` candidate is not an instruction to merge.
3. Run its focused tests and the existing deployment-reconciliation checks.
4. Add a programme-level realization contract template that can name all
   source-to-target edges for this convergence programme.

**Pass:** G1 and G2 pass for a source-only fixture. No AWS state changes.

### Phase B — implement data governance before consumer duplication

1. Complete Data Governance Foundation v1 Stages 0–2: compatibility inventory,
   Core provider-neutral vocabulary, and fail-closed platform resolver.
2. Add a concise architecture rule and package/source READMEs as part of the
   same slice.
3. Add deterministic type/runtime/boundary/negative tests, including attempted
   tenant-policy weakening and unsafe telemetry handling.
4. Do not add a tenant-policy database, provider setting, or global raw-data
   interceptor.

**Pass:** G1 passes. The resolved-policy seam is source-proven but has no cloud
resource or real policy values.

### Phase C — make consumers consistently apply the result

1. Add narrow consumer seams to `platform/persistence`,
   `platform/observability`, and the future `platform/storage`; preserve their
   current provider-neutral boundaries.
2. Update Core/Platform contracts only where a stable cross-consumer noun is
   justified; preserve public compatibility or include a reviewed migration.
3. Prove one in-memory fixture receives the same resolved policy at the record,
   transfer, and telemetry boundaries.
4. Extend the feature-consumption decision record validator to require data
   purpose, profile, classification, residency, lifecycle, evidence, and
   processing declarations where a capability handles governed data.

**Pass:** G1 passes. No consumer can silently replace a resolved policy with a
local permissive default.

### Phase D — complete source candidates without blind merges

1. Reconcile the PostgreSQL source against fresh `main`; retain only the
   reviewed recovery categorisation and no-residual-task safeguards.
2. First locate and preserve the exact scheduler/time draft. Only a separately
   scoped source review may then rebase/test it against the selected baseline.
   Preserve the recorded no-automatic-missed-run limit until durable terminal
   state exists; an unavailable draft is not permission to reconstruct it.
3. Implement Storage Platform v1 source Stages 1–4: split Core files
   compatibly, create `platform/storage`, add S3 adapter source with recording
   client tests, and do not provision a bucket.
4. Extend observability profiles and target contract catalogues only with
   finite, low-cardinality, data-governance-compliant facts.

**Pass:** all affected source packages, adapters, smoke app, workflow, rule,
and full-repository checks pass at one immutable main revision.

## Single Staging Delivery Train

The delivery train is one orchestration run, but uses multiple ordered,
individually reviewed change sets. This limits blast radius while allowing the
programme to continue automatically when every preceding checkpoint passes.

```text
fresh target reconciliation
  → G2 compiled contract
  → PostgreSQL recovery/proof change set and bounded proof
  → scheduler trigger change set and bounded proof
  → S3 reference change set and bounded proof
  → consolidated reconciliation, cost, evidence, and closeout
```

### Train 1 — PostgreSQL reference completion

Use the realization gate to inspect the exact Foundation/Service state,
immutable image, task definition, task role, database boundary, queue state,
alarm state, and recovery destination. The programme may run one fresh,
labelled controlled route only when its source/image/current-fact graph passes.

The proof sequence is: source artifact → healthy service deployment → bounded
bootstrap/migration only if not already complete → one harmless persistence
acceptance → one relay → one self-terminating worker → aggregate terminal
state → isolated restore rehearsal → return worker scale to zero.

**Checkpoint:** no raw task/provider/database response, record, queue message,
credential, SQL, or content is retained. A failed check consumes its label and
requires a new source/current-fact review; it is never replayed as a retry.

### Train 2 — scheduler/time reference

Select a narrowly scoped trigger that creates one standard job through the
existing queue/worker route. The target plan must specify timezone source,
schedule identity, missed-run rule, idempotency key, queue policy, execution
deadline, EventBridge-or-equivalent adapter configuration, IAM, cost, alert,
and cancellation/rollback.

The proof uses one harmless fixed schedule/job, proves correct target
translation and worker completion, then removes/disables the temporary trigger
or returns it to its declared dormant state.

**Checkpoint:** no business schedule, customer timezone, recurring production
job, or continuous dispatcher is inferred from this reference proof.

### Train 3 — S3 storage reference

This train starts only after Data Governance Stages 1–3, a selected
metadata-persistence seam, and the storage source/adapter checks pass. Its
first profile is service-controlled and harmless; it does not accept browser or
customer uploads.

The target plan must select bucket topology, private/public-access controls,
TLS, encryption, region/residency, version/lifecycle posture, identities,
delivery boundary, cost ceiling, recovery path, alerts, and the exact
validation/scanner posture. If a required scanner/DLP selection is absent, the
train may prove only a harmless storage mechanism and must not claim real
document readiness.

The bounded proof is: authorised intent → opaque harmless quarantine write →
selected verification state → approval/promotion → short-lived authorised
delivery check → expired/unauthorised denial → selected logical-delete/restore
check → aggregate reconciliation and steady-state cleanup.

**Checkpoint:** no object key, filename, body, signed URL, scanner output, or
raw provider result is printed, logged, committed, or retained as evidence.

## One-Run Orchestrator Requirements

The eventual GitHub/deployment orchestration must:

1. accept only a reviewed immutable source revision, target, and named
   programme stage—never arbitrary shell, SQL, queue, bucket, or task input;
2. run G0–G3 before its first mutation and write safe gate results after every
   action;
3. use a distinct least-privilege identity per capability/operation class;
4. make target dependencies explicit rather than assuming a successful prior
   workflow or administrator session;
5. stop automatically on a failed/unknown gate without retrying a consumed
   proof label or broadening IAM;
6. preserve safe checkpoints so a later approved run starts from a fresh
   reconciliation rather than chat memory;
7. run final readiness, cost, alarm, queue/worker, and evidence checks before
   marking the programme complete; and
8. leave no temporary worker scale, schedule, disposable test task, object,
   or recovery destination outside its declared steady state.

## Cost And Security Boundaries

- PostgreSQL remains under its separately approved new-recurring-cost ceiling;
  each later train adds an explicit incremental and total monthly estimate
  before change-set execution.
- No train may use a wildcard administration role, public database/bucket,
  arbitrary task command, persistent secret output, DNS change, or legacy
  resource.
- Provider-neutral contracts contain no provider imports; adapters do not
  provision resources; infrastructure does not own product/business meaning.
- A target may choose EU-only placement, but each copy and processor—backup,
  archive, log/audit sink, preview, extraction, scanner, support, or AI—must be
  represented in its resolved handling policy and target mapping.

## Completion Definition

The programme can say it has completed only when all applicable source and live
gates pass, each train returns to its declared steady state, and the evidence
states both what was proved and what remains intentionally unbuilt.

At that point, the platform will have a governed source and staging reference
for data governance, relational persistence, scheduler/time, and harmless
object storage. It will **not** yet be entitled to claim feature-ready
personal/medical document handling until scanner/DLP, real upload, retention,
sharing, recovery, and support decisions for the selected feature profile pass
their own programme.

## Related Plans

- [AWS Change Reliability Programme](kanbien-staging-aws-change-reliability-programme.md)
  — reusable source/live/IAM reconciliation discipline.
- [Data Governance Foundation v1](../../../.agentic/03.product/plans/implementation/data-governance-foundation-v1.md)
  — shared policy-plane source work.
- [PostgreSQL Relational Persistence Reference v1](../../../.agentic/03.product/plans/implementation/postgresql-relational-persistence-reference-v1.md)
  — relational adapter and controlled proof.
- [Storage Platform v1](../../../.agentic/03.product/plans/implementation/storage-platform-v1.md)
  — storage lifecycle and S3-reference route.
- [Platform Runtime Implementation Plan](../../../.agentic/03.product/plans/implementation/platform-runtime-implementation.md)
  — platform composition and observability consumer boundary.
- [AWS Change Planning Workflow](../../../.agentic/aws/workflows/plan-aws-change.md)
  and [approved AWS execution workflow](../../../.agentic/aws/workflows/execute-approved-aws-change.md).
