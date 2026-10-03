<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.plan.postgresql-stage6-restart-2026-10-03
version: 1
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
| Restore | One reviewed disposable private recovery instance; the existing fixed identifier is not permission to reuse an uncertain or pre-existing instance. |
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

Every future external action requires the approved exact source, image, target,
operation bounds and responsible coordinator. A failed predecessor prevents onward
execution. The table defines a review sequence, not a command runlist.

| Operation | Evidence required before action | Bounded action and acceptance |
| --- | --- | --- |
| Discover/reconcile | Historical sessions and durable backups, exact local source, protected identity, no competing operator. | Read current stacks/tasks/labels, configuration metadata, queues, database/restore state, alarms and budget. Resolve recovery-4 and unknown operations. Record only safe verdicts and operation references in their permitted storage. |
| Source qualification | Reviewed instruction amendments and narrow source patches; no pending ownership conflict. | Run focused controller/regression checks, adapter/product checks and disposable real-database tests. Demonstrate failure/duplicate/fence handling, least privilege, redaction and cleanup. |
| Artifact qualification | Exact source revision and build inputs, required scanner/attestation results. | Publish only through the existing workflow after approval; pull the immutable digest and execute the actual image/entrypoints. No host-only build or separately rebuilt smoke image substitutes for this proof. |
| Refresh target prerequisites | Current resource discovery and approved assessment scope. | Use existing Foundation/Service/artifact assessors only where needed; preserve classified parameter normalization and reject other drift. Fresh live-boundary proof confirms private/encrypted/TLS/network/operations posture. |
| Bind candidate | Reviewed candidate-only change set and fresh candidate-baseline Service evidence. | Modify only the existing candidate task definition to the qualified digest; preserve non-image properties. Use the amended existing candidate controller; require healthy then stopped and no lingering candidate. |
| Promote shared image | Candidate passed for exact digest/revision; fresh Foundation/Service evidence; recorded previous good template, parameters, images and revisions. | Existing bootstrap-recovery reconciler permits eight existing task-definition replacements plus two in-place service references, with zero additions/removals. Execute only that reviewed scope; verify health and all resulting identities. |
| Bootstrap only | Fresh reconciled fixed label, exact task revision/image, TLS/secret/role proof, empty queues, server `1/1`, worker `0/0`, healthy stacks/database. | Run exactly one reviewed bootstrap. Require successful terminal outcome and unchanged aggregate boundary before continuation. No migration, relay, worker or restore on failure. |
| Continue once | Successful exact bootstrap predecessor and renewed immediate prerequisites; no consumed continuation label. | Migration applies the immutable manifest; relay accepts one fixed work item and produces one delivery; worker records completion before acknowledgement. Source/DLQ return to zero and due outbox is empty. |
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

## Limits, aborts and recovery

Proposed attempt limit: one reviewed image publication, one new candidate attempt,
one candidate binding, one shared-image promotion, one fresh bootstrap and one
continuation with one disposable restore. Failures stop the affected path; any
additional candidate, label, publication, data repair or permission expansion needs
an amended reviewed allowance. Include exact rollback actions in future approval.

Retain existing per-task wait `900s`, restore availability/deletion `1800s` each,
queue-settlement `90s`, and candidate start/stop `300s/120s` unless separately
reviewed. A timeout is a failed observation, not proof that remote work stopped.
Keep the candidate stopped before promotion; preserve steady server one/worker zero.
Record any permitted temporary service overlap from the exact reviewed ECS policy.

Set total wall-clock/recovery allowance and incremental cost ceiling after current
pricing/resource reconciliation and before execution approval. Historical database
estimates, the tag-scoped budget alert and the earlier HTTP `$10`/four-hour example
are not authorization for this work or automatic cost enforcement.

Abort for unexpected drift, unknown accepted operation, consumed label, identity or
digest mismatch, unsafe evidence, unresolved cleanup, unhealthy target, unexpected
permissions/exposure/cost, non-empty terminal queue or unproved restore scope.
Never fix freshness by editing timestamps or clear a queue to make a check pass.

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

## Completion and handoff

Completion requires the final image and exact task revisions to pass source,
adapter and target proofs; successful bootstrap/migration; one accepted/processed
delivery with empty terminal queues/outbox; appropriate duplicate/retry/fence
proof; restore coverage plus schema/checksum/state verification; completed cleanup;
healthy public service, dormant worker and protected database; operational alarms,
notification evidence, reconciled cost, rollback evidence and an owned runbook.

Record only safe stage/aggregate facts, source/image identity and approved evidence
references in the [Stage 6 evidence record](../../../../docs/aws/kanbien-staging-postgresql-relational-reference-v1-stage6-evidence.md)
and [session](../../../../commitLogs/2026/oct/03/2026-10-03-14-13-platform-restart-preparation/README.md).
Never retain credentials, endpoints, SQL, row/message contents, raw task logs or
provider responses there. Distinguish local fixture, actual-image, adapter and live
target outcomes. Single-AZ, RLS, product authorization, HA/RPO/RTO and broader
persistence adoption remain explicitly outside this bounded completion claim.
