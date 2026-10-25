<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.verify-accept-or-restore-release
version: 4
status: active
created_on: "2026-10-21"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.release-lifecycle
disciplines: [security, sre]
kind: workflow
purpose: Verify a deployed candidate and accept its exact identity or restore and verify the retained release under explicit authority.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.workflow.release-update-and-recovery
  path: .agentic/04.deploy/50-deploy/workflows/review-and-execute-target-update.md
-->
# Verify, Accept or Restore Release

Follow the [shared change-completion principles](../../../shared/standards/require-change-completion.md) for consumer impact, selected verification, continuation and evidence reporting.
The [deployment proof standard](../../standards/operational-realization-gate.md) owns cross-phase proof requirements; this workflow applies its stage-specific controls.

## Use When and Inputs

Use after Deploy hands over a deployed candidate, its qualified receipt,
reviewed change identity and deployment result, and the unchanged accepted
baseline. Follow
`.agentic/04.deploy/60-run/standards/retain-accepted-release-for-restoration.md`
and the selected provider workflow for concrete commands and authority.

## Verify and Accept

1. Validate the scope's health, failure, and recovery declaration through
   `verify-health-failure-and-recovery.md`. Stop when its structure, safe
   diagnostics, proof ownership, or recovery boundary is incomplete.
2. Confirm rollout and workload health before running the declared meaningful
   operation verifier. Use the deployed candidate's receipt.
3. Require the workload digest, application source identity and receipt to
   agree. Process health alone is insufficient. Retain the safe report.
4. For a normal accepted update, collect the target's verified release-candidate
   record, then use the release-succession command with the exact current
   release id as `--expected-predecessor`. It archives immutable evidence before
   atomically advancing the current reference. Retain prior release evidence for
   recovery; the image source revision is distinct from the evidence commit.
   Do not directly overwrite an `accepted-release.yml` file.
5. For an approved update/restoration rehearsal, retain the original accepted
   baseline and record candidate proof separately. Continue with restoration;
   do not declare the candidate current after restoring the original release.

## Restore and Verify

1. Revalidate the scope's health, failure, and recovery declaration before
   provider restoration steps; its immutable recovery rule must still match the
   selected accepted baseline.
2. On rejected or unproved verification, keep the existing accepted baseline.
   A failure alone does not authorize restoration.
3. Select the retained immutable package and its receipt/evidence, preserving
   the original source revision. Establish that its configuration and permission
   contract are compatible with the current target before restoration. Do not
   rebuild earlier source, reuse the rejected candidate's receipt, re-broaden
   data privileges, or use legacy history with unrecorded permission facts as
   an automatic rollback candidate.
   When an earlier retained image predates the permission model, require a
   fresh release-succession rollback-compatibility record. It must bind that
   exact image and source identity to the current configuration/permission
   contracts and completed proofs for every workload actually selected by the
   rollback. Do not replay a completed migration merely to produce this proof.
4. Follow the provider's bounded restoration control for fresh alignment,
   condition checks and change review. Execute only under restoration authority.
5. Privately verify the restored release. If the restoration wrapper includes
   verification, observe that invocation's result; do not independently launch a
   second verifier because the wrapper's response was interrupted.
6. Reconcile the immutable release history and current reference with actual
   restored workload identities and proof. Retain candidate and restoration
   evidence separately.

## Uncertain Results and Completion

Use existing logs, receipts and provider operation identities to inspect an
interrupted operation before repeating it. Reusing completed verification is
not proof that pending, running or concurrent invocations are safe to repeat.
If the selected command cannot reconcile state, stop that effect and report the
precise uncertainty through its governed diagnosis route.

Complete only when the declared final release is healthy, independently verified
and reflected in the accepted record. Output the candidate verdict, final live
identity, accepted record and safe evidence references. No result grants new
permissions, expands the scope, or substitutes for missing mutation authority.
