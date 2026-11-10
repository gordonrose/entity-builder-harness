<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.verify-accept-or-restore-release
version: 6
status: active
created_on: "2026-10-21"
updated_on: "2026-11-10"
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
   For the approved entity-smoke acceptance route only, recognize the collector's
   exact generated proof JSON and candidate YAML as evidence additions, not
   executable-source changes. Derive their paths, byte lengths and hashes from
   its original validated immutable collection observation, bound to the current
   qualified source/image/receipt/controller and original record. Admit only those
   matching untracked additions during acceptance, including reconciliation of a
   partial copy. Keep HEAD equal to the qualified source; reject changed bytes,
   symlinks, staged or modified tracked files, unrelated additions and all source
   or configuration dirt. Ordinary operational callers remain strict. Retain these
   files for normal evidence validation and the later evidence commit;
   neither a blanket ignore nor a caller-supplied CLI allowlist is permitted.
   This classification grants no AWS authority, freshness, successful collection
   or acceptance: promotion still reobserves the full declared live proof.
   The [collector](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-route.py)
   derives the selection; the
   [source guard](../../../../scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/script.py)
   enforces exact paths, bytes and Git status. The existing
   [route fixture](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-route-test.py)
   exercises the actual Git boundary and partial-copy reconciliation separately
   from its controlled proof prerequisites.
5. For an approved update/restoration rehearsal, retain the original accepted
   baseline and record candidate proof separately. Continue with restoration;
   do not declare the candidate current after restoring the original release.

## Restore and Verify

### Eligible initial scope

If the scope declares the optional initial-release policy, select its applicable
recovery through the existing release-succession command:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action \
  scripts/04.deploy/lifecycle/60-run/release-succession/script.sh \
  --operation select-recovery --scope-contract <canonical-scope-contract> \
  --evidence-root <scope>/30-release-evidence --json
```

Require complete health/declaration and lifecycle validation separately. The
selector binds the local evidence directory and accepted history; it does not
inspect AWS, prove rollback compatibility or perform a recovery operation.
Confirm fresh live alignment and revalidate the selected custody at the owned
execution boundary, so concurrent acceptance cannot turn an old initial result
into authority to stop an accepted deployment.

If the selected policy is `stop-own-scope-workloads-preserve-data`, use only the
approved, labelled provider stop control for this scope. Preserve database data
and migration history, verify owned workloads stopped and other scopes unchanged,
and retain the safe terminal receipt. Reconcile an uncertain stop before another
effect. Stop if that control or proof chain is not implemented. Do not emit an
accepted release for a failed first deployment. A later attempt still needs its
own reviewed plan; migrations are observed, not blindly replayed.

First acceptance still requires the separate original-record replacement and
isolated-database-restore proofs. Only after all applicable proofs pass may its
verified candidate be promoted with `--expected-predecessor none`; an orphaned
accepted history is a reconciliation block. Once custody exists, the selector
chooses the normal compatible-image restoration policy below. The conditional
policy may remain in the declaration; it cannot be selected for later releases.

### Existing accepted release

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

## Bounded Connection Investigation

A connection diagnostic is a separate non-accepting operation against an owned
disposable restored database. The selected scope declares its controller mode,
record/snapshot binding, task identity, attempt/deadline limits and cleanup.
It does not recreate a database, replay migrations, rotate credentials, promote
a release or satisfy recovery acceptance. Only the existing recovery verifier's
accepted receipt can meet that obligation.

The diagnostic controller reserves one launch per database incarnation before
submitting its task. An uncertain response, interrupted invocation, expired ECS
task retention or missing logs permits observation of that reservation and task,
never another launch. The existing recovery verifier keeps its own single-run
identity. Log reconciliation reads at most three pages/observations per stream
per invocation and retains new closed observations without rewriting earlier
reports. Collection/write failure is reported separately from the original
operation result. Deployment authority owns live execution and temporary access.

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

Historical succession validation checks the retained evidence hashes and full
predecessor lineage without comparing historical contracts to today's files.
New candidate promotion and rollback compatibility still require exact current
configuration/permission contract hashes. This permits a corrected successor
without rewriting or invalidating genuine historical proof.
