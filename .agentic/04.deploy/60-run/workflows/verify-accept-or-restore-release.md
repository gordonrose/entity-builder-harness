<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.verify-accept-or-restore-release
version: 11
status: active
created_on: "2026-10-21"
updated_on: "2026-11-26"
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

### Connected ordinary-update invocation

The selected acceptance route's `ordinary_delivery` identifies the binding
consumed by the shared `release-succession/ordinary-update.sh` command. This is
the Deploy-to-Run connection, not another provider task engine or proof store.
Use only under the owning provider workflow's recorded operation authority:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action \
  scripts/04.deploy/lifecycle/60-run/release-succession/ordinary-update.sh \
  --scope-contract <scope>/00-declaration/declaration-contract.yml \
  --inputs <ordinary-update-inputs.json> --plan-release --json
```

Review the returned release boundary under the provider workflow and match it
to the recorded [end-to-end delivery authority](../../standards/operational-realization-gate.md#end-to-end-live-delivery-authority).
Do not request another approval solely because its exact hash is now known.
Execute the same invocation with `--execute --approved-release
<approval_sha256>` instead of `--plan-release`. The hash binds the exact input
bundle, packages, accepted predecessor, controller/configuration sources,
account/region, declared operations and protected resources. Planning is not
approval. Changed inputs require a freshly reviewed matching boundary; renewed
user approval is required only when the effects exceed the recorded authority.

The bounded JSON input has exactly `schema: deploy/ordinary-update-inputs/v1`,
`target`, `scope` and `values`. Both bindings require `candidate_receipt` and the
exact `expected_predecessor`, `rollback_receipt` and `rollback_compatibility_id`.
The qualified package and accepted-history readers
validate those references; strings alone are not authority or proof.
Entity's `rollback_compatibility_id` also accepts the explicit
`accepted-proof-<accepted-release-suffix>` selection governed by
[accepted-release restoration](../standards/retain-accepted-release-for-restoration.md).
It revalidates the complete accepted proof, exact predecessor package and shared
immutable operational-input comparison. It does not write a compatibility
record or report fresh live proof. Changes to schema inputs, permissions,
operational configuration or database incarnation reject that selection.

- Persistence adds a stable `delivery_label` and `operation_predecessors` using
  the exact predecessor placeholder names from its declared fresh proof commands
  and `current-health`. Select each original predecessor once; do not advance it
  to the newly launched task on resume. Reuse of the same values invokes the
  existing journal's original reservation/completion rather than another task.
- Entity adds `proof_label` and `expected_digest`. The former draft
  `approved_plans` map is removed: state-dependent hashes are derived only after
  the generated plan matches the approved release and bounded operation shape.
  Existing controllers still check exact plan hashes and their original gates.
  Recovery selects only its separately labelled rollback readiness/read tasks,
  using candidate controller custody and the compatible predecessor workload.

The entity binding selects the infrastructure controller's connected `apply`
mode. It first reconciles an existing execution using its original admission;
otherwise it performs `review` and then `execute` against the same approved
plan. A non-successful review stops that sequence. Individual review/execute
commands remain available, but an execute-only command cannot prepare a new
change set. This connection does not manufacture approval.

The connection runs the owned deployment, declared fresh checks and collector,
then the route's candidate validator and promotion command. Generated collector
manifests are temporary inputs, not trusted evidence. Accepted custody and all
operation evidence remain in their existing owners. An interrupted invocation
uses the same input bundle: child controllers reconcile original operations.
After interrupted promotion, exact accepted predecessor/package custody is
validated without redeploying; the result is `retained`, not fresh readiness.

Pending, uncertain, admission, collection and promotion failures stop progression
without selecting rollback. Only a declared verification stage's positive terminal
failure, validated against its original reservation and completed candidate
deployment, selects the already approved exact-predecessor restoration. Entity
reobserves the original reserved task; persistence validates its retained verifier
receipt and operation custody. Generic failure wording is not evidence.

On resume, an existing rollback preparation/execution takes precedence over
candidate deployment. Continue only that original recovery and privately check
the restored predecessor. Persistence preserves completed task journal entries
in the same journal owner's immutable history before advancing a mode's head;
this keeps candidate failure and recovery task identities distinct. No additional
release journal is introduced. Its stable-stack restoration may recover a stopped
candidate, but not repair a failed CloudFormation stack. No migration, grant
change, scope activation or source-data deletion is selected. Changed recovery
inputs select the separately declared successor requalification sequence below;
that sequence must appear in the approved release boundary before execution.
Successful recovery reports the candidate as failed and the predecessor restored;
it never promotes the failed candidate or counts as successful delivery.
This invocation's duration is not the build-to-live delivery measurement: the
report explicitly marks the delivery budget not established.

Use the [realization proof-applicability assessment](../../standards/operational-realization-gate.md#proof-applicability-by-change)
from the change inventory. Acceptance still requires the selected declaration
and collector to agree; neither a routine-release label nor a faster report
waives their current proof set. Preserve original evidence when qualifying a
more reusable successor route.

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
   or acceptance. Promotion validates retained proof and rechecks the current
   workload identity and health and database identity; unchanged historical proof
   is not recollected or invalidated solely by age. Historical proof alone does
   not establish that database permissions remain unchanged out of band.
   The [collector](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/implementation/acceptance-route.py)
   derives the selection; the
   [source guard](../../../../scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/script.py)
   enforces exact paths, bytes and Git status. The existing
   [route fixture](../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/tests/acceptance-route-test.py)
   exercises the actual Git boundary and partial-copy reconciliation separately
   from its controlled proof prerequisites.
5. For an approved update/restoration rehearsal, retain the original accepted
   baseline and record candidate proof separately. Continue with restoration;
   do not declare the candidate current after restoring the original release.

## Restore and Verify

### Ordinary acceptance and recovery-proof reuse

Both persistence and entity-smoke use the shared Run
`release-succession/proof-policy.py` comparison and their existing acceptance
schemas' `ordinary_update` declarations. The shared comparison does not prove
accepted custody or current health; collectors establish those separately.
First qualification keeps its complete proof set. Missing historical bindings,
changed input selectors, changed protected Git objects, contracts or database
incarnation require requalification. The shared requirements comparison names
the changed bindings; it is not successful proof or cloud authority. Source
database incarnation and original-record changes remain rejected by the feature
requalification route rather than treated as permission to replace source data.

Persistence accepts an `acceptance-inputs/v1` manifest with
`release_mode: ordinary-update` and the exact `ordinary_update_inputs` keys from
its route. Collect fresh migration state, effective privileges, runtime identity
access and workload read proof, followed by fresh readiness. Each receipt must
name the current image/definition and postdate both the running deployment and
accepted predecessor. The collector observes current service/source identity
and database posture, not the old restore clone. It retains an immutable
observation and predecessor reference in the existing succession candidate.
It cannot reuse a legacy record missing recovery bindings: a full qualification
must establish those facts first. The old restore-verifier-only applicability
format is read-only historical compatibility, not a new-release exception.

#### Entity-smoke task sequence

The owning acceptance route declares `expected_predecessor` alongside the
candidate receipt, stable original-record proof label and digest. Use `none`
only for first acceptance. For an ordinary update, the collector requires its
checked update receipt and a distinct delivery-bound sequence: current runtime
permissions, the feature lifecycle smoke, collision behaviour, migration-state
observation and final
original-record read. Each operation retains its own preflight, original plan,
prerequisites, reservation and completion. Synthetic lifecycle data uses the
delivery's derived label; the original data check retains the stable label.

The existing acceptance schema owns recovery-input selectors. Actual source
trees, configuration/permission contracts and database incarnation must still
match before earlier recovery capability evidence can be used. A changed or
removed protected input selects the declared successor requalification below;
ordinary evidence reuse does not claim that fresh proof succeeded. The retained v1 reader
continues to validate the original full qualification; v2 historical and v3 current records reference
accepted predecessor custody rather than copying or restamping its proofs.
New entity promotion requires v3's fresh migration-state proof or v4's complete
successor requalification; historical v2
records remain readable. Promotion rechecks current applicability, live
observations and exact predecessor.
These local implementation checks do not establish the ten-minute live target.

#### Successor recovery requalification

Use the same coordinator, accepted-history owner, task runner, resource controls
and evidence store. The acceptance schema declares the fresh task/control set;
the release approval binds that set and the exact changed-input assessment.
Do not reset acceptance or replay initial bootstrap, migration or grants.

The feature sequence starts from its completed checked update, fresh effective
permissions, lifecycle/collision checks, migration observation and read of the
preserved original record. It observes permissions, revokes only the feature's
runtime access, proves live-but-unready, restores that access, replaces the
runtime and proves original-record read plus effective permissions. It then
creates one snapshot, restores one owned eight-resource clone, reads the original
record there, deletes only that proven clone, and obtains fresh final readiness
and original-record read on the source runtime.

Controller provenance, every original reservation/admission, complete task and
control gates, chronology, unchanged source incarnation and predecessor custody
remain mandatory. Fresh proof has its own v4 packet; old accepted proofs are
neither copied nor restamped. Snapshot/clone names derive from the delivery id,
while record checks retain the original label and digest. The initial stop-only
failure policy is not available for an accepted successor. Recovery still needs
the exact compatible predecessor, with feature runtime access restored first.

A positively observed terminal failure of the original revoke or unready task
may admit only the already-declared access-restoration operation before
predecessor recovery. Missing or uncertain task evidence does not qualify.
Retain the failed task and its original reservation; never retry it or count the
restoration as a successful capability proof. A previously completed, bound
restoration may be reused after server replacement without demanding that the
old stopped server still be running.

New delivery task-step v3 packets retain hash-bound references to validated
prior task packets instead of embedding the same evidence recursively. The
collector must compare every reference with the independently validated task
archive. Older v2 packets remain readable for actual retained custody.

This is additional capability qualification, not routine deployment timing.
Unchanged protected inputs continue to use the smaller ordinary sequence. The
persistence consumer retains its existing strict applicability requirement until
its own declared requalification binding exists; shared classification alone
does not implement or authorize another consumer's recovery actions.

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

Report delivery-budget outcome separately using the shared
[accounting rule](../../../shared/testing/standards/test-execution.md#delivery-budget-accounting).
Only terminal required verification and acceptance can close a successful
delivery measurement. Include available preceding build/package/deploy timing;
missing connected timing means the budget is not established. Publication,
submission, readiness alone or a successful restoration is not successful
delivery of the rejected candidate.

Historical succession validation checks the retained evidence hashes and full
predecessor lineage without comparing historical contracts to today's files.
New candidate promotion and fresh rollback-compatibility records still require
exact current configuration/permission contract hashes. The separately declared
accepted-proof reuse comparison binds both original and current configuration
hashes and permits only non-operational test-selection metadata differences;
it never changes historical bytes. This permits a corrected successor
without rewriting or invalidating genuine historical proof.
