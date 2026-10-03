<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.controlled-recovery-replacement-2026-10-03
version: 2
status: draft
layer: 04.deploy
domain: infra.ci-cd
disciplines: [architecture, agentic, sre]
kind: implementation-plan
purpose: Propose practical concurrent delivery and learning after controlled recovery without implementing or authorising deployment.
portability: {class: internal, targets: [entity-builder]}
used_by:
- id: deploy.plans.readme
  path: docs/04.deploy/plans/README.md
-->
# Proposal for deployment recovery and parallel learning

Prepared for the owner on 3 October 2026. Local preservation and a tested source
reversal are approved. Merging the rollback, implementing this proposal and
resuming deployment remain separate decisions. The intended result is one
bounded deployment approval, with concurrent delivery and learning through
ordinary failures.

Before shared changes, complete the [recovery report's](controlled-recovery-report-2026-10-03.md)
durable evidence/backups, named preservation refs and inverse on a branch from
freshly verified live main. Compare against baseline with exact historical and
recovery-document exceptions; run checks there. Reassess the recognition index
on that branch, making only a narrow correction or obtaining an explicit
exception. Do not repair unrelated governance in the old integration workspace.
The workspace exception covers only its named local actions.

Verified inspection covers the configured account and all 17 enabled regions.
The current HTTP service is healthy; its image, reviewed templates and publisher
permissions predate or match baseline. No AWS resource rollback was identified.
The report retains historical-audit limitations. Readiness is still blocked:
[reconciliation run 37099261022](https://github.com/gordonrose/entity-builder-harness/actions/runs/37099261022)
rejected stale artifact-stack drift evidence; foundation retains the known
parameter-group representation difference. Metadata requires TLS, but no new
database connection was tested. PostgreSQL recovery-4 remains unfinished.

HTTP is the first delivery milestone; PostgreSQL is next in the agreed sequence,
with separately bounded execution. Healthy HTTP does not complete database work.
Follow existing [platform ownership](../../../.agentic/03.product/plans/implementation/platform-runtime-implementation.md):
shared process owns coordination, AWS operations own provider behavior, and the
target owns service requirements. Do not copy the runtime package hierarchy.

First, supersede the conflicting instructions through small edits. These are
baseline `0da085b5` clauses, still effective until approved implementation:

| Instruction | Exact mandate to replace |
| --- | --- |
| `.agentic/01.harness/standards/operational-realization-gate.md`: Required Realization Contract, Mandatory Gate Sequence, Recovery and Retry Rules, Compliance | Universal contract/compiler and every preceding gate on every recovery. Substitute evidence needed for the approved operation. |
| `.agentic/01.harness/workflows/operational-realization-gate.md`: Use When, Procedure 1–7, Stop Conditions | Complete graph/normalized-adapter/compiler prerequisites for every changed path. Permit in-scope diagnosis, repair and bounded recovery. |
| `.agentic/03.product/plans/implementation/postgresql-relational-persistence-reference-v1.md`:589–607 | Whole-route generic migration before Stage 6 may be proposed. Replace with the next PostgreSQL work package and actual task preflights; retain controller limits at 639–650 until specifically revised. |
| `.agentic/aws/plans/implementation/local-to-proven-deployment-reliability.md`:35–42,59–63,84–87,196; `.agentic/aws/README.md`:57–62 | Whole-estate/all-provider completion and feature freeze. Mark superseded and route to this scoped sequence. |
| `docs/04.deploy/README.md`:29–32; `docs/04.deploy/plans/README.md`:36–38; `docs/04.deploy/plans/operational-realization-gate-programme.md`:46–63; `docs/04.deploy/plans/operational-realization-v2-programme.md`:24–28,70–93,116–130,182–196; `.agentic/01.harness/templates/operational-realization-contract.v1.guide.md`:82–94 | Add superseding applicability pointers so another entry point cannot revive the full graph/compiler programme or demand a new image for every diagnostic failure. Preserve real candidate proof, terminal-outcome checks and cleanup. |

Retain target approval, necessary preflight and escalation for new effects,
destructive changes, broader permissions or exhausted limits. No compiler/schema
rewrite is needed merely to remove blanket applicability. The existing AWS
execution workflow already accepts an approved change plan; clarify continuation
within that plan rather than asking about every command.

The minimum proposed layout is:

```text
.agentic/shared/workflows/deployment-recovery.md       shared coordination
.agentic/aws/workflows/execute-approved-aws-change.md  bounded AWS authority
scripts/04.deploy/reconcile-platform-shell-staging/    promotion/restore preflight
scripts/04.deploy/run-platform-shell-candidate-execution-preflight/ outcome recovery
scripts/04.deploy/smoke-test-platform-shell-image/     final-image execution
infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml service scope
.github/workflows/deploy-platform-shell-staging.yml   existing publisher
commitLogs/<session>/README.md                        existing ownership record
```

Reuse wrapper statuses and provider responses first. Add
`scripts/shared/deployment/observe-result.py` only for a demonstrated remaining
shared need. No speculative provider adapters, persistent control store,
receipt framework or extra general gate is proposed.

| Lesson | Carry forward |
| --- | --- |
| Managed PostgreSQL credential shape | Preserve the correction already at baseline. |
| Final-image commands | Extend the existing smoke wrapper with an existing-image/no-build mode; it currently rebuilds a separate smoke image. Run server and health commands from the publisher's pulled immutable digest. |
| Database effects/preflights | Reintroduce disposable real-database tests and actual task preflights when PostgreSQL resumes. |
| Image/task identity | Preserve source, immutable digest and exact returned task-revision checks. |
| Custom admission/journal framework | Leave retired. |

The publisher does not deploy. Reuse `.agentic/aws/workflows/execute-approved-aws-change.md`
and `docs/aws/runbooks/platform-shell-staging-rollback.md`. Delivery uses
`aws cloudformation create-change-set --change-set-type UPDATE --use-previous-template`
for `kanbien-staging-platform-shell-service`, reviews it, then runs
`aws cloudformation execute-change-set` and observes CloudFormation/ECS. Preserve
the execution role and every non-image parameter with `UsePreviousValue`.

Minimally extend `scripts/04.deploy/reconcile-platform-shell-staging/script.py`,
called by `npm run platform:shell:deployment-reconciliation`, with named HTTP
promotion/restore modes. The existing bootstrap-recovery mode is not HTTP
authority. Validate image-only parameters and non-image properties as well as
resource/action/replacement counts; the existing tuple comparison alone is
insufficient.

| Phase | Full permitted change and execution boundary |
| --- | --- |
| Candidate | Change only `CandidateImageUri`: replace `CandidatePreflightTaskDefinition` through the existing candidate-image mode. Run one isolated candidate, then prove it stopped before promotion. |
| Promotion | Change only `ImageUri`: replace `TaskDefinition`, `WorkerTaskDefinition`, `RelayTaskDefinition`, `RelationalBootstrapTaskDefinition`, `RelationalMigrationTaskDefinition`, `RelationalRelayTaskDefinition`, `RelationalWorkerTaskDefinition`, `RelationalRestoreVerificationTaskDefinition`; update `Service` and `WorkerService` task-definition references in place. Only HTTP runs; worker stays zero, relay and five PostgreSQL definitions stay dormant. No database, IAM, network or queue changes. |
| Restoration | Reverse `ImageUri` through the same scoped path; restore previous `CandidateImageUri` separately through the candidate-only mode. New revision numbers may differ: require previous image and equivalent configuration, not identical old ARNs. |

Capture the template digest, nonsecret parameters, both images, revisions,
counts, roles/network/commands and prior completed ECS deployment first.
Observe native rollback before another mutation; never race an in-progress
stack. The enabled circuit breaker needs a previous `COMPLETED` deployment;
it does not test arbitrary authenticated behavior or prove restoration of
all dormant definitions. Configuration/fixture checks are distinct from
witnessing live automatic rollback, which needs its own bounded rehearsal.
[ECS circuit-breaker behavior](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html)

The runbook's direct `aws ecs update-service` is emergency service-only recovery,
requiring explicit approval scope and subsequent CloudFormation reconciliation.
Its host-rule deletion fallback is excluded. The planned rehearsal ends on the
restored previous good image/configuration; another promotion would need budgeted
permission.

The active coordinator consumes command responses and GitHub run status, then
uses the available agent-launch tool to assign delivery and learning when a
failure occurs. Shell wrappers cannot launch intelligent agents themselves.
Demonstrate actual launches. Separate worktrees and one integrator preserve
ownership; only delivery gets external mutation authority. Both jobs persist
in the existing session record and resume after coordinator restart. No
unattended operation is promised after the host closes.

A failure requires investigation and a prevention decision, not necessarily a
new permanent component. Learning may confirm the existing refresh operation,
correct an instruction or add one focused regression. Prove the chosen remedy;
block delivery only for an immediate safety/correctness dependency. Preserve
managed credential rotations, backups and monitoring.

Extend the existing candidate wrapper: its useful failure/cleanup handling
currently lacks an explicit persisted `RunTask` token and safe lost-response
handling. Record exact parameters/token before submission; reconcile uncertain
outcomes before repeating while independent work continues. Same-token ECS
retries have a limited window: the shorter of 24 hours or task lifetime plus
one hour. A new token must not bypass uncertainty.
[AWS idempotency](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ECS_Idempotency.html)
GitHub reruns retain the original commit; changed source needs a fresh dispatch
and verified run SHA. [GitHub rerun behavior](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)

Illustrative future authority: account `337159794548`, `eu-west-1`, the exact
resources above; reviewed source repairs/publication; three image attempts,
one candidate binding/restoration, one promotion/restoration, server steady at one
and worker zero, temporary service overlap at most two with candidate already stopped;
four hours including 30 minutes recovery, $10 incremental ceiling. Include any
needed bounded active drift assessments explicitly; never edit timestamps to
fake freshness. Confirm pricing and identities before approval. Different
targets, broader permissions/exposure, persistent-data effects, destructive
changes, exhausted limits or loss of the recovery path require a new decision.

Costs below are estimates to measure, including the actual user and maintenance
burden of each component. Development estimates overlap; approval waits excluded.

| Component and user | Runtime/check cost; implementation and maintenance |
| --- | --- |
| Shared instructions; coordinator | Seconds; 1–2 days initially. Maintain authority/ownership clauses. |
| Existing result wrappers; coordinator | Focused tests under 1 minute; up to 1 day for needed changes. Optional shared adapter under 1 second/result; add only if justified. |
| AWS/candidate wrapper; delivery | Reads seconds, candidate budget 10 minutes, approved drift checks minutes; 1–2 days. Maintain native outcome/token cases. |
| Target profile; delivery/owner | Static under 1 minute, targeted live checks 1–5 minutes; half-day. Maintain actual resource boundaries. |
| Publisher/final-image smoke; build job | Build/scan/smoke 5–20 minutes per changed image; 1–2 days. Maintain packaging/dependencies. |
| Reconciler/CloudFormation; delivery | Focused tests under 1 minute, promotion/restore 5–20 minutes each; 1–2 days. Maintain image-change scope. |
| Session log; both jobs | Seconds/update; half-day integration. Preserve restart ownership; no hosted store. |

Archive the broad audit once. During repair refresh affected resources and
freshness only; broaden for new scope/findings. Run focused tests first;
rebuild when image inputs change. Run final route-wide checks on the final
source/image, retaining required commit checks without another general suite.

| Milestone | Demonstration and acceptance |
| --- | --- |
| 1. Replace blanket gates and define operations | Make the listed narrow instruction edits and scoped reconciler extension. Permit authorized recovery and dormant-definition updates; reject execution of those workloads, non-image changes and new effects. Measure checks. |
| 2. Run both responsibilities | Reproduce stale evidence: delivery uses the approved existing refresh; learning proves its prevention decision without assuming a new component. Real drift still blocks. Restart restores both jobs. |
| 3. Reconcile uncertainty | Test lost acknowledgement, then exercise an approved isolated candidate. Find the existing task, prove no duplicate launch and terminal cleanup while independent work continues. |
| 4. Deliver HTTP and prove recovery | Run the final registry-digest server/health commands without rebuilding. Candidate using that digest/revision becomes healthy then stops. Promote the new image; verify digest, ALB health and authenticated behavior. Restore previous image/configuration and candidate binding; verify all affected definitions, consistent stack, server one/worker zero, authenticated behavior again, unchanged queues and no running candidate/unresolved operation. Demonstrate the learning remedy independently and reconcile cost. |

These four milestones deliver the HTTP route and its recovery. PostgreSQL remains
the next unfinished delivery; none of this authorises its workloads today.
