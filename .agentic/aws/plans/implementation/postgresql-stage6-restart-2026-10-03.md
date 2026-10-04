<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.plan.postgresql-stage6-restart-2026-10-03
version: 3
status: draft
layer: 04.deploy
domain: persistence.operations
disciplines:
- architecture
- security
- sre
kind: implementation-plan
purpose: Prepare a bounded PostgreSQL Stage 6 completion proposal for review without authorizing implementation or AWS execution.
portability:
  class: source-only
  targets: []
used_by:
- id: aws.readme
  path: .agentic/aws/README.md
-->
# PostgreSQL Stage 6 restart proposal

## Decision requested and conflicting recovery evidence

This is review preparation under [Plan AWS Change](../../workflows/plan-aws-change.md).
It proposes completion of the existing PostgreSQL relational reference through
bootstrap, migration, one delivery, restore verification and cleanup. It grants
no implementation, publication, deployment, AWS mutation or task-execution authority.
The public HTTP service remains healthy throughout the proposed work; HTTP-only
delivery is not this plan's completion milestone.

The proposed execution approval covers continued diagnosis, relevant source or
configuration repair, affected verification, image qualification/publication and
bounded reattempts until the PostgreSQL completion criteria pass. An ordinary
failure pauses the affected operation and its dependants while that work proceeds
within the allowance below. It is not a session closeout or a request for renewed
permission for an already approved repair. The current request amends this review
package; adoption, prerequisite implementation and cloud execution remain pending.

**Recovery-4 must not be proposed as the next executable attempt.** The restored
[target profile](../../../../infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml)
records recovery-4 as not started, whereas the later
[reliability plan](local-to-proven-deployment-reliability.md#starting-state-postgresql-terminated-not-a-successful-prerequisite)
records a user-reported recovery-4 bootstrap failure before application telemetry.
Neither is fresh cloud evidence. Treat the initial and recovery-1 through
recovery-4 labels as consumed or unavailable until reconciled. Missing task-list
results cannot alone turn a historically consumed label into an unused one.

The local restored baseline is merge `2309e676`, with the reviewed source inverse
described in the [recovery report](../../../../docs/04.deploy/plans/controlled-recovery-report-2026-10-03.md).
No AWS inspection was performed for this proposal. Historical service health,
stored-template equality, backup coverage, permissions and drift classifications
must not be presented as current readiness. Reconciliation must establish the last
accepted operation, its artifact/revision, terminal outcome, cleanup and ownership.
Only then may a reviewed controller/profile amendment name a fresh fixed attempt.

## Scope and preserved work

The target remains `kanbien/staging`, account `337159794548`, region `eu-west-1`,
with the profile-selected administrator identity verified before any future use.
Preserve all branches, worktrees, dirty files, durable recovery evidence, managed
credential rotations, rolling backups and existing monitoring. Storage/data-governance,
tenant-authority and scheduler drafts are separate work; importing them is unnecessary.
The retired replacement programme and a general compiler/control framework are excluded.

| Boundary | Existing source and proposed limit |
| --- | --- |
| Infrastructure | Existing `kanbien-staging-platform-shell-foundation` and `kanbien-staging-platform-shell-service`; no new Foundation, IAM, network, listener, DNS or alarm resources. |
| Public runtime | Existing `kanbien-staging-platform-shell` service and DynamoDB-backed default command remain; steady server `1/1`, dormant worker `0/0`. |
| Database | Existing `kanbien-staging-platform-relational`; private, encrypted, deletion-protected PostgreSQL 17 reference, seven-day backups and verified TLS. No replacement or restore over it. |
| Workloads | Existing bootstrap, migration, relay, worker and restore-verification task definitions; non-public, no port mappings; reviewed dormant-worker network only. |
| Data | One existing fixed harmless smoke work item, its lineage/outbox/processing facts and isolated relational source/DLQ queues. No product data or direct queue clearing. |
| Restore | At most three sequential disposable private recovery instances under the proposed allowance, with at most one existing at a time. An uncertain or pre-existing identifier cannot be reused. |
| Source ownership | Existing target entrypoints, image/check wrappers, candidate and relational controllers, reconciler and target profile. No speculative replacement packages. |

The exact definitions and outputs are in
[service.yml](../../../../infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml).
The [Stage 6 source plan](../../../03.product/plans/implementation/postgresql-relational-persistence-reference-v1.md#stage-6--one-controlled-delivery-recovery-rehearsal-and-handoff)
and [threat model](../../../../docs/aws/kanbien-staging-postgresql-relational-reference-v1-threat-model.md)
retain their data, security and completion requirements.

## Minimum instruction proposal

The unapplied review patch is
[postgresql-instructions.patch](../../../../commitLogs/2026/oct/03/2026-10-03-14-13-platform-restart-preparation/proposals/postgresql-instructions.patch).
It should narrowly replace blanket whole-estate/compiler prerequisites for this
named slice with the operation-specific evidence below, retaining explicit target
approval and all substantive security, identity, recovery and cleanup requirements.
Its scope must cover conflicting standard/workflow applicability and PostgreSQL
Stage 6 routing; indirect programme entry points need a matching scoped pointer.
Until reviewed and applied, the current instructions remain in force.

The patch also makes the repair-cycle authority explicit and clarifies that
cleanup of positively owned disposable resources expressly included in an
execution approval needs no second approval. Other destructive actions remain
outside this allowance. Required checks pause remote progression while their
cause is repaired; they are never waived or relabelled as passing.

Correct stale recovery-1/recovery-2 runbook descriptions when the reconciled next
attempt is selected. Do not resolve the recovery-4 contradiction by merely changing
a status string, renaming a label or treating a diagnostic as retry authority.
The existing replacement proposal's HTTP-first milestones and illustrative budget
are not this PostgreSQL completion plan.

## Existing-route source prerequisites, for separate review

These are identified gaps, not implemented protection. Prepare the smallest patches
to the existing owners, with focused negative tests, before requesting execution.

| Gap | Minimum proposed correction and proof |
| --- | --- |
| Final image is not exercised | Extend the existing image-smoke wrapper to accept the reviewed existing immutable image without rebuilding. Exercise actual server/health commands and the five relational entrypoints from that digest; bind platform, source revision and packaged assets. |
| Adapter proof is narrower than task proof | Keep the disposable real-PostgreSQL semantic suite; add exact bootstrap credentials-only master shape, migration ownership/default grants, runtime DML/no-DDL and TLS/configuration proofs using synthetic inputs. Do not equate a superuser fixture with target-role proof. |
| Relational launches select latest family | Resolve the reviewed task-definition ARNs/revisions from stack outputs; check digest, command, roles, secret/configuration shape, network and container boundary, then launch those exact revisions. Verify returned task identity. |
| Accepted operations can be uncertain | In the existing candidate/relational controllers, retain bounded operation identity before submission and reconcile accepted-or-unknown outcomes before any repeat. Prove interrupted/lost-response paths without a second unintended launch; expired or unresolved identity blocks retry. |
| Timeout does not establish cleanup | Prove controlled terminal handling for relational task timeout/interruption and restore-response loss. An accepted or possibly accepted task/restore remains owned until termination/cleanup or explicit handoff is evidenced. |
| Restore point may omit smoke state | Establish that the selected recovery point covers the completed smoke transaction before restoring. Verify migration versions/checksums, expected synthetic state, terminal outbox and completed processing on the isolated restore. |
| Documentation overstates current readiness | Align controller/profile labels, runbook and evidence only with reconciled outcomes; keep planned, local, adapter and target proof separate. |
| Continuation cannot resume after a partial success | Extend the existing relational controller/profile to select the first incomplete stage from durable successful receipts. Revalidate completed stage effects under the current bindings; preserve consumed labels and the one logical smoke work item. Prove failure after each stage, process restart and no duplicate delivery. |
| Candidate identity requires an unnecessary image change | Extend the existing candidate policy/controller and relational candidate-predecessor check to distinguish immutable artifact from bounded attempt identity. Keep terminal attempts consumed, and permit a fresh reviewed attempt with the same qualified digest after reconciliation. |
| Proposed cumulative limits are not enforced | Use the existing controllers, preflights and session/evidence records to persist and check cumulative attempt/time/spend counters before submission. No counter reset by a new process, label, image or chat; local tests must prove exhaustion blocks new effects while approved cleanup remains possible. |

Evidence for these gaps: the [image wrapper](../../../../scripts/04.deploy/smoke-test-platform-shell-image/script.sh)
currently rebuilds; the [payload checker](../../../../scripts/04.deploy/build-platform-shell-image/verify-runtime-payload.mjs)
only checks a missing-CA bootstrap failure; the
[adapter integration](../../../../platform/adapters/aws/persistence/postgresql/tests/postgresql-persistence-adapter-integration.test.ts)
uses a superuser pool without TLS; the
[relational controller](../../../../scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py)
launches by family and owns restore cleanup after an acknowledged response; the
[restore entrypoint](../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-restore-verify.main.ts)
currently checks only work-item/outbox row counts.

## Operation, evidence and action sequence

Every future external action binds an exact reviewed source, image, target,
operation and coordinator within the approved allowance. A qualifying in-scope
repair may change that binding without a new execution approval; record its diff,
checks and replacement binding before use. A failed predecessor prevents dependent
execution while reconciliation and repair continue. This is a review sequence.

| Operation | Evidence required before action | Bounded action and acceptance |
| --- | --- | --- |
| Discover/reconcile | Historical sessions and durable backups, exact local source, protected identity, no competing operator. | Read current stacks/tasks/labels, configuration metadata, queues, database/restore state, alarms and budget. Resolve recovery-4 and unknown operations. Record only safe verdicts and operation references in their permitted storage. |
| Source qualification | Reviewed instruction amendments and narrow source patches; no pending ownership conflict. | Run focused controller/regression checks, adapter/product checks and disposable real-database tests. Demonstrate failure/duplicate/fence handling, least privilege, redaction and cleanup. |
| Artifact qualification | Exact source revision and build inputs, required scanner/attestation results. | Publish only through the existing workflow after approval; pull the immutable digest and execute the actual image/entrypoints. No host-only build or separately rebuilt smoke image substitutes for this proof. |
| Refresh target prerequisites | Current resource discovery and approved assessment scope. | Use existing Foundation/Service/artifact assessors only where needed; preserve classified parameter normalization and reject other drift. Fresh live-boundary proof confirms private/encrypted/TLS/network/operations posture. |
| Bind candidate | Reviewed candidate-only change set and fresh candidate-baseline Service evidence. | Modify only the existing candidate task definition to the qualified digest; preserve non-image properties. Use the amended existing candidate controller; require healthy then stopped and no lingering candidate. |
| Promote shared image | Candidate passed for exact digest/revision; fresh Foundation/Service evidence; recorded previous good template, parameters, images and revisions. | Existing bootstrap-recovery reconciler permits eight existing task-definition replacements plus two in-place service references, with zero additions/removals. Execute only that reviewed scope; verify health and all resulting identities. |
| Bootstrap | Fresh reconciled attempt identity, exact task revision/image, TLS/secret/role proof, empty queues, server `1/1`, worker `0/0`, healthy stacks/database. | Launch one task per attempt. Require a successful terminal receipt and unchanged aggregate boundary before continuation. A failure enters the repair cycle; dependent stages remain paused. |
| Resume continuation | Valid successful predecessor receipts and renewed immediate prerequisites; unused bounded identity for the first incomplete stage. | Migration applies the immutable manifest; relay accepts the one logical work item; worker records completion before acknowledgement. Reconcile existing effects before resuming; never restart the whole continuation merely because a later stage failed. Source/DLQ and due outbox finish empty. |
| Restore and clean | Smoke completion is covered by recovery point; isolated destination proven absent; bounded creation/deletion authority. | Restore privately, verify TLS and required schema/state/checksums/processing, then remove only the owned disposable instance without final snapshot. Verify absence, including after failure. |
| Close proof | All operation outcomes reconciled; cleanup complete; service/database/queue/alert/cost evidence current. | Update Stage 6 readiness and handoff with exact bounded claims, residual limits and owner; no product deployment or wider programme follows automatically. |

## Existing interfaces and unavailable future invocations

The current commands are evidence of available interfaces, not approval or a claim
that their execution paths are ready. No proposed new flag exists until implemented,
tested and reviewed. **All execution variants remain unavailable for this restart
until amendments and reconciliation select a safe new attempt.**

| Interface | Supported current mode and use in the later reviewed plan |
| --- | --- |
| `platform:shell:postgresql-relational-smoke` | `--validate`; later amended `--execute-bootstrap-recovery --approve-relational-bootstrap-recovery`, then `--execute-recovery-continuation --approve-relational-recovery-continuation`. Their current recovery-4 binding is not executable restart authority. |
| Same relational controller | `--diagnose-bootstrap-recovery --approve-relational-bootstrap-recovery-diagnostic` reads only its fixed consumed label; no diagnostic authorizes a replay. The generic full-route `--execute` is excluded from this restart sequence. |
| `platform:shell:candidate-execution-preflight` | `--validate`; guarded `--execute --approve-candidate-execution-preflight` only after source amendments, exact binding and execution approval. No caller-selected image, label, network or timeout. |
| `platform:shell:deployment-reconciliation` | `--validate`; existing `pre-candidate-execution-preflight-image-change-set` and `pre-relational-stage6-bootstrap-recovery-service-change-set` modes require `--service-change-set` and fresh `--service-drift-evidence`; relational rollout also requires `--known-foundation-drift-evidence`. |
| Active drift assessors | Existing Foundation/Service/artifact commands require their respective `--execute-approved-active-...-drift-assessment` guards and a new direct-child `/tmp` evidence file; candidate Service assessment additionally uses `--candidate-onboarding`. Approval must include these metadata-changing assessments. |
| `platform:shell:postgresql-live-boundary` | `--validate` is local; later `--json` inspection proves declared provider metadata/network/operations, not an actual authenticated database connection. |
| Local qualification | `platform:adapter:aws:persistence:postgresql:check`, `platform:adapter:aws:persistence:postgresql:integration`, `platform:server:image-runtime-check`, controller `:check` commands and relevant product/container checks. New final-image/role cases remain prerequisites. |

Use the [reconciler](../../../../scripts/04.deploy/reconcile-platform-shell-staging/script.py)
and [candidate controller](../../../../scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py)
as argument authorities. CloudFormation creation/execution remains separately
governed by [Execute Approved AWS Change](../../workflows/execute-approved-aws-change.md).

## Diagnosis, repair, verification and resume

After execution approval, continue this cycle autonomously while its scope and
cumulative limits hold. Keep PostgreSQL completion as the goal; scheduler,
storage and tenant-authority work remains deferred.

1. Pause the failed operation and its dependants. Record its safe verdict,
   stage, source/image bindings and evidence reference. Establish whether the
   operation was rejected, accepted, terminal or still unknown. A failed process
   exit is not evidence that no remote effect occurred.
2. Reconcile the owned task, stack update, queue/data effect or restore before
   another submission. Complete required cleanup or establish a safe retained
   checkpoint with ownership. Keep a successfully committed migration, outbox
   or processing fact; cleanup never means undoing valid state or clearing queues.
3. Diagnose the cause and why earlier checks missed it. Use existing safe
   classifiers, preflights and local fixtures; choose a bounded distinguishing
   check for an unconfirmed cause. Unknown acceptance, unsafe evidence or a cause
   without a safe disposition blocks reattempt, while bounded investigation continues.
4. Repair only the relevant existing source, configuration or instructions
   within the declared owners/effects. Preserve failure lineage. Use the existing
   commit/review gates and checkpoint meaningful repairs; normal in-scope source
   review and verification do not require another human execution approval.
5. Rerun affected checks and add the smallest effective prevention measure to
   an existing test, preflight or instruction. Demonstrate the original fault is
   detected or safely handled and that the corrected case passes. Instructions
   alone are insufficient when executable enforcement owns the failed assumption.
6. If packaged runtime or build inputs changed, qualify and publish a new
   immutable image within its allowance; repeat actual-image, candidate and
   affected target proofs. A controller-only repair does not require a new image
   when relevant artifact/configuration evidence remains valid. Refresh all
   bindings affected by the repair; unrelated successful evidence may be reused.
7. Renew immediate preconditions and budget checks; resume the first incomplete
   operation with a fresh supported attempt identity and verified predecessors.
   Observe the result, update its failure/prevention record, and repeat as needed
   until acceptance passes or a precise escalation condition is reached.

An uncertain submission is reconciled as the same operation, not relabelled as
a new attempt. For ECS, persist the exact request and client token before launch.
Any supported same-request recovery must remain within the provider token window;
expired identity plus unknown outcome requires reconciliation, not a blind launch.
AWS documents that token validity is the lesser of 24 hours and task lifetime plus
one hour; see [ECS idempotency](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ECS_Idempotency.html).
Durable local receipts therefore cannot depend on indefinite ECS task-list retention.

After a partial continuation, reassess the actual database/queue state. A successful
migration is not re-applied blindly; an accepted relay is not repeated to create
another message; a failed worker is reconciled against processing/acknowledgement
state. Reattempt only behavior proved safe for that state. If the existing entrypoint
cannot do this within the same logical work item and effect boundary, repair and
test it first or escalate. A stale predecessor under changed semantics is requalified,
not silently reused. No general controller or replacement programme is introduced.

## Proposed cumulative allowance, escalation and recovery

These are proposed ceilings for one approved PostgreSQL completion effort,
not current authority or a promise to consume the whole allowance. They include
initial prerequisite work, ordinary repair and reattempts. Use all applicable
counters together; the first exhausted limit governs. A new session, process,
source revision, image or operation label never resets them.

| Limit | Proposed allowance and counting rule |
| --- | --- |
| Source/configuration work | Two prerequisite qualification batches plus six material-failure repair cycles, eight reviewed batches total, in existing owners listed above. A cycle includes diagnosis, the relevant repair, affected tests and proportionate prevention; editing iterations are covered by its time budget. |
| Image publication | Four immutable publications total: initial qualified image plus up to three changed-image repairs. Each needs existing scanner/attestation and actual-image proof. Do not publish a new image solely for an attempt label. |
| Candidate / candidate binding | Six candidate launch attempts and six candidate-only binding updates total, including failed or possibly accepted submissions. Same-digest reattempts need the amended controller and safe reconciliation. |
| Shared image promotion / rollback | Four guarded promotions total, each limited to the existing eight task definitions and two service references; at most one reviewed rollback per promotion, four total, preserving the same resource/configuration boundary. |
| Relational stages | Four launch attempts per stage (bootstrap, migration, relay, worker, restore verification), twenty total. Count rejected/accepted/unknown submissions conservatively before submission; no consumed identity is reused. Resume skips valid completed stages. |
| Restore resources | Three creations total, sequential, one owned disposable instance at a time; at most four hours owned lifetime each including cleanup. Each creation includes deletion and verified absence. A possibly accepted create consumes an allowance until reconciled. |
| Active work / elapsed time | Twenty-four active hours total: up to eight for the two prerequisite source batches under separate source-work approval, and sixteen for execution/repair after execution approval, across sessions. Execution also has a 48-consecutive-hour elapsed limit from its approval. Reserve the last four execution active hours and last four elapsed hours for reconciliation/cleanup; normal work stops before it would invade either reserve. |
| Per-failure diagnosis | Up to two active hours to establish a tested cause and safe disposition, within the applicable phase/total allowance. An unresolved failure at that limit is escalated with its evidence and remaining ownership. |
| Incremental spend | USD 100 maximum above the existing target baseline: USD 75 for normal qualification, publication, tasks, rollout and restore; USD 25 reserved for approved reconciliation/cleanup/rollback. Include billable build/CI, registry/log/storage, task overlap and restore costs; do not count free-tier/credits as authority to exceed this ceiling. |
| Concurrency / replay | One coordinator and one active stage/candidate/restore operation; public service overlap only as reviewed in its existing deployment policy. No concurrent repair launches or replay of consumed labels. |

Before each external action, record used/remaining counters and an upper-bound
cost/time estimate for that action plus its cleanup. Do not launch if the estimate
does not fit the normal allowance and remaining reserve. Include accepted and
possibly accepted work, failed builds/publications and delayed billing in the
conservative ledger. The total ceiling includes reserve; it is not USD 100 plus
another USD 25. Existing ongoing database/service costs remain in the baseline,
but repair-induced extra hours/resources/storage/overlap count as incremental.
The execution approval records already consumed prerequisite batches/time/spend;
they are not reset or charged again. The pre-approval source allowance grants no
cloud action and is available only when that source work is explicitly authorized.

Validate the proposed ceiling against current eu-west-1 sizes, storage and rates
before approval. [RDS pricing](https://aws.amazon.com/rds/postgresql/pricing/)
includes instance/storage charges; [Fargate pricing](https://aws.amazon.com/fargate/pricing/)
depends on actual allocated resources and duration. This is an allowance, not a
fresh target estimate. A tag budget alert or delayed bill is not enforcement:
existing controller/preflight amendments must block submissions using the ledger
and conservative estimates. If costs cannot be bounded, approval readiness fails.

Retain existing per-task wait `900s`, restore availability/deletion `1800s` each,
queue-settlement `90s`, and candidate start/stop `300s/120s` unless separately
reviewed. A timeout is a failed observation, not proof that remote work stopped.
Keep the candidate stopped before promotion; preserve steady server one/worker zero.
Record any permitted temporary service overlap from the exact reviewed ECS policy.

The existing `900s` task wait must gain an owned-stop/terminal-verification path;
the current exception alone is insufficient. Reserve up to `120s` for task stop
verification within the recovery allowance and prove the existing identity can
perform it. RDS availability/deletion waits remain `1800s` each; each timeout
returns to reconciliation while ownership and lifetime accounting continue.

Ordinary loader, configuration, test, image, task or restore failures enter the
repair cycle. Unexpected drift, identity/digest mismatch, non-empty terminal
queue or missing restore proof pauses affected work for bounded diagnosis; it
does not itself end authorized in-scope repair. Escalate when safe reconciliation
or necessary cleanup cannot be completed within the allowance, a tested repair
requires new effects/resources, broader permissions, altered security posture,
persistent schema/data repair outside the immutable manifest, or any exhausted
attempt/time/cost limit. Escalate a third live occurrence of the same cause after
two purportedly verified corrections; preserve all occurrences and revisit the
failed prevention premise. Unknown outcome or unsafe evidence never permits
onward execution. A transient cause may be reattempted only after classification,
backoff within the same deadlines and fresh immediate preconditions.
Never fix freshness by editing timestamps or clear a queue to make a check pass.

At a normal-work limit, use only the reserved, already approved recovery actions
to reconcile, stop owned tasks, perform the reviewed rollback and remove owned
disposable restores. The reserve authorizes no new proof attempt or image. If
the recovery reserve is exhausted or cleanup still cannot be completed safely,
escalate immediately with exact remaining ownership; do not silently abandon it.

Capture previous good stack template/parameters, both image parameters and exact
task revisions before mutation. Observe native stack/service rollback to terminal
state before another action. A reviewed service rollback must preserve existing
configuration and reconcile all affected task definitions; direct emergency service
updates require explicit scope and later stack reconciliation. Host-rule deletion
is excluded. Migration failures require reviewed forward repair, not schema undo.

Delete only the positively owned disposable restore instance. If acceptance or
cleanup is uncertain, reconcile first and preserve responsibility for any remaining
resource. No deletion of the source database, backup, unrelated instance, branch
or preserved work is allowed. Preserve managed credentials and rotation history.

## Evidence required before requesting execution approval

The amended documents alone do not establish controller support. Do not request
execution approval until the effective-instruction and controller evidence below
is complete. Source-only prerequisite implementation needs its own authorized
scope; the present revision only proposes that work and its proof requirements.

| Requirement | Current local finding | Required approval evidence using existing owners |
| --- | --- | --- |
| Effective repair authority | The patch is unapplied; canonical realization/Stage 6 instructions still require the broad route. The AWS workflow also requires renewed approval for destructive actions without distinguishing pre-approved owned cleanup. | Adopt the scoped patch through normal review, regenerate/check affected recognition sources and inspect every relevant entry point. Record adopted source hashes and the exact execution allowance, including owned restore deletion/rollback. No remaining instruction may convert an ordinary in-scope failure into mandatory closeout or blanket reapproval. |
| Safe bounded attempt identity | `load_policy` hardcodes recovery-4 and lifecycle strings; `no_prior_label` uses current ECS listings. Candidate `attempt_label` is digest-derived and terminal digests cannot be replayed. | Reviewed finite identities selected from committed policy, durable consumed/unknown receipts, same-digest candidate reattempt and compatible relational predecessor lookup. Tests must reject consumed/expired/unknown identities and prove counters survive restart. |
| Resume from the correct checkpoint | `execute_recovery_continuation` always starts migration, relay, worker and restore after bootstrap. A late failure encounters a consumed earlier label on reinvocation. | Stage-aware resume and predecessor/effect validation in that controller. Inject a failure after every stage, resume from the first incomplete stage and prove successful stages and the logical delivery are not duplicated. |
| Unknown acceptance / timeout / cleanup | Candidate cleanup owns an acknowledged task in memory; relational timeout only raises. Restore ownership is set after a response, leaving lost-response acceptance unresolved. | Local injected lost-response/interruption/restart and timeout cases must reconcile exactly one effect and prove terminal cleanup or a precise owned blocker. Include restore absence, token expiry and exhausted normal budget with cleanup reserve. |
| Changed artifact/configuration | Current image-smoke rebuilds; exact relational task-revision/role/TLS and restored-state gaps are listed above. | Actual qualified digest, exact current task bindings, real role/TLS/semantic proof and stronger restore checks. Demonstrate that a changed image re-enters qualification/candidate/promotion and that unrelated valid evidence is retained. |
| Safe diagnostics and cumulative bounds | Bootstrap has allowlisted classification; other relational errors collapse to a generic failed verdict. Existing checks do not demonstrate a multi-stage repair loop or cumulative spend/time/attempt enforcement. | Extend existing safe classifiers/checks without raw payload retention. Behavioral tests prove distinct failure dispositions, budget exhaustion, cleanup ownership and repaired resume. Record exact command, source revision and result. |
| Approval feasibility | No current target/resource/pricing reconciliation has been performed. | Resolve recovery-4, competing operations, identity, existing permissions, drift and target health; price the proposed ceiling and cleanup reserve. Existing source guards/checks must pass. Any unresolved requirement means approval is not yet requested. |

The existing checks are
`platform:shell:postgresql-relational-smoke:check`,
`platform:shell:candidate-execution-preflight:check` and
`platform:shell:deployment-reconciliation:check`, plus their local `--validate`
modes and affected adapter/image/product checks. Current guard/shape test passes
are useful baseline evidence; they do not prove missing resume or recovery behavior.
Extend their current test files with focused behavioral cases rather than building
a separate test/preflight/controller framework. No required failing gate is bypassed.

## Prerequisite implementation checkpoint — 2026-10-03

The scoped applicability amendment is now adopted. It permits the following
source preparation and local verification immediately; it does **not** grant
image publication, AWS mutation, deployment, or relational task execution.
Those remain subject to the final concrete execution approval.

The existing relational controller now uses a source-owned atomic receipt ledger
with finite recovery-5 stage labels. It records submission, accepted, succeeded,
failed, unknown, and timeout-cleanup-pending states without task identifiers or
provider payloads. Its local behavioral proof covers late-stage resume without
restarting a completed migration, timeout cleanup ownership, an uncertain
submission blocking retry, and receipt/attempt/cost limits persisting after a
process restart. The candidate controller now assigns up to four durable,
same-image candidate identities rather than requiring an image change after a
terminal attempt.

The restore entrypoint now proves both immutable migration IDs/checksums, the
fixed work item, a published terminal outbox row, and a completed processing
record. The disposable real-engine suite proves the migration/runtime role
boundary: the runtime role can use required DML and cannot create schema
objects. Configuration still requires injected CA material and verify-full TLS.
The image smoke wrapper can qualify a supplied immutable digest without a
rebuild and invokes every relational entrypoint through its safe isolated
failure path; the compiled payload check also loads the restore verifier.

Local verification passed: relational smoke controller, candidate preflight,
deployment reconciliation, PostgreSQL adapter check, disposable real-engine
integration, compiled image payload, and infrastructure/reference static
checks. The direct Docker image smoke safely skipped because a Docker daemon
was unavailable; the independent disposable integration engine completed and
cleaned up normally.

Read-only target reconciliation was attempted through the PostgreSQL live
boundary verifier. Its source-policy check passed, but the current
`kanbien-dev` AWS identity was unavailable, so no current account or target
facts were obtained. This is an execution-approval prerequisite, not a reason
to claim target readiness. Recovery-4 remains unreconciled and unavailable;
the reviewed recovery-5 route cannot be selected for live use until a fresh
read-only reconciliation establishes operation ownership, current resource
health, identity, drift and cost facts.

The proposed execution allowance remains: up to four attempts per relational
stage, 16 active hours and 48 elapsed hours, USD100 total with USD25 reserved
for cleanup/reconciliation/rollback, and at most three sequential disposable
restores. The source ledger enforces its finite attempts, elapsed window and
conservative cost reserve before a new task; final approval must bind the
remaining active-time, restore and price facts to the reconciled target.

## Material failure and prevention records

Use the existing [Stage 6 evidence record](../../../../docs/aws/kanbien-staging-postgresql-relational-reference-v1-stage6-evidence.md)
for safe acceptance/failure summaries and this chat's
[session record](../../../../commitLogs/2026/oct/03/2026-10-03-14-13-platform-restart-preparation/README.md)
for diagnosis, source corrections, checks and cumulative counters. Link the same
failure reference in both; preserve prior entries and append outcome updates.
Do not create a replacement incident system or hide failures behind new labels.

For every material failure, including a meaningful local qualification failure,
record the following before reattempt and complete its outcome at closeout:

| Field | Required safe content |
| --- | --- |
| Failure and supporting evidence | Operation/stage, UTC observation, safe category, source/image bindings, accepted/rejected/unknown disposition, aggregate effect/cleanup verdict and permitted evidence reference. |
| Cause and earlier-check gap | Established cause with distinguishing evidence; identify the test/preflight assumption or coverage that missed it. Mark unknowns explicitly and never turn a category into an invented root cause. |
| Correction and verification | Relevant diff/commit or configuration-shape revision, affected check commands/results, artifact qualification and renewed target bindings where required. |
| Proportionate prevention and proof | Existing regression/preflight/instruction amended; evidence it catches or safely handles the original failure and accepts the corrected behavior. State any fidelity limit and the live proof still needed. |
| Resumed outcome or remaining blocker | First incomplete checkpoint, fresh attempt reference, consumed/remaining budgets, acceptance/cleanup result; otherwise exact unresolved condition, owner and next safe action or requested scope expansion. |

A first occurrence, repeated same-cause failure, uncertain outcome, escaped check
or cleanup failure is material. Routine editing/test iterations for the same
record can be appended without creating separate incidents. Recoverable failures
remain recorded when the final route succeeds. Historical recovery-4 starts as
an unresolved reported failure; its cause/correction/prevention remain unproven
until reconciliation and relevant verification supply evidence.

## Completion and handoff

Completion requires the final image and exact task revisions to pass source,
adapter and target proofs; successful bootstrap/migration; one accepted/processed
delivery with empty terminal queues/outbox; appropriate duplicate/retry/fence
proof; restore coverage plus schema/checksum/state verification; completed cleanup;
healthy public service, dormant worker and protected database; operational alarms,
notification evidence, reconciled cost, rollback evidence and an owned runbook.

At closeout provide both the PostgreSQL acceptance evidence and every completed
material-failure/prevention record, with original failures, corrections, prevention
proof and resumed outcomes preserved. Include cumulative allowance consumption,
remaining resources/ownership and fidelity limits. If acceptance has not passed,
state the precise blocker and outstanding records instead of claiming completion;
ordinary in-scope repair continues until acceptance or the escalation boundary.

Record only safe stage/aggregate facts, source/image identity and approved evidence
references in the [Stage 6 evidence record](../../../../docs/aws/kanbien-staging-postgresql-relational-reference-v1-stage6-evidence.md)
and [session](../../../../commitLogs/2026/oct/03/2026-10-03-14-13-platform-restart-preparation/README.md).
Never retain credentials, endpoints, SQL, row/message contents, raw task logs or
provider responses there. Distinguish local fixture, actual-image, adapter and live
target outcomes. Single-AZ, RLS, product authorization, HA/RPO/RTO and broader
persistence adoption remain explicitly outside this bounded completion claim.
