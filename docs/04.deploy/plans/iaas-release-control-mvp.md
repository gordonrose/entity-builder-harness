<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.iaas-release-control-mvp
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre, agentic]
kind: plan
purpose: Bound the first usable AWS staging release path and defer additional checks unless concrete blocker or drift risk requires them.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
- id: deploy.plan.iaas-release-control-progress
  path: docs/04.deploy/plans/iaas-release-control-progress.md
-->

# IaaS release-control MVP — B02, 2026-09-30

## Outcome and scope

**One repeatable, controlled release path for the existing AWS `kanbien/staging`
platform target, using the existing deployment scripts and realization gate.**
A repo update can be built into an exact artifact, checked against current target
prerequisites, reviewed for its effects, executed with explicit authority, and
verified with recoverable, durable evidence. First make that path usable; expand
coverage later. No new deployment framework or general language-analysis project.

This is the user's requested scope/prioritization revision after B01, not an
assertion that unfinished full-plan requirements are complete. The full
[progress ledger](iaas-release-control-progress.md) and
[original plan](../../../.agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md)
remain the wider roadmap. U01–U16 remain accepted components to reuse.

Selected scope includes every command, resource, dependency, sidecar, identity,
workflow and recovery/cleanup action actually required by this platform release
path. It includes server startup and the bootstrap, migration, relay, worker and
restore/preflight graph needed for later PostgreSQL Stage 6 readiness. This does
not implement new PostgreSQL product features or authorize its live execution.
Unrelated RAG releases, legacy targets and repository-wide migration are deferred;
shared resources and callers capable of affecting this same target are not
unrelated and must remain within the safety review.

## Five fixed delivery milestones

These are outcomes, not a claim of five equal coding sessions. Each has source
acceptance and, where required, separate current target/hosted acceptance.
Nothing is marked newly complete by this planning change.

| ID / status | Done when | Reuse / full-plan mapping |
| --- | --- | --- |
| M1 / partial | Produce a versioned selected target/release blueprint validated by the existing compiler with positive/negative fixtures; freeze its graph, commands, artifact inputs, resource/identity boundary and recovery routes. Trace reachable build/deployment callers and dependencies; reconcile missing or hidden selected paths. Bind current source/configuration revisions and explicit owners, permissions, cost/attempt limits, authority expiry and cleanup rules. Classify every discovered gap as necessary now or backlog. | U01–U05/U12/U14/U16; selected parts of R1. No whole-repository zero-findings requirement. |
| M2 / partial | Qualify the current exact image and every selected command with appropriate dependency/effect tests. Reuse existing build, SBOM, scan, provenance and signature controls with verified current receipts. Changed artifacts invalidate affected proofs; health cannot replace job completion or restore proof. | U07–U11/U16; selected R2. Renew the image proof invalidated by U16; do not rebuild generic verification machinery. |
| M3 / partial | Connect existing AWS inspection, template/change-plan and preflight commands through thin profiles in the existing gate. Verify selected account/region/resource identity, IAM, injected configuration/secret shape, network/TLS, dependency reachability, capacity/cost and evidence paths. Candidate runtime proof and each task's no-effect preflight are distinct. Return one safe, source/digest/target-bound readiness and effect summary. | Existing deployment checks; selected R4 and R7.1. Source fixtures first; current provider proof stays separate. |
| M4 / partial | Wire one supported release command to the existing compiler/engine and selected workflow. Enforce current evidence/authority, one writer, durable intent before effects, bounded attempts, unknown-outcome reconciliation, safe receipt retention and cleanup. Existing supported callers for this target join that boundary. Prove interruption/retry refusal and recovery through the public path. | U01/U04/U13/U15; necessary R3/R5/R6. Local SQLite alone does not prove shared writer exclusion or production durability. |
| M5 / open | After specific approval, rehearse the immutable staging graph with its actual artifact, identities and commands. Verify intended effects, basic telemetry and alert receipt, interruption/denial handling, rollback or forward repair/restore, and final cleanup/steady state. Preserve evidence and prove stale inputs are refused before a subsequent operation. | Selected R7 with minimum R8 signals. Source-ready is not live-proven. |

The selected blueprint, exact-image publication handoff and task/passive
preflight components are now accepted as U17–U19; see the
[B03 acceptance record](release-control-source-adoption/2026-09-30-mvp-selected-path/README.md) for before/after outcomes and exact evidence.
This closes named source/local subcriteria, not the five complete milestones.
The first AWS passive observation blocked on stale drift evidence; no task or
resource was changed. Hosted publication and per-task live proof remain open.

The next bounded M4 component is also accepted as **U20: versioned selected
operation/shared-store records and conditional backend conformance**; see the
[B04 evidence](release-control-source-adoption/2026-09-30-selected-store-conformance/README.md).
The full clean run passed 2,173 tests in 68 suites. This uses an injected fixture
transport and cannot grant authority or prove live durability. M4 stays partial.
The user accepted the [operating policy](iaas-release-control-mvp-control-policy-proposal.md)
for source implementation. Next integrate one existing candidate start, health
observation and controlled stop through durable shared execution, authenticated
admission, unknown-outcome/cleanup reconciliation and selected-caller refusal.
Specifically approved store bootstrap, hosted/target acceptance and M5 rehearsal
remain ahead. No extra milestone is added; the live MVP is not complete tonight
within this batch's timebox.
The current batch ends by 21:10 UTC under the user's three-hour maximum; this
supersedes the earlier weekly-allowance stop for this batch.

## Safety floor and honest qualification

- Preserve the 17 ordered gates and source-result authority refusals. No removed
  row, unsupported `not-applicable` claim or fixture-only promotion. Current
  pre-execution gates must pass before effects; execution/recovery evidence is
  collected at its proper phase. Stage 17's long-window evidence remains pending.
- A scoped staging rehearsal is not full-programme or production qualification.
  The existing engine needs an explicit reviewed qualification operation and
  scoped evidence/decision boundary if it cannot currently represent that state.
  Implement and test that in M4; never reinterpret a blocked source exit code as
  permission or build a parallel route around the compiler.
- One writer must be enforced across every permitted host, workflow and manual
  route able to mutate the selected scope. If existing controls cannot ensure it,
  the minimum shared lease/fence store is necessary now. A local mutex, workflow
  convention or postponed high-availability project is not a substitute.
- Durable intent/evidence must survive controller restart and remain retrievable
  from the approved execution environment. Bind source, image, target, identity,
  attempts, effects and cleanup. Unknown outcomes stop replay; reconciliation
  handles in-flight provider effects that a local lock cannot cancel.
- Reuse existing policy values and evidence services where adequate. No invented
  trust identity, vulnerability exception, owner, budget, RPO/RTO or retention
  value. Unresolved decisions actually needed by this path block its execution.
- Keep secret values/private provider responses out of source and public evidence.
  Legacy resources, DNS, main and unrelated worktrees remain protected. Source
  work authorizes no push, hosted activation, resource creation or live Stage 6.

## Backlog-first rule for new findings

A new check goes to the backlog by default. Merely being useful, general,
unsupported by a static parser, or part of the eventual roadmap is insufficient
reason to interrupt the selected delivery unit.

Promote a finding to **necessary now** only with a recorded, credible chain from
observed code/configuration or a reproduced failure to at least one of:

1. A likely blocker of the selected build, preflight, deployment or recovery path.
2. Wrong target/identity/effects, secret exposure, destructive change, concurrent
   writers, duplicate effects, lost operation state or unverifiable cleanup.
3. Acceptance of stale/mismatched source, artifact, configuration, permissions
   or target state; an unobserved dependency/caller capable of material drift.
4. A known approval, security or target policy requirement the selected operation
   would otherwise violate, or a failure its required evidence cannot detect.

Each promotion records: finding/evidence; affected M ID and exact operation;
likelihood and consequence; existing control and why insufficient; smallest fix;
acceptance check; and impact on the current batch. No numerical risk score or
hypothetical worst case alone justifies promotion. If outside the selected path,
keep it deferred unless evidence shows a shared-resource or bypass risk.

Necessary ordinary source fixes stay within the authorized batch and are
reported visibly; do not ask again for routine repair permission. A promotion
requiring external mutation, destructive action, a material scope expansion or
an irreducible policy decision still needs the applicable explicit approval.
For an unresolved credible high risk, fail the affected operation closed rather
than using the backlog as a waiver. Batch acceptance is not held up by deferred
checks with no such dependency. Do not silently add milestones.

## Initial deferred backlog

Status of every row is deferred, not implemented, exempt or approved. The owner
is programme intake until a specific accountable owner accepts the item. Revisit
on the named trigger; no automatic implementation merely because it is listed.

| ID | Deferred work / full-plan reference | Trigger to reconsider |
| --- | --- | --- |
| B01 | Whole-estate source closure and all 403 adoption proposals; R1.1/R1.3 and wider R6 | Another target/path enters scope or a caller can bypass/corrupt the selected path |
| B02 | Universal action/default/tool analysis and unsupported language semantics; wider R1.2/R1.3 | Selected action inputs, artifact trust or authority cannot be established by bounded existing checks |
| B03 | General cross-cutting policy engines and all unused profile contracts; wider R1.4/R5.2 | Selected operation needs a missing contract; implement that contract only, not the entire framework |
| B04 | Other image families, unrelated executable profiles and exhaustive compatibility combinations; wider R2 | They become release dependencies or a selected migration/rollback requires that combination |
| B05 | Multi-runner/high-availability storage and control-plane expansion; wider R3 | Additional writers/hosts or recovery requirements exceed the enforced MVP model; minimum shared locking/durability remains in M4 |
| B06 | AWS operations and environment permutations outside the selected graph; wider R4 | Target composition actually adopts the resource, service or operation |
| B07 | Automated break-glass, general resource decommissioning and broad controller self-hosting automation; wider R3.3/R5.2 | Such an operation is proposed; MVP refuses unsupported emergency/destructive modes and still bounds bootstrap authority |
| B08 | Repository-wide wrapper retirement, unrelated workflow migration and broad documentation conversion; wider R6 | A supported path migrates, or existing target callers can bypass the common authority boundary |
| B09 | Rich dashboard, comprehensive scheduled controls and complete 28-day programme observation; wider R8 | After staging qualification, or earlier if a missing signal/expiry check would hide selected-path failure or drift |

Other-cloud adapter implementations remain outside this MVP; this is not a new
commitment to implement Azure, Oracle or Snowflake. Keep neutral existing
contracts without speculative provider machinery. Existing tests and controls
remain in place; deferral concerns additional implementation, not disabling them.

## Progress and completion reporting

Before a batch, name its M ID and concrete acceptance boundary. Afterward report:
accepted criteria and evidence; remaining criteria; new backlog rows; any
necessary-now promotions with reasons and cost to the batch; exact next unit;
and real approval/stop condition. Preserve the full R register's unfinished
status; do not mark an R milestone complete because its MVP subset passes.

MVP source-ready means M1–M4's source/local checks make a specific staging
rehearsal reviewable. MVP live-proven requires M5's actual scoped qualification.
The 28-day window and wider roadmap remain explicitly unqualified. There is no
new date or slice forecast in this revision. M1 must expose the actual remaining
integration work before another estimate is offered.

B02 delta: accepted deliveries remain 16; no new runtime capability. The user
changed the active scope from completing the entire roadmap to an MVP with
backlog-first intake. Whole-R1 completion is no longer the immediate goal.
That planning update started no implementation or live run. The subsequent
B03 batch is authorized and uses the user-approved maximum roughly three-hour
timebox, ending by 21:10 UTC; the user explicitly withdrew the allowance stop
for this batch. B03 acceptance and remaining criteria are recorded above.
