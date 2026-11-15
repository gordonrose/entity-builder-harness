<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.release-update-and-recovery
version: 5
status: active
created_on: "2026-10-20"
updated_on: "2026-11-15"
layer: 04.deploy
domain: deployment.release-lifecycle
disciplines: [security, sre]
kind: workflow
purpose: Execute a bounded update to an accepted deployment scope and hand its evidence to run-stage verification and recovery.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.standards.accepted-release-and-recovery
  path: .agentic/04.deploy/60-run/standards/retain-accepted-release-for-restoration.md
- id: deploy.workflow.verify-accept-or-restore-release
  path: .agentic/04.deploy/60-run/workflows/verify-accept-or-restore-release.md
-->
# Review and Execute Target Update

Use this workflow when a selected target already has an accepted healthy
release. The provider-specific workflow owns exact commands and inspection and
mutation authority. An absent foundation or runtime requires its separately
governed creation route; this workflow does not recreate the target.

Follow the [shared change-completion principles](../../../shared/standards/require-change-completion.md) for consumer impact, selected verification, continuation and evidence reporting.
The [deployment proof standard](../../standards/operational-realization-gate.md) owns cross-phase proof requirements; this workflow applies its stage-specific controls.

## Inputs and Readiness

Select the scope declaration, retained accepted release, runnable-program and
image contracts, and publication route. Follow the build and package workflows
linked from the lifecycle map. A new capability must first satisfy declaration
coverage; existing exclusions are not implicit authority to expand the scope.

Reconcile [proof applicability](../../standards/operational-realization-gate.md#proof-applicability-by-change)
against those declarations before selecting checks. Refer to valid earlier
build/package proof through its owning readers rather than independently
repeating preparation. Carry source/artifact identity and available stage
observations forward under the shared [delivery accounting](../../../shared/testing/standards/test-execution.md#delivery-budget-accounting)
rule; starting Deploy does not restart the delivery clock. If cross-stage
timing is unavailable, say so without inventing a new execution journal.

Before unattended work, resolve the worktree and tool/dependency setup, exact
committed source revision, permitted operations, credential availability,
publication approval mechanism, and expiring provider conditions. Use existing
approval evidence; request only missing authority or a change of scope. Check
account capability before claiming an external approval can only be performed
by the user. No recorded intention bypasses a protected gate. Continue
independent local work when an external prerequisite blocks mutation.

## 50 Deploy Procedure

1. Confirm declaration coverage, build/package qualification and the exact
   receipt for the immutable candidate. Qualification is not deployment.
2. Read and validate the scope's current accepted-release reference without
   changing it. Retain the immutable history. Run the scope's connected
   release-contract check against image and target together.
3. Run fresh update alignment. It must prove the live workload matches the
   retained accepted baseline before a new candidate is proposed.
4. Under the required creation authority and valid provider conditions, create
   and review a bounded UPDATE change set. Creation itself may be a provider
   mutation; it does not authorize execution.
5. Under explicit execution authority, execute that exact reviewed change set
   and wait for completion. A started task or successful submission does not
   prove a healthy release.
6. Pass the receipt, deployment result, reviewed change identity and retained
   baseline to
   `.agentic/04.deploy/60-run/workflows/verify-accept-or-restore-release.md`.

For the entity-smoke adapter, use its existing infrastructure command with
`--phase update` and the exact `--expected-predecessor`; create/activate are
initial deployment operations, not aliases for an update. The same shared
change-set and reservation owners review, submit once and reconcile updates.
Supply `--rollback-receipt` and `--rollback-compatibility-id` for the update
too: compatible recovery is checked before deploying, not discovered only
after the candidate fails.
Before submission, the adapter checks the existing acceptance schema's
recovery-input boundary against both immutable source revisions. Changes to
that boundary require affected capability requalification, not a silent
readiness-only acceptance. Keep the original proof label/data ownership and
use the derived delivery namespace for new operation receipts.

Recovery uses `--phase rollback`, the same candidate/controller receipt,
and the separate `--rollback-receipt` and `--rollback-compatibility-id`.
Compatibility must cover every image role the actual template updates.
It never rewinds migrations, widens grants or promotes the failed candidate.

## Stop Conditions and Output

Stop when the accepted record and its retained verification proof, package
receipt, alignment, release-contract gate, reviewed change set or provider
authority is absent or mismatched. Candidate verification follows in Run.
Do not discover a substitute procedure in a historical plan.

An interrupted response or failed wait is an uncertain operation: inspect the
existing operation through the governed provider read route before repeating
an effect. Retain a safe deployment-operation diagnostic and its opaque
evidence reference before cleanup or deletion. The report must preserve the
original failure, say whether the provider outcome is known, and name only the
next permitted observation or retry decision. A deterministic name alone does
not make a retry safe.

Output a deployed candidate and its safe evidence for Run. Only Run-stage
verification and acceptance may advance the accepted baseline.
