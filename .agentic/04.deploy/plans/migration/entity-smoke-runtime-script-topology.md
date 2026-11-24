<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.migration.entity-smoke-runtime-script-topology
version: 1
status: draft
created_on: "2026-11-22"
updated_on: "2026-11-22"
layer: 04.deploy
domain: migration
disciplines: [architecture, sre, agentic]
kind: migration-plan
purpose: Move the active entity-smoke runtime scripts from one flat scope root into focused operational folders without changing deployed behaviour, accepted evidence, or provider authority.
portability: {class: source-only, targets: []}
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
- id: deploy.standards.lifecycle-stage-ownership
  path: .agentic/04.deploy/standards/lifecycle-stage-ownership.md
-->
# Entity-smoke runtime script topology migration

## Decision and scope

The active `60-run` entity-smoke route currently has 76 executable files at
one scope root.  Preserve the scope identity and its existing `bindings/`
tree, but move those direct files to focused operational folders.  A folder
states the objective; `implementation/`, `tests/`, and `commands/` distinguish
supporting roles where that improves reviewability.

This plan is preparation only.  It does not move a script, invoke AWS or
GitHub, alter a release, rewrite an accepted record, or activate dormant RAG
machinery.  The existing direct paths remain canonical until this plan's
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
