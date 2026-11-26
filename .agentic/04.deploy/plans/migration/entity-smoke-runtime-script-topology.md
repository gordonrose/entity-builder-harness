<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.migration.entity-smoke-runtime-script-topology
version: 2
status: draft
created_on: "2026-11-22"
updated_on: "2026-11-26"
layer: 04.deploy
domain: migration
disciplines: [architecture, sre, agentic]
kind: migration-plan
purpose: Plan bounded retained-deployment isolation and focused Entity Smoke runtime folders without changing deployed behaviour, accepted evidence or provider authority.
portability: {class: source-only, targets: []}
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
- id: deploy.standards.lifecycle-stage-ownership
  path: .agentic/04.deploy/standards/lifecycle-stage-ownership.md
-->
# Deployment isolation and Entity Smoke runtime script topology

## Decision and scope

The active `60-run` entity-smoke route currently has 76 executable files at
one scope root.  Preserve the scope identity and its existing `bindings/`
tree, but move those direct files to focused operational folders.  A folder
states the objective; `implementation/`, `tests/`, and `commands/` distinguish
supporting roles where that improves reviewability.

The deployment manifest remains approved preparation, not permission to invoke
AWS/GitHub, alter releases or activate dormant RAG. The P6 first packet below
implements only two prelisted shared inspection relocations and placement
reconciliation. Existing deployment paths remain canonical until their own
reference and compatibility gates are completed in a later migration slice.

The canonical scope remains:

```text
scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/
```

## Protected boundaries

- Retain the existing `bindings/local-qualification/entity-smoke-proof/` tree;
  it is already focused and is not part of this move.
- Preserve current provider, package, release and proof behaviour.  This is a
  path-only refactor, not a replacement of the entity-smoke operation engine.
- Preserve accepted release records and proof receipts byte-for-byte.  Their
  historical source-path fields must not be rewritten.
- Do not update, regenerate, or make active
  `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`.
  It is dormant retained material, not a core-platform migration consumer.
- Preserve the unrelated local-qualification implementation already present in
  this worktree; its modified files participate in the move only with their
  current content intact.

## Exact path manifest

Each row is relative to the canonical scope above.  The destination is the
future authoritative location; old paths are **not** compatibility promises.

| Current relative path | Canonical relative path |
| --- | --- |
| `acceptance-controls.py` | `acceptance-evaluation/implementation/acceptance-controls.py` |
| `acceptance-evidence.py` | `acceptance-evaluation/implementation/acceptance-evidence.py` |
| `acceptance-route.py` | `acceptance-evaluation/implementation/acceptance-route.py` |
| `acceptance-state.py` | `acceptance-evaluation/implementation/acceptance-state.py` |
| `acceptance-steps.py` | `acceptance-evaluation/implementation/acceptance-steps.py` |
| `acceptance-aggregate-test.py` | `acceptance-evaluation/tests/acceptance-aggregate-test.py` |
| `acceptance-control-test.py` | `acceptance-evaluation/tests/acceptance-control-test.py` |
| `acceptance-route-test.py` | `acceptance-evaluation/tests/acceptance-route-test.py` |
| `acceptance-control-test.sh` | `acceptance-evaluation/commands/acceptance-control-test.sh` |
| `acceptance-state.sh` | `acceptance-evaluation/commands/acceptance-state.sh` |
| `administrator-observation.js` | `administrator-recovery/implementation/administrator-observation.js` |
| `administrator-recovery.js` | `administrator-recovery/implementation/administrator-recovery.js` |
| `administrator-observation-test.mjs` | `administrator-recovery/tests/administrator-observation-test.mjs` |
| `administrator-recovery-test.mjs` | `administrator-recovery/tests/administrator-recovery-test.mjs` |
| `control-completion.py` | `controls-and-readiness/implementation/control-completion.py` |
| `credential-steps.py` | `controls-and-readiness/implementation/credential-steps.py` |
| `deployment-control.py` | `controls-and-readiness/implementation/deployment-control.py` |
| `preflight-control.py` | `controls-and-readiness/implementation/preflight-control.py` |
| `resource-control.py` | `controls-and-readiness/implementation/resource-control.py` |
| `unready-control.py` | `controls-and-readiness/implementation/unready-control.py` |
| `credential-route-test.py` | `controls-and-readiness/tests/credential-route-test.py` |
| `deployment-control-test.py` | `controls-and-readiness/tests/deployment-control-test.py` |
| `infrastructure-route-test.py` | `controls-and-readiness/tests/infrastructure-route-test.py` |
| `preflight-control-test.py` | `controls-and-readiness/tests/preflight-control-test.py` |
| `resource-control-test.py` | `controls-and-readiness/tests/resource-control-test.py` |
| `failure-binding.py` | `failure-handling/implementation/failure-binding.py` |
| `failure-control.py` | `failure-handling/implementation/failure-control.py` |
| `failure-route.py` | `failure-handling/implementation/failure-route.py` |
| `failure-route-test.py` | `failure-handling/tests/failure-route-test.py` |
| `failure-plan.sh` | `failure-handling/commands/failure-plan.sh` |
| `failure-stop.sh` | `failure-handling/commands/failure-stop.sh` |
| `image-delivery-repair.py` | `image-delivery-repair/implementation/image-delivery-repair.py` |
| `image-delivery-repair-test.py` | `image-delivery-repair/tests/image-delivery-repair-test.py` |
| `acceptance-promote.py` | `orchestration/implementation/acceptance-promote.py` |
| `feature-steps.py` | `orchestration/implementation/feature-steps.py` |
| `ordinary-update.py` | `orchestration/implementation/ordinary-update.py` |
| `collect-acceptance.sh` | `orchestration/commands/collect-acceptance.sh` |
| `plan.sh` | `orchestration/commands/plan.sh` |
| `promote-acceptance.sh` | `orchestration/commands/promote-acceptance.sh` |
| `script.py` | `orchestration/commands/script.py` |
| `script.sh` | `orchestration/commands/script.sh` |
| `recovery-history.py` | `recovery-and-replacement/recovery-state/recovery-history.py` |
| `recovery-state.py` | `recovery-and-replacement/recovery-state/recovery-state.py` |
| `recovery-steps.py` | `recovery-and-replacement/recovery-state/recovery-steps.py` |
| `replacement-route.py` | `recovery-and-replacement/replacement/replacement-route.py` |
| `replacement.sh` | `recovery-and-replacement/replacement/replacement.sh` |
| `restart-route-test.py` | `recovery-and-replacement/restart/restart-route-test.py` |
| `restart-route.py` | `recovery-and-replacement/restart/restart-route.py` |
| `restart.sh` | `recovery-and-replacement/restart/restart.sh` |
| `restore-binding.py` | `recovery-and-replacement/restore/restore-binding.py` |
| `restore-control-test.py` | `recovery-and-replacement/restore/restore-control-test.py` |
| `restore-control.py` | `recovery-and-replacement/restore/restore-control.py` |
| `restore-reader-route.py` | `recovery-and-replacement/restore/restore-reader-route.py` |
| `restore-reader.sh` | `recovery-and-replacement/restore/restore-reader.sh` |
| `restore-route-test.py` | `recovery-and-replacement/restore/restore-route-test.py` |
| `restore-route.py` | `recovery-and-replacement/restore/restore-route.py` |
| `restore.sh` | `recovery-and-replacement/restore/restore.sh` |
| `snapshot-route.py` | `recovery-and-replacement/snapshot/snapshot-route.py` |
| `snapshot.sh` | `recovery-and-replacement/snapshot/snapshot.sh` |
| `source-transition-test.py` | `recovery-and-replacement/source-transition/source-transition-test.py` |
| `source-transition.py` | `recovery-and-replacement/source-transition/source-transition.py` |
| `task-binding.py` | `task-execution/implementation/task-binding.py` |
| `task-completion.py` | `task-execution/implementation/task-completion.py` |
| `task-control.py` | `task-execution/implementation/task-control.py` |
| `task-evidence.py` | `task-execution/implementation/task-evidence.py` |
| `task-graph.py` | `task-execution/implementation/task-graph.py` |
| `task-route.py` | `task-execution/implementation/task-route.py` |
| `task-runner.py` | `task-execution/implementation/task-runner.py` |
| `task-steps.py` | `task-execution/implementation/task-steps.py` |
| `task-binding-test.py` | `task-execution/tests/task-binding-test.py` |
| `task-control-test.py` | `task-execution/tests/task-control-test.py` |
| `task-evidence-test.py` | `task-execution/tests/task-evidence-test.py` |
| `task-route-test.py` | `task-execution/tests/task-route-test.py` |
| `task-runner-test.py` | `task-execution/tests/task-runner-test.py` |
| `task-execute.sh` | `task-execution/commands/task-execute.sh` |
| `task-plan.sh` | `task-execution/commands/task-plan.sh` |

## Reference census — 2026-11-22

The exact-string census covered all 76 source paths above.  Every path has at
least one reference; it found 547 literal reference lines in 59 consumers:

| Bucket | Reference lines | Consumer files | Required handling |
| --- | ---: | ---: | --- |
| Script | 232 | 45 | Update imports, shell invocations, test loaders, route bindings, the check selector and diagnostic-review inputs in the same slice. |
| Workflow | 236 | 4 | Update active deploy instructions.  The three dormant RAG generated-reference lines are retained and must not be regenerated. |
| Other | 79 | 10 | Update active infra and documentation callers; preserve accepted proof-receipt source fields as historical evidence. |

The existing governed planner was run for
`acceptance-aggregate-test.py`.  It found five exact references: three in the
dormant generated RAG artifact and two in diagnostic-review inputs.  It took
28 seconds because it scans the full generated RAG corpus.  Before each move,
run the same planner for that exact old/new pair and record the result in the
implementation record; this preparation census is not a substitute for that
gate.

The historically retained proof receipts name eight moved files:
`failure-route.py`, `replacement-route.py`, `restart-route.py`,
`restore-reader-route.py`, `restore-route.py`, `snapshot-route.py`,
`source-transition.py`, and `task-route.py` (with several repeated across the
two receipts).  Those immutable evidence records are not current execution
callers.

## Compatibility and execution prerequisites

The intended old-path disposition is **retired after active consumers move**.
No wrapper is desired: retaining dozens of executable compatibility files in
the scope root would defeat the topology change.

Two existing checker classifications are insufficient for that disposition:

1. The artifact-path checker treats only `commitLogs/` and explicit RAG
   retirement records as historical.  It currently sees accepted proof receipts
   as active `other` references even though they are immutable historical
   evidence.
2. The checker also sees the dormant generated RAG recognition corpus as active
   workflow content.  Refreshing that corpus would violate its dormant boundary;
   using `--allow-active-old-path` for all files would hide real missed callers.

The reusable artifact-path migration control now classifies only immutable
accepted-release proof-receipt JSON and declared dormant generated RAG
recognition separately from active consumers.  Its regression proves that both
an active current-release pointer and an ordinary active script still fail.
That correction is complete; the implementation slice must use the checker
without a blanket active-path allowance.

## Migration-checker prerequisite — completed 2026-11-22

`scripts/01.harness/check-artifact-path-migration.sh` now recognizes the two
historical locations described above.  The focused smoke test proves the
exemptions are narrow and cannot conceal either an active release pointer or an
ordinary script consumer.  This is process control only: no deployment runtime
predicate, diagnostic identifier, provider contract, or accepted record changed.

The real-repository negative check for `failure-route.py` remains blocked by
seven active reference locations.  Its failure output excludes both the
accepted proof-receipt JSON and dormant RAG generated corpus, confirming that
the new classifications remove only the intended historical records.

## Consumer inventory and proof

The move affects relative Python imports, shell wrappers, `importlib` path
loading, workflow guidance, target declarations, image/payload source lists,
the delivery-control inventory, check-selection registration and diagnostic
review source lists.  It must preserve command arguments, exit statuses,
diagnostic identifiers, receipt schemas and live-operation boundaries.

<!-- deterministic-check: allow reason="This migration checklist requires human review of active consumer paths; existing planners, validators, and test runners own its deterministic steps." -->
For each moved group, the implementing slice must:

1. run the exact old/new path planner and update active consumer paths;
2. run the artifact-path checker with this plan, without a blanket active-path
   allowance;
3. run the group’s existing focused tests plus the delivery-control inventory;
4. verify the operation’s command wrapper reaches the relocated module; and
5. run the registered package and run-route checks only after all affected
   inputs are stable.

Recovery is an inverse, reviewed patch restoring the prior paths and their
callers together.  Never reset the worktree, rewrite accepted evidence, or
rerun a live operation as a path-migration recovery.

## ADR disposition

No ADR is required for this internal script topology change if command and
provider contracts remain unchanged.  Reconsider that decision if the future
harness prerequisite changes public compatibility promises or lifecycle
authority.


## P4 whole-deployment isolation proposal — 2026-11-25

### P6 first execution packet — 2026-11-25

The user approved P6 after the P5 local-handoff briefing. Preserve all pending
P4/P5 changes in the recorded November 21 worktree. This first bounded group
reconciles the placement owner with the approved operation/role and retained
system forms, then relocates the two audited shared import-inspection files.
These are cross-layer prerequisites of this existing script-library migration,
not a second programme or a new shared execution engine. Their semantic owner
remains shared architecture inspection; build declarations stay in workspace-build.

| Old path | Canonical path | Disposition |
| --- | --- | --- |
| scripts/repo/workspace-build/dependencies.mjs | scripts/repo/module-structure/dependencies.mjs | Retired internal path after callers move; no wrapper. |
| scripts/repo/workspace-build/dependencies-test.mjs | scripts/repo/module-structure/dependencies-test.mjs | Retired internal test path after wrapper moves; no wrapper. |

Both old paths exist and both destinations are absent. Run the existing exact
per-path planner before changing references. Consumers: check.mjs import,
module-structure smoke wrapper/README, catalogue proof/selection inputs,
repository-contract expectations, source-matched diagnostic review and existing
helper audit/catalogue references. Fix the moved files' declarations import to
../workspace-build/declarations.mjs; no fixed-root depths, provider authority,
runtime source enumeration or historical release reader depends on these files.
Keep artifact IDs stable and preserve inspection bodies/cases. Current helper
indexes follow canonical paths; pinned audit observations remain observations
of their original source snapshot, not fresh execution proof. Migration evidence
retains old full paths here; immutable session/dormant generated history stays.

Named risks/proof: misplaced new paths or traversal (existing artifact-placement
regression); missing relocated import, lost findings/cases and runner dispatch
(existing module-index-structure-regression); dangling active old callers
(existing migration checker, --plan this file, no active-path allowance);
catalogue invalidation/ordinary selection (existing repository contract tests).
The broad real-source scan remains hygiene/manual and is not selected merely
because its regression files move. Review the full diff and record actual
results. Five-minute focused batch budget; do not repeat P5's unchanged package
proof or run providers. Metadata and whitespace complete the bounded packet.

Recovery: reviewed inverse path/reference patch only. No deletion of code,
reset, commit/merge/push, cloud operation, schedule change or subsequent P6 group
is authorised by this packet. Brief and stop after this group; P6 as a whole
is not complete while the approved deployment families remain unmoved.

Planner evidence: /tmp/script-p6-path-plans.MuSVIP contains both exact reports.
The inspector has 18 literal references, its test 14; each includes three in
dormant generated RAG recognition. New destinations had zero references.
Literal planning misses relative imports/README links; those were separately
read and repaired. The existing checker now supplies the no-active-old-caller
decision, not a renamed filename or a heuristic catalogue label.

Pre-proof self-review: all 173 approved deploy source destinations pass the
existing shape function (76 operation + 97 retained). Only the two shared
inspection artifacts moved. One existing downstream input needed explicit
preservation: core-runtime imported check.mjs, whose inspector previously lived
under its workspace-build input. Both proof invalidation and selection now name
the moved implementation; moving a test does not turn it into runtime input.
Existing repository assertions cover those bindings. Three existing diagnostic
review owners have fresh hashes and unchanged adoption/debt classifications.
No new source program, diagnostic schema, scheduler or blanket path allowance.
Freeze executable/config/review inputs now; final registered proof requests
artifact-placement-regression, module-index-structure-regression and
check-selection-repository-contracts. Full affected integration remains pending.

First final batch: placement passed in 1.932746s and relocated module fixtures
passed in 2.381498s. Existing retained repository-contract owner failed after
456.367583s; total 475.761009s misses the five-minute budget. Report:
.cache/test-runs/20261125T103006Z-374d4115eed44a5abdb25ae28ebb1d60/report.json.
That owner's failure detail is unsupported-format/unavailable, so no failing
method name survives in the retained report. Do not call that a pass.

Exploratory supported historical runner isolated the three affected existing
methods. Two revealed pre-existing mismatches confirmed against HEAD: the test
expected cadence deferred while the catalogue already says hygiene, and it
required manual scan invalidators to be automatic repository selection rules.
Correct only those expectations: keep the scan hygiene, assert its declared
input invalidation, and assert automatic fixture selection separately. Keep
actual source/data assertions, Core consumer binding and private input-change
counterexamples. All three methods then passed in 1.105s. No scheduling or
source-inspection rule was disabled or relaxed to obtain that result.

Final retry uses the unchanged registered catalogue argv directly:
bash scripts/repo/check-selection/smoke-test.sh --unit repository-contracts.
This exposes existing unittest progress without changing its runner or adding
a diagnostic framework. Preserve both previous passes; do not re-execute them.
Direct output is not imported into the private cache. Keep all inputs stable
during the retry and report its terminal outcome separately from the budget.

Retry terminal outcome: FAILED, 49 methods in 461.391s, 462s command wall time;
eleven failure records across eight methods. The three changed relocation
methods pass. Preserve the first batch's two independent successful owners.
No third broad retry. The current programme's P6 hold-point table names every
remaining method and investigation; normal candidate policy was not rewritten.
Confirmed the 15 context flags and relevant aggregate/diagnostic declarations
are unchanged from HEAD. This group is implemented with focused proof, not a
green full retained suite or complete P6/integration. Stop for user review;
recommend a separately approved repair of the shared context anchor first.

This extends the existing plan, not a second registry. Source head 1ed9157c;
full semantic review baseline 33f479b1. All 76 Entity direct-file pairs above
remain exact (E01). The user approved the P4 layout/scope after the complete
folder briefing; placement-standard reconciliation still precedes P6 movement.
No source had moved at the P4 snapshot. The P6 first packet above records the
two current shared-owner relocations; no deployment family has moved.

The [current audit](../../../../scripts/helpers/audit.md#p4-current-disposition-and-proposed-folder-manifest--2026-11-25)
contains the source digest, all 690 dispositions, complete 471-source deploy
leaf counts, consumers, proof and invalidating inputs. Proposed relocation:
173 source files and 31 Markdown companions; retain 517 sources in place;
delete none. No scheduler, broad verification gate or cloud work is added.

### P6 next-packet review — selector input projection, not yet implemented

Reviewed the next prelisted shared-owner pair in the November 21 worktree:

| Current path | Proposed canonical path |
| --- | --- |
| scripts/repo/workspace-build/check-inputs.mjs | scripts/repo/check-selection/check-inputs.mjs |
| scripts/repo/workspace-build/check-inputs-test.mjs | scripts/repo/check-selection/check-inputs-test.mjs |

Both source files are clean relative to HEAD. Destinations are absent. Exact
existing planner reports: /tmp/script-p6-projection-helper.xaNVvu (15 literal
references) and /tmp/script-p6-projection-test.LHXEJr (10). Each includes three
dormant generated RAG references, which stay unchanged. Active helper catalogue,
audit, source-review and timeout-inventory pointers must follow the canonical
path while retaining their original snapshot/provenance, not claiming a rerun.
Old full paths remain migration evidence only here; no compatibility copy is
proposed after active callers move. No move or active reference edit occurred.

Actual ownership and nonliteral callers:

- workspace_context.py PROJECTOR invokes the helper using the selected root
  as working directory. Its result contributes actual command/compiler source,
  manifest and installation inputs to selector proof identities. Preserve JSON
  shapes, finite failures, npm hook semantics and changes that invalidate proof.
- The helper imports declarations.mjs, script.mjs and compile.mjs relatively.
  Those compiler owners stay in workspace-build; adjust only the three import
  paths. Test import and new URL remain sibling-relative, so move both together.
- mechanics_test.py workspace_context_fixture copies the old compiler folder
  into a temporary repository. It must additionally copy the moved helper to
  PROJECTOR; otherwise apparently unrelated Python fixture cases lose it.
- prepare-runtime-payload/script.sh currently runs the seven selector-helper
  tests beside compiler and packaging tests. A simple path substitution would
  preserve the cross-role verification coupling; it is not the final ownership
  decision. Keep the five actual compiler tests and packaging tests intact.
- Three existing source-review owners name the test: workspace-check-input-projection
  (partial), shared-runtime-payload-test-dispatch (support), and
  runner-core-verification-enforcement (partial). Preserve their remaining debt;
  reconcile proof references as well as hashes if ownership changes.

Desired execution-owner decision: a focused selector route for these seven
existing cases, removing only their invocation from packaging. Do not attach
them to full deferred mechanics or every package build. The initially considered
addition to check-selection/smoke-test.sh is NOT ready to implement: the actual
selection preview below establishes a fan-out prerequisite. Catalogue entries
require bash; a direct Node entry would change an unrelated runner contract.
A new shell launcher would duplicate an existing role. Neither alternative is
approved. No new source, test case, engine or parallel registry is proposed.

Known cost risk: the shared dispatcher is a command owner for 37 catalogue
checks and appears in exact repository-input mappings to 34 identities.
These are declared links, NOT 34 observed executions. The existing selector was
then run with --paths scripts/repo/check-selection/smoke-test.sh --json,
without execution. Report /tmp/script-p6-projection-dispatch-impact.cmh2t7:
planned, zero findings, 31.221361s, 33 candidate-local pending checks and one
deferred repository-contract suite; zero commands executed. Thus editing the
shared dispatcher genuinely broadens normal selection. No blind batch ran.

Prerequisite recommendation, requiring separate approval: existing branches
mostly delegate to already-existing standalone owner scripts. Point those
catalogue entries directly at the same scripts, preserving stable check IDs,
effects, scheduling, dependencies and original outcomes. Remove a dispatcher
input/trigger only after confirming that the actual command and its consumers
no longer use it; keep any real indirect dependency. Do not blanket-delete all
shared dependencies, weaken checks or build another dispatcher/branch parser.
Start with harness-header-regression and harness-lifecycle-metadata-regression:
their literal dispatcher branches already exec the respective existing
artifact-metadata check-headers and update-lifecycle smoke-test.sh scripts.
Then re-preview actual selection before extending this correction. Shared
dispatcher compatibility remains; its file need not change for this pilot.
This addresses coupling before the helper move, not a justification to waive
the 33 selected checks. No routing correction is implemented in this review.

Baseline proof: existing node --test command passes all seven cases in
7.506295s. A direct Node invocation also passes seven in 3.687334s, but is not
a permitted catalogue command shape; it is not a reason to change the runner.
Both outcomes are local synthetic proof, not package/deployment acceptance.
After the routing prerequisite is approved and proved, migration checker after
the move, the seven cases, existing affected Python
workspace-context cases, source-review/header checks and impact preview are the
proposed proof. Full mechanics/repository suites and providers are not part of
this review. Five-minute focused execution budget; report any overrun honestly.

Review checkpoint: source count remains 690 and no files moved. User approval
is required first for the bounded catalogue-to-owner routing pilot, then for the
helper/test ownership move. Recovery would be a reviewed inverse patch, never
a worktree reset or rewrite of accepted evidence. No commit/merge/push authority.

#### Metadata routing pilot — approved, partially delivered

User approved the two metadata routes. Actual pre-edit validation exposed an
omitted prerequisite: direct lifecycle declares stages-files/commits, which
the local guard rejects. Its test Git work is temporary, but current permission
classification does not distinguish that scope. Header also uses temporary Git
but has only writes-files metadata. Do not remove truthful declarations or
loosen LOCAL_EFFECTS to force this pilot through; obtain the owning harness
decision before direct lifecycle registration. Its old registered wrapper stays.

Only header is now direct: same stable check, existing test script/metadata
owner, writes-files declaration, all real inputs/runtime/scheduling retained.
Only its two dispatcher edges are removed. No wrapper or test implementation
changed. Header passed as a registered local command in 24.020669s; the request
also reused unchanged lifecycle proof, total 29.004423s, no findings.
Report: .cache/test-runs/20261125T173812Z-2f5aa5a4fd7c45cf81caf8569868a2ef/report.json.
The existing component/owner contract passed in 0.408s.

Actual no-execution previews confirm header is absent for dispatcher changes
(32 pending candidate-local checks, down from 33, plus one deferred suite),
and present for its own test path. Both have zero findings; safe reports are
/tmp/script-p6-metadata-pilot-impact.S9oTmH and
/tmp/script-p6-metadata-owner-impact.xzgFbz. This removes one false dependency,
not all runner coupling. No time-saving claim for a full release is established.
No helper/test path moved; the two-route pilot and P6 are still incomplete.
The implementation programme owns the effects decision. The user subsequently
approved its correction; both pilot routes are now direct as recorded below.

#### Metadata routing prerequisite — completed locally after scope correction

Canonical metadata standard now distinguishes contained private fixture Git
state from existing task/integration Git state. The existing lifecycle test
helper rejects external/escaped working directories and .git pointers, clears
inherited Git redirection and host configuration, bounds discovery, and preserves
explicit fixture dates. Its original lifecycle assertions remain. This is
source-reviewed fixture containment, not a new process sandbox or global bypass.
The central local effect guard and shared dispatcher are unchanged.

Lifecycle now directly names its existing test script/owner with writes-files,
and only its obsolete dispatcher input/trigger edges are removed. Both metadata
routes pass the registered request: lifecycle executes in 17.019666s, unchanged
header proof is reused; total 22.838635s, no findings. Report:
.cache/test-runs/20261125T174843Z-6a9c9013a5de465aaa1c6cbacedea178/report.json.
Three existing component/effect/stage cases pass; bounded probes reject actual
helper symlink escapes and declared real Git actions before spawn. Real HEAD,
branch and index bytes remain unchanged around verification.

Actual dispatcher-change preview now has 31 candidate-local pending checks,
one deferred suite, neither metadata route and zero findings/execution. Own
lifecycle test still selects its route. Reports and exact scope are recorded
in the programme. This completes the two-route pilot, not all runner coupling
or P6. No helper source path has moved. Return to the next packet only after
the user's bounded implementation approval; do not silently convert all routes.

#### Next routing prerequisite — reviewed, then delivered locally

The programme now records source review of three direct-owner candidates:
process-drift, bootstrap-audit and migration-audit regression fixtures. Their
existing commands validate with unchanged writes-files permissions; no source
move or catalogue edit was made. The proposed bounded correction includes the
existing catalogue contract assertion that currently requires wrapper routing.
Retain operational commands, compatibility branches and all real dependencies.
Obtain approval for that increment before implementation; helper relocation
remains blocked on the recorded execution-ownership prerequisite, not approved
merely by this review. Exact owners and proving commands are in the programme.

The user subsequently approved the three-route correction. Existing direct
owners and the reconciled catalogue-contract case pass; registered execution
takes 8.189545s. Launcher-only selection drops from 31 to 28 pending checks,
while all three remain selected by their own checker-source changes. No source
path moved; compatibility branches, runtime effects and timing stay unchanged.
See the programme for reports, counterexamples and retained integration debt.

The next reviewed prerequisite is the summary/upstream three-test routing batch
in the programme. Existing standalone commands validate without effect changes;
no catalogue edit or source move is implemented by that review. Maintenance and
conflict-classification fixtures are explicitly excluded because their real Git
operations need separate containment decisions. The programme owns exact scope,
approval and proof; the helper relocation remains pending.

The user then approved that batch. All three direct registered tests pass in
14.515545s; launcher-only selection is 26 pending (was 28), not 25. The contract
test remains selected through existing metadata links to its copied commit-
preparation input. Preserve that obligation pending separate declaration review;
do not remove the real input or weaken the selector to force the expected count.
The programme records exact evidence, files and unchanged integration debt.

The remaining indirect selection has now been reviewed at its source. The
programme proposes correcting the launcher's metadata registration/caller links,
not deleting the upstream test's real copied input or changing selection code.
Its in-memory preview removes only that indirect check; implementation awaits
approval. Current real launcher-only selection is still 26 pending plus one
deferred; the proposed 25 is not an implemented result.

The user approved the launcher ownership correction. Its header now names the
catalogue and actual Python caller; all executable branches and selector code
stay unchanged. Existing focused cases pass; actual launcher-only selection is
25 pending plus one deferred. Real preparation changes still select upstream-
contract, whose unchanged proof is reused. The programme owns exact reports.
This closes the single indirect-link correction, not remaining dispatcher
coupling, helper movement or complete P6/integration acceptance.

### Exact isolation pairs

Paths are relative to `scripts/04.deploy/`. Each directory carries its
source/test/README companions without changing public command semantics.
All unlisted paths remain unchanged; no filename-based glob is a move authority.

| Packet | Current path | Proposed path | Source files |
| --- | --- | --- | ---: |
| S01 | `assess-platform-shell-artifact-drift/` | `legacy/kanbien-staging/assess-platform-shell-artifact-drift/` | 3 |
| S02 | `assess-platform-shell-foundation-drift/` | `legacy/kanbien-staging/assess-platform-shell-foundation-drift/` | 3 |
| S03 | `assess-platform-shell-service-drift/` | `legacy/kanbien-staging/assess-platform-shell-service-drift/` | 3 |
| S04 | `build-platform-shell-image/` | `legacy/kanbien-staging/build-platform-shell-image/` | 7 |
| S05 | `provision-platform-shell-negative-authz-client/` | `legacy/kanbien-staging/provision-platform-shell-negative-authz-client/` | 3 |
| S06 | `provision-platform-shell-persistence-write-client/` | `legacy/kanbien-staging/provision-platform-shell-persistence-write-client/` | 3 |
| S07 | `reconcile-platform-shell-staging/` | `legacy/kanbien-staging/reconcile-platform-shell-staging/` | 5 |
| S08 | `render-platform-shell-foundation-template/` | `legacy/kanbien-staging/render-platform-shell-foundation-template/` | 1 |
| S09 | `run-platform-shell-candidate-execution-preflight/` | `legacy/kanbien-staging/run-platform-shell-candidate-execution-preflight/` | 4 |
| S10 | `run-platform-shell-controlled-smoke/` | `legacy/kanbien-staging/run-platform-shell-controlled-smoke/` | 3 |
| S11 | `run-platform-shell-ingress-smoke/` | `legacy/kanbien-staging/run-platform-shell-ingress-smoke/` | 3 |
| S12 | `run-platform-shell-metric-coverage/` | `legacy/kanbien-staging/run-platform-shell-metric-coverage/` | 4 |
| S13 | `run-platform-shell-negative-authz-smoke/` | `legacy/kanbien-staging/run-platform-shell-negative-authz-smoke/` | 3 |
| S14 | `run-platform-shell-persistence-admission-probe/` | `legacy/kanbien-staging/run-platform-shell-persistence-admission-probe/` | 3 |
| S15 | `run-platform-shell-persistence-delivery-proof/` | `legacy/kanbien-staging/run-platform-shell-persistence-delivery-proof/` | 4 |
| S16 | `run-platform-shell-persistence-smoke/` | `legacy/kanbien-staging/run-platform-shell-persistence-smoke/` | 3 |
| S17 | `run-platform-shell-postgresql-relational-smoke/` | `legacy/kanbien-staging/run-platform-shell-postgresql-relational-smoke/` | 4 |
| S18 | `run-platform-shell-rate-limit-smoke/` | `legacy/kanbien-staging/run-platform-shell-rate-limit-smoke/` | 3 |
| S19 | `run-platform-shell-worker-smoke/` | `legacy/kanbien-staging/run-platform-shell-worker-smoke/` | 4 |
| S20 | `smoke-test-platform-shell-image/` | `legacy/kanbien-staging/smoke-test-platform-shell-image/` | 2 |
| S21 | `verify-platform-shell-deploy-readiness/` | `legacy/kanbien-staging/verify-platform-shell-deploy-readiness/` | 4 |
| S22 | `verify-platform-shell-deployment-artifact-store/` | `legacy/kanbien-staging/verify-platform-shell-deployment-artifact-store/` | 2 |
| S23 | `verify-platform-shell-deployment-reconciliation/` | `legacy/kanbien-staging/verify-platform-shell-deployment-reconciliation/` | 2 |
| S24 | `verify-platform-shell-deployment-workflow/` | `legacy/kanbien-staging/verify-platform-shell-deployment-workflow/` | 3 |
| S25 | `verify-platform-shell-drift-detection-boundary/` | `legacy/kanbien-staging/verify-platform-shell-drift-detection-boundary/` | 3 |
| S26 | `verify-platform-shell-infrastructure/` | `legacy/kanbien-staging/verify-platform-shell-infrastructure/` | 2 |
| S27 | `verify-platform-shell-metric-coverage/` | `legacy/kanbien-staging/verify-platform-shell-metric-coverage/` | 2 |
| S28 | `verify-platform-shell-observability-prerequisites/` | `legacy/kanbien-staging/verify-platform-shell-observability-prerequisites/` | 1 |
| S29 | `verify-platform-shell-postgresql-live-boundary/` | `legacy/kanbien-staging/verify-platform-shell-postgresql-live-boundary/` | 3 |
| S30 | `verify-platform-shell-postgresql-reference/` | `legacy/kanbien-staging/verify-platform-shell-postgresql-reference/` | 2 |
| S31 | `verify-platform-shell-synthetic-scheduler/` | `legacy/kanbien-staging/verify-platform-shell-synthetic-scheduler/` | 2 |
| S32 | `shared/provider-adapters/aws/cognito-provisioning.py` | `legacy/kanbien-staging/shared/provider-adapters/aws/cognito-provisioning.py` | 1 |
| R01 | `verify-rag-rulebook-deploy-readiness/` | `legacy/rag-rulebook/verify-rag-rulebook-deploy-readiness/` | 2 |

S01–S31 = 94 sources; S32 makes staging 95; R01 = 2; E01 = 76.
Keep shared root inventory-deploy-control (6), operational-realization-gate (5)
and validate-container-boundaries (2). Moving them only to hide three roots
adds compatibility work without removing mixed responsibilities. Retain the
69 RAG-layer sources in their already separate scripts/02.rag-rulebook home.

### Migration prerequisites, not new ordinary gates

1. Use the recorded P4 destination/scope approval. P6's first group reconciles
   the existing placement owner and bounded fixtures with legacy and E01's
   operation/role forms, without per-file exceptions. That shape prerequisite
   is delivered; it does not waive the remaining per-packet checks below.
2. Refresh each packet's real import/config/workflow/metadata closure. Run the
   existing per-path planner when destinations are approved; P4 has not executed
   173 expensive planner calls or claimed migration-checker success.
3. Preserve npm aliases and documented arguments/results. Proposed old internal
   path disposition is retired-after-consumers-move, subject to each packet's
   compatibility review. If concrete direct-path consumers require compatibility,
   stop for that decision; do not pre-create dozens of wrappers. Preserve
   immutable receipt/source path history byte-for-byte.
4. Consume the audit's hold-point matrix: mixed Cognito/provider and package
   proof, active staging transactions versus historical modes, source-byte
   recovery allowlists, original reservation/controller/template hashes, Entity
   historical readers and embedded retained-RAG source lists. Literal references
   and topology remove labels do not establish migration closure.
5. Update registrations/reviews and actual rooted fixtures with the moved owner.
   Use its existing focused proof plus physical delivery census. Package/live
   proof is due at its actual affected stage, not by default for every move.
6. Use the existing path checker without a blanket old-path allowance. Older
   audit/plan references outside its narrow historical classes require explicit
   owning disposition. Recovery is an inverse reviewed patch restoring paths
   and callers together, never reset, history rewrite or cloud-operation replay.

GitHub workflows stay at their required root and keep current schedules and
authority. Staging remains retained and scheduled, not operationally dormant.
RAG's existing false-guarded hosted job stays disabled. Physical moves alone
are not a claim that verification coupling is solved.

### Autonomous implementation checkpoint — 2026-11-26

The user's autonomous P6/P7 goal supersedes the earlier per-increment approval
pauses above; those paragraphs remain the dated decision trail, not current
blocking instructions. The exact manifest remains authoritative.

All E01/S01–S32/R01 moves are implemented locally: 173 source files and 31
Markdown companions, with current imports, declarations, aliases and workflow
references following their destination. The four repository helper source/test
moves are also implemented. No compatibility controller copies were added.

Existing historical Entity release source digest is unchanged at the recorded
starting revision; current nested source discovery and bounded alignment moves
have focused proof. All 76 Entity path checks pass. All 28 available legacy
local owner commands pass and delivery inventory covers 521 entrypoints in six
scopes with no gaps. Eight remaining legacy path-check failures concern exact
frozen historical references; these eight now pass with exact provenance-aware
classification that still rejects current commands and links. The separate
dated timeout-inventory TSV retains its original historical snapshot bytes.

The independent historical-reader review also corrected graph fingerprints
through a finite old/new entrypoint mapping, without executable aliases or
weakened plan, journal, gate or permission checks. Fourteen old/current graph
forms pass and all 90 accepted/proof records are unchanged. Final selection must
also account for actual Git rename ownership before candidate acceptance.

Caller review, lifecycle preparation and source-bound review reconciliation are
complete. The corrected registered candidate passed 133 entries (105 reused),
with 28 later/manual-stage deferrals and no findings, in 1177.492 seconds.
The programme records its report and the final protected-RAG correction: exact
original recognition bytes remain frozen; existing runtime fixtures use
disposable source copies, and R01 directly proves its moved current references.
No search-corpus refresh is a deployment-migration requirement. Final integrated
qualification, coherent commits, refresh and actual main publication are tracked
in the existing script-library-simplification programme.
