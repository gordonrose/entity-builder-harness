<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.inventory.core-platform-deployment-routes
version: 1
status: draft
created_on: "2026-11-14"
updated_on: "2026-11-15"
layer: 04.deploy
domain: deployment.consolidation
disciplines: [architecture, sre, security]
kind: inventory
purpose: Record source-backed reuse, overlap, workload differences and migration candidates for the two accepted core-platform deployment routes.
portability: {class: source-only, targets: []}
used_by:
- id: deploy.plan.consolidate-core-platform-deployment-routes
  path: .agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md
-->
# Core platform deployment route inventory

## Findings and recommended starting point

The repository does not contain two wholly independent deployment systems.
It contains shared foundations plus two substantial, separately specialised
release controllers. The avoidable overlap is real, but deleting either route
wholesale would lose behaviour and break accepted-evidence readers.

Start by consolidating **runtime payload assembly**: both image builders
independently validate compiled exports and write package shims, manifests and
entrypoint wrappers. This is a complete local operation with two real consumers
and no AWS effects. Preserve each workload's entrypoints and diagnostic
behaviour. Then consolidate provider/task handling, deployment, recovery and
acceptance in that order.

The [consolidation plan](../../../.agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md)
owns the sequence and completion criteria. This inventory records findings,
not permission to remove files or evidence that consolidation has happened.

## Source boundary and method

- Inspected on 2026-11-14 at commit
  `eecf0c50178ef004f62792aef2835023e492a470` on
  `chat/2026-11-06-17-07-new-chat-session`.
- Worktree: `/home/owner/projects/.chat-worktrees/entity-builder-harness-restart-3842312794/chat_2026-11-06-17-07-new-chat-session-1937001871`.
- Existing untracked lesson plan
  `docs/education/lesson-plans/0002-entity-smoke-release-retrospective.md`
  was preserved. Deployment source matched the checkpoint.
- Enumerated tracked lifecycle paths for both names; read representative
  implementation bodies, imports, declarations, builders, callers and tests.
  The findings below distinguish confirmed overlap from proposed extraction.
  This is not a line-by-line correctness review of every enumerated file.
- No AWS calls, deployments, image builds or regression suites were run for
  this inventory. Source structure cannot establish current live health or
  compatibility of a future refactor.

### Measured lifecycle footprint

Counted tracked files beneath `scripts/04.deploy/lifecycle/` whose path contains
`core-server-persistence` or `entity-smoke`, excluding the separately named
`core-server-persistence-observability-collector` package route. Counts include
tests, fixtures, wrappers, comments and READMEs; lines mean physical text lines,
not executable statements or removable duplication.

| Phase | Persistence files | Persistence lines | Feature files | Feature lines |
| --- | ---: | ---: | ---: | ---: |
| Target alignment | 0 | 0 | 4 | 715 |
| Build and composition checks | 11 | 2,515 | 8 | 1,569 |
| Package | 14 | 1,361 | 16 | 1,722 |
| Deploy | 23 | 4,062 | 0 | 0 |
| Run, recovery and acceptance | 44 | 7,921 | 76 | 17,005 |
| Total | 92 | 15,859 | 104 | 21,011 |

Zeros describe file placement, not missing capabilities: persistence alignment
is inside `50-deploy/prepare-candidate`; feature infrastructure deployment is
inside its `60-run` directory. Shared scripts, app/platform code, infrastructure
templates, GitHub workflows and historical receipts are outside these counts
but are considered below. The five excluded collector-package files remain
outside the consolidation scope.

The feature's 76-file Run directory contains 53 non-test-named executable files
(9,317 lines), 22 test-named files (6,890 lines), and one README (798 lines).
This naming-based breakdown is not a claim that all 9,317 lines are redundant.
There are no byte-identical executable files in the counted set. Overlap is
primarily repeated responsibilities implemented differently, not exact copies.

Reproduce the path enumeration at the pinned checkpoint:

```bash
git ls-tree -r --name-only eecf0c50178ef004f62792aef2835023e492a470 scripts/04.deploy/lifecycle |
  rg 'entity-smoke|core-server-persistence' |
  rg -v 'core-server-persistence-observability-collector' |
  LC_ALL=C sort
```

The sorted, newline-terminated 196-path list has SHA-256
`a7ce89e4cc7596c83be4edb29fff1de8f38b3c3f962ac18079012021223eafeb`.
Read each file at that commit and count `splitlines()` to reproduce line totals.

## What is already shared

Keep these owners. Consolidation should call them, not replace them with a
third implementation.

| Shared owner | Observed reuse and boundary |
| --- | --- |
| [Declaration coverage](../../../scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py), [runnable program validation](../../../scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh) and [delivery inventory](../../../scripts/04.deploy/inventory-deploy-control/script.py) | Both packaging routes invoke existing checks. Workload declarations remain inputs. |
| [ECS configuration normalisation](../../../scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py) | The feature's `entity-smoke-runtime-configuration.py` delegates to it for two templates. Preserve that adapter rather than rewriting normalisation. |
| [Package qualification](../../../scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py), [receipt validation](../../../scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py) and [workflow guards](../../../scripts/04.deploy/lifecycle/40-package/package-custody-receipt/workflow_guard.py) | Both package routes reuse these. Their surrounding build/publication orchestration still differs. |
| [AWS response classification](../../../scripts/04.deploy/shared/provider-adapters/aws/response.py), [CloudFormation parser](../../../scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py), [ECR scanning](../../../scripts/04.deploy/shared/provider-adapters/aws/ecr-scan.py) | Existing provider helpers. AWS CLI invocation is still repeated in controllers. Feature template controls use the shared parser. |
| [Release succession](../../../scripts/04.deploy/lifecycle/60-run/release-succession/script.py), [acceptance route validation](../../../scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py), [scope promotion](../../../scripts/04.deploy/lifecycle/60-run/promote-accepted-scope/script.py) | Release identity/history machinery already exists; the feature promotion delegates to succession and scope promotion. Do not create another accepted-release ledger. |
| [Realization gate](../../../scripts/04.deploy/operational-realization-gate/script.py) | Feature infrastructure/task routes call the existing generic gate; this does not mean the old controller has identical gate wiring. Preserve the owner and compare call-site semantics. |
| [Safe command diagnostics](../../../scripts/04.deploy/shared/safe-command-diagnostics.sh), [operation diagnostics](../../../scripts/04.deploy/shared/deployment-operation-diagnostics.py), [disposable Docker cleanup](../../../scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py) | Existing reusable diagnostics and cleanup. Retain diagnostic ownership and no-replay behaviour. |
| [PostgreSQL adapter](../../../platform/adapters/aws/persistence/postgresql/src/index.ts) and [feature migration composition](../../../infra/04.deploy/03.product/entrypoints/entity-smoke/migrations.ts) | The feature already uses the platform connection pool and migration runner. There is not a second PostgreSQL engine to remove. |

## File level disposition map

Paths below use these existing roots to keep the comparison readable:

- **L** = [`scripts/04.deploy/lifecycle/`](../../../scripts/04.deploy/lifecycle/).
- **P50** = [`L/50-deploy/targets/kanbien-core-platform/core-server-persistence/`](../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/).
- **P60** = [`L/60-run/targets/kanbien-core-platform/core-server-persistence/`](../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/).
- **E60** = [`L/60-run/targets/kanbien-core-platform/entity-smoke/`](../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/).
- **T** = [`infra/04.deploy/03.product/targets/kanbien-core-platform/`](../../../infra/04.deploy/03.product/targets/kanbien-core-platform/).
- **I** = [`infra/04.deploy/03.product/`](../../../infra/04.deploy/03.product/).

“Consolidate” identifies common responsibility, not proven interchangeability.
“Remove after migration” is conditional on caller and compatibility proof.
No current executable has been certified unused by this inventory.

### Alignment, composition and packaging

| ID | Existing files | Finding and proposed disposition |
| --- | --- | --- |
| A01 | `P50/prepare-candidate/script.py`; `L/00-target-alignment/targets/kanbien-core-platform/entity-smoke/script.py` and their shell wrappers | **Consolidate and parameterise.** Both inspect selected foundation/package/dependency facts. Persistence pins stack, repository and expected package/program in constants; feature pins its own scope and adds image-delivery checks. Extract common observations while retaining each allowed resource binding and feature's endpoint-policy checks. |
| A02 | `L/00-target-alignment/provider-adapters/aws/entity-smoke-runtime-configuration.py`; shared `ecs-runtime-configuration.py` | **Keep existing reuse; later parameterise binding.** The feature adapter selects six workloads over main and restore templates, then delegates. It is not a duplicate ECS normaliser. |
| A03 | `L/20-build/core-server-persistence-composition/{build.sh,smoke-test.sh,postgresql-diagnostics-check.sh,postgresql-integration-check.sh}`; `L/20-build/entity-smoke-composition/smoke-test.sh`; both `I/entrypoints/kanbien-*.tsconfig.json` selections | **Keep workload assertions; consolidate assembly callers where appropriate.** Different runtime behaviour and observability coverage are legitimate. Do not erase tests merely because they use similar setup. |
| A04 | `L/40-package/build-core-server-persistence-image/{prepare-runtime.mjs,runtime-contract.mjs,verify-runtime.mjs}`; `L/40-package/build-entity-smoke-image/prepare-runtime.mjs` | **Confirmed duplicated responsibility; first consolidation slice.** Both validate compiled roots/exports and generate CommonJS shims, manifests and executable wrappers. Keep mappings and wrapper policies as explicit inputs. Feature adds JSON assets and dry-run support; baseline has a separate payload verifier. Neither is a drop-in replacement for the other. |
| A05 | `L/40-package/build-entity-smoke-image/prepare-dependencies.mjs`; `I/image/core-server-persistence/Dockerfile` dependency-copy commands | **Reuse candidate, not direct deletion.** Feature resolves a lock-bound dependency closure; baseline manually copies driver packages and broad SDK/telemetry trees. Later parameterise dependency roots to include baseline observability. Do not drop those dependencies while making its image smaller. |
| A06 | Both `L/40-package/build-*-image/script.sh` and `I/image/{core-server-persistence,entity-smoke}/{Dockerfile,Dockerfile.dockerignore,image-contract.yml}` | **Consolidate common build mechanics; retain package identity/content.** The builders share prechecks and Docker invocation but differ in committed-source enforcement, timeout, platform/provenance flags and checks. Changing this requires an explicit behaviour comparison, not choosing the shorter script. Dockerfiles must copy any extracted assembler. |
| A07 | `L/40-package/smoke-test-core-server-persistence-image/{script.sh,capability-negative-test.py,qualify-local-public-images.sh}`; `L/40-package/smoke-test-entity-smoke-image/{script.sh,verify-image.mjs,capability-negative-test.py}` | **Consolidate lifecycle setup later; keep proof assertions.** Both qualify a real disposable image/database, but feature fields/lifecycle and baseline observability are not interchangeable. Reuse the existing disposable-cleanup owner. |
| A08 | `L/40-package/targets/kanbien-core-platform/{core-server-persistence,entity-smoke}-package-custody/{script.sh,verify-workflow.py}`; feature `publication.py`; the two `.github/workflows/publish-kanbien-core-platform-*.yml` workflows | **Consolidate on existing custody helpers, retaining separate destinations.** The feature has durable publication reservation and recovery; baseline uses shared ECR publication command generation. Both validators also pin builder text. Common implementation must preserve failure ordering, immutable publication and authority; changing only workflow YAML will leave validators behind. |

### Deployment, tasks and recovery

| ID | Existing files | Finding and proposed disposition |
| --- | --- | --- |
| B01 | `P50/{create-change-set,deploy-candidate,transition-qualified-release}/script.py`; `E60/{script.py,deployment-control.py,plan.sh,script.sh}` | **Consolidate common change-set mechanics after task/provider seams.** Keep create, activation and successor update distinct operations with one engine. Feature creates a count-zero service and later activates; baseline creation/update has different parameters and predecessor rules. Its Deploy logic being under Run is placement debt, not a reason for a blanket move now. |
| B02 | `P60/{run-migration,run-administration,verify-candidate}/script.py`; `E60/{task-control.py,task-runner.py,task-route.py,task-binding.py,task-graph.py,task-completion.py,task-plan.sh,task-execute.sh}` | **Consolidate task execution around validated bindings.** Both launch/observe bounded ECS tasks. Feature has durable request reservation, original admission and completion sidecars; baseline has explicit reconciliation paths and proof receipts. Preserve the stronger necessary invariants, with both routes tested; do not weaken to the least common denominator. |
| B03 | `P60/ecs-task-evidence.py`; `E60/task-control.py::exact_task` | **Confirmed overlapping predicate.** Both reject unexpected overrides, allow only an empty optional inference-accelerator list, and compare one exact container/environment. Extract one parameterised provider response predicate. Keep feature task ARN/definition/operation checks around it; do not confuse this with sharing the entire task runner. |
| B04 | `P60/{run-migration,verify-candidate,collect-acceptance-evidence}/script.py` AWS functions; `P50/prepare-candidate/script.py`; `E60/script.py::Provider` | **Consolidate provider invocation.** They already share error classification but still repeat subprocess/timeouts/JSON boundaries. Keep call allowlists and effect admission in callers; a shared subprocess helper must not become unrestricted AWS authority. |
| B05 | `E60/{preflight-control.py,unready-control.py,task-steps.py,feature-steps.py,credential-steps.py,recovery-steps.py,acceptance-steps.py}`; baseline command sequencing in `T/20-scopes/core-server-persistence/00-declaration/acceptance-route-contract.yml` | **Separate common dependency ordering from workload proof requirements.** Feature's stage tables, real database-access preflight and expected-unready observation are not interchangeable with ordinary readiness. Use the existing route declarations rather than inventing a second scheduler. Feature-specific CRUD/lifecycle result assertions remain specific. |
| B06 | `P60/rehearse-server-replacement/script.py`; `E60/{replacement-route.py,replacement.sh,resource-control.py}` | **Consolidate original-task replacement and successor observation.** Never select the replacement task as another stop target after interruption. Same-record readback stays an independently required proof. |
| B07 | `P50/{retire-failed-candidate,transition-qualified-release}/script.py`; `E60/{failure-binding.py,failure-control.py,failure-route.py,failure-plan.sh,failure-stop.sh,restart-route.py,restart.sh,recovery-state.py}` | **Keep distinct recovery policies, share mechanics.** Initial stop/preserve/restart and rollback to an accepted predecessor solve different situations. A generic policy selector can choose between them; deleting either policy loses supported behaviour. |
| B08 | `P60/rehearse-runtime-credential-lifecycle/script.py`; `P60/run-administration/script.py`; `E60/{credential-steps.py,recovery-history.py,administrator-observation.js,administrator-recovery.js}` | **Consolidate ordering/observation; retain role-specific actions and evidence compatibility.** Deliberate revoke, unready observation, restoration and independent recovered read are common. The feature administrator repair path also contains incident-specific recovery, not just reusable credential handling. |
| B09 | `P60/create-recovery-point/script.py`; `E60/{snapshot-route.py,snapshot.sh,resource-control.py}` | **Consolidate snapshot ownership and reservation mechanics.** Source database and recovery-point identity remain workload/dependency inputs; never infer deletion authority from successful creation. |
| B10 | `P60/rehearse-isolated-database-restore/script.py`; `E60/{restore-control.py,restore-binding.py,restore-route.py,restore.sh,restore-reader-route.py,restore-reader.sh}` | **Consolidate restore/readback/cleanup orchestration later.** Feature uses a declared clone stack and exact original readback before owned cleanup. Preserve source DB/snapshot protections and readers for both receipt formats. Do not require a fresh restore merely to read accepted history. |
| B11 | `E60/{source-transition.py,image-delivery-repair.py}` and their imports in task/acceptance routes | **Separate incident compatibility from normal delivery; remove effectful repair paths only after migration.** `source-transition.py` embeds exact old source/image, task IDs, packet hashes and cache paths from this incident. These are not future-feature configuration. Historical validation still consumes this module, so deleting it now would break proof readers. Preserve the read-only compatibility needed for original evidence; retire launch/repair branches after callers migrate. |

### Acceptance, declarations and supporting consumers

| ID | Existing files | Finding and proposed disposition |
| --- | --- | --- |
| C01 | `P60/{proof-receipts.py,collect-acceptance-evidence/script.py,validate-accepted-release/script.py}`; `E60/{task-evidence.py,acceptance-evidence.py,acceptance-controls.py,acceptance-route.py,acceptance-state.py,acceptance-promote.py,control-completion.py}` and public acceptance shell wrappers | **Consolidate collection and state validation around existing succession; preserve typed readers.** Baseline uses persistence proof receipts; feature archives tasks, admissions and control gates. Share mechanics, not a lossy conversion of historical evidence. Workload proof schemas and freshness policy remain explicit. |
| C02 | `T/20-scopes/{core-server-persistence,entity-smoke}/{00-declaration,10-workload-binding}`; `T/30-provider-realization/aws/cloudformation/{core-server-persistence.yml,entity-smoke.yml,entity-smoke-isolated-restore.yml,entity-smoke-publication.yml}` | **Keep identities, resources and contract facts.** Parameterise common code from existing bindings. Similar IAM/task template fragments are later factoring candidates, not established safe deletions or permission to combine stacks. No logical resource ID changes in initial slices. |
| C03 | `I/entrypoints/entity-smoke/{administration.ts,preflight.ts}` imports of `kanbien-core-server-persistence-{configuration,role-credential}.ts`; shared platform PostgreSQL modules | **Keep existing reuse; improve ownership later.** Reuse already occurs through files named after the baseline. A later extraction can give common configuration/role helpers a neutral home and remove accidental dependency on baseline composition, with image copy/compile closure tests. This inventory does not classify all feature SQL as duplication. |
| C04 | `apps/entity-smoke/features/test-entity/`; `I/entrypoints/entity-smoke/{postgresql.ts,migrations.ts,verification.ts,database-verification.ts,proof-facts.ts,runtime.ts,configuration.ts}` | **Keep workload behaviour.** Fields, migrations, schema/roles, endpoint composition, lifecycle operations and their assertions are the feature itself. Only infrastructure mechanics or duplicated connection configuration are consolidation candidates. |
| C05 | `P50/{apply-database-permission-surface,apply-observability-mvp-surface,apply-private-verifier-route-update,apply-restoration-verifier-surface,reconcile-rds-log-export-surface}/script.py`; `P60/{observability-receipts.py,rehearse-observability-readiness,qualify-proof-applicability,qualify-rollback-predecessor}` | **Preserve baseline-only capabilities.** They are not duplicates of feature functionality simply because they occur in the larger baseline route. Their shared transport may migrate later; retiring them requires an actual caller/support review. |
| C06 | `scripts/repo/check-selection/checks.yml`, `scripts/repo/diagnostic-coverage/reviews.v1.json`, `scripts/04.deploy/inventory-deploy-control/`, both scope acceptance routes, package contracts and publication workflow validators | **Update with each extraction.** Moving a common module without updating selector inputs, copied fixtures, diagnostic source ownership and registered command routes would reproduce previous failures. Do not weaken selection or discard negative assertions to obtain a pass. |
| C07 | Both `T/20-scopes/*/30-release-evidence/` trees | **Keep immutable history.** Accepted records, proof receipts, original release candidates and current references are evidence, not code duplication. Their readers need backward compatibility. |
| C08 | `E60/README.md`, original feature plan and original fixed PostgreSQL workflow | **Update active guidance when callers change; retain historical decisions.** Feature README still says full live acceptance has not run, while the accepted reference records completion. It must not be used as current-status authority. This inventory records that stale guidance without rewriting it during the audit. |

## Concrete overlap evidence

### Runtime assembly is independently implemented

In the baseline [assembler](../../../scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs),
`writePackageShim` creates each package directory, writes CommonJS forwarding
files and writes its export manifest. The feature
[assembler](../../../scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs)
implements the same loop inline, plus JSON copying and dry-run support.
Both first check compiled entrypoints and exports.

Their wrappers differ materially: baseline wrappers immediately invoke the
selected export; feature wrappers support importing without starting the
program and report through the feature diagnostics module. The baseline also
has its own `runtime-contract.mjs` shared with `verify-runtime.mjs`. Preserve
these policies explicitly when extracting the common file-writing operation.

The older `L/40-package/build-core-server-image/prepare-runtime.mjs` contains
another fixed package-shim loop. It is an adjacent historical bootstrap caller,
not a generic implementation to adopt blindly. Do not expand the first slice
to changing that accepted-historical route.

### ECS response validation repeats the same rule

Baseline [task evidence](../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/ecs-task-evidence.py)
exposes `task_overrides_match(task, container_name, expected_environment)`.
The feature [task controller](../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-control.py)
repeats that shape/environment check inside `exact_task`, alongside additional
reservation identity checks. Those surrounding identity checks must remain.
The baseline's server-observation helper accepts a different service-task
override shape; do not merge it into this one-off task predicate without a
separate contract.

### Accepted history depends on incident code

The feature [source transition module](../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/source-transition.py)
contains pinned recovery exceptions for particular attempts. Its imports reach
normal task and acceptance paths. Removing those constants just because the
incident ended would change the interpretation of existing proof.

The cleanup target is to separate historical read compatibility from future
execution, not to allow arbitrary replacement hashes or to erase the history.

## Tests and migration consumers

| Slice | Existing coverage to retain or adapt |
| --- | --- |
| Payload assembly | `L/40-package/smoke-test-core-server-persistence-image/payload-fixture-test.sh`; baseline `verify-runtime.mjs`; feature composition `smoke-test.sh`, `dependency-boundary.mjs` and `runtime-test.mjs`; both Dockerfile copy closures. Add focused common-assembler cases for both bindings and a renamed fixture. |
| Dependency assembly | Feature `build-entity-smoke-image/dependency-test.mjs`; both final-image capability negatives and runtime imports. Baseline telemetry dependencies remain required. |
| Publication | Both `verify-workflow.py`; feature `workflow-test.py`, `pipeline-test.py`, `publication-test.py`; baseline `qualification-route-test.py`; shared custody and qualification tests. |
| Task/provider handling | `P50/controller-regression.py`, `provider-cli-regression.py`; `P60/fixtures/ecs-captured-responses.yml`, `verify-candidate/operation-test.py`; `E60/task-{control,evidence,runner,route,binding}-test.py`, `preflight-control-test.py`; shared provider recovery tests. |
| Infrastructure/recovery | Baseline replacement/credential/restore routes and acceptance rehearsal; feature `deployment-control-test.py`, `infrastructure-route-test.py`, `resource-control-test.py`, `failure-route-test.py`, `restart-route-test.py`, `credential-route-test.py`, `restore-{control,route}-test.py`, `source-transition-test.py`, `image-delivery-repair-test.py`, administrator observation/recovery tests. |
| Acceptance compatibility | `P60/proof-receipts-smoke-test.py`, `collect-acceptance-evidence/{smoke-test.py,current-observations-test.py}`, `acceptance-route-rehearsal/{controller-fixtures.py,smoke-test.py}`; `E60/acceptance-{control,aggregate,route}-test.py`; shared release-succession tests; read-only validation of retained records. |

Existing selector units include `persistence-payload-regression`,
`persistence-composition`, `entity-smoke-composition`,
`persistence-provider-regression`, `entity-smoke-publication-contract`,
`entity-smoke-acceptance-controls` and `acceptance-route-regression`.
Container units are `persistence-container` and `entity-smoke-container`;
alignment and acceptance have separately registered later-stage units.
Do not run all later-stage units after each local source edit.

## Protected acceptance references

| Scope | Current release | Current-reference SHA-256 |
| --- | --- | --- |
| `core-server-persistence` | `release-570327efbb91af717da6da13` | `02bfafd548967031922e3d99ad57c4f1a221f9b3acff5b3c0c0ec67710dac453` |
| `entity-smoke` | `release-53798ef563be4ce9a8c5b2f0` | `77055d8fbeabc53190c22d1b64de5238432a1913948b10bec9a1a4a1f0464cf5` |

The files are each scope's
`T/20-scopes/<scope>/30-release-evidence/current-accepted-release.yml`.
These hashes protect the inventory baseline; they do not replace the existing
accepted record validators or assert current AWS health.

## Remaining design work

### A04 implementation checkpoint — 2026-11-14

Both original runtime preparers now delegate their filesystem assembly to
`scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/assemble.mjs`.
Their workload-specific mappings, wrapper policies and diagnostic adapters
remain at their original public paths; both independent write loops are gone.
Docker copy closures, future qualification receipt inputs, focused test
registration and diagnostic review consumers have been updated together.

Controlled fixtures and fresh compiled payload checks passed. Parent review,
final registered integration and actual image qualification remain pending;
this is not completion of the consolidation programme. See the plan's
[A04 implementation record](../../../.agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md#implementation-record--slice-a04)
for changed owners, exact results, size measurements and remaining work. The
pinned inventory counts above still describe the original checkpoint, not the
working-tree result. Accepted history and AWS resources are unchanged.

Connected-consumer review subsequently found that both default-deny Docker
context filters also needed exact shared-module exceptions. Those filters,
future qualification inputs and omission fixtures are now corrected. The
corrected 23-case local assembler suite passed in 10.646s and both workflow
suites passed. Parent review is reopened for this correction; the interrupted
final batch produced no completed aggregate report. Its two completed leaf
receipts and all outstanding verification are recorded in the plan. A05 has
only been compared, not implemented.

The subsequent registered six-check run completed with five passes and one
failure in 834.665s. The failure was the baseline local-public-image recovery
route's stale exact Dockerfile pin, after its actual payload and workflow
fixtures passed. That pin is now refreshed to the parent-reviewed Dockerfile;
its existing 45-case controlled recovery fixture passes. Review and the
affected registered rerun remain pending. The full report path and per-check
timings are retained in the plan; this is still not full integration or image
qualification.

The parent subsequently reviewed that exact recovery-pin correction. The
registered persistence rerun passed in 28.587s (54.444s total), with zero findings;
its retained report is recorded in the plan. A04 source review and focused
evidence are established. Full affected integration is now explicitly batched
until connected package slices are frozen; actual images remain unqualified.

### A05 implementation checkpoint — 2026-11-14

Both Dockerfiles now use the feature's existing installed-lock dependency
resolver, extracted once to `L/40-package/prepare-runtime-dependencies/prepare.mjs`.
Two thin bindings retain the feature's two roots and declare the baseline's six
PostgreSQL/observability roots. Baseline manual whole-namespace copies are removed;
the feature no longer carries a separate resolver implementation. Both context
filters, qualification input owners, omission tests and compiled consumers were
updated together. Selected installed dependency counts in fresh local payloads
were 52 for baseline and 40 for feature, with independent imports/runtime checks
passing without checkout dependency fallback.

The 12-test common dispatch, retained feature fixture, both workflow omission
suites, real selector/fingerprint counterexample, diagnostic coverage and affected
metadata passed exploratorily. Parent review and registered focused verification
remain pending. The baseline recovery command's exact Dockerfile pin deliberately
awaits review of this new dependency mechanism before refreshing. Script lines
increase by 63 (140 becomes 148 common + 27/28 bindings); consolidation removes
duplicate responsibility and broad copies, not a measured net line reduction.
The plan records exact results, paths and limits. No accepted reference, workload
identity, Git checkpoint, publication or AWS state has changed.

### Later slices

A05 parent review and the narrow preflight-fixture correction are complete.
The corrected registered composition check passed in 467.133s execution
(493.627s total); its retained report is linked in the plan. The earlier failed
observation remains retained. Full affected integration and real images remain
pending, not implied by these focused passes.

### A06 implementation checkpoint — 2026-11-14

Both actual builders now use one private `L/40-package/build-candidate-image/operations.sh`
for common prechecks and Docker arguments. Workload source/tag/engine/test policies
remain in the original callers. Both existing workflow validators and future
qualification bindings cover the helper. Controlled actual-builder fixtures
exercise preserved arguments, order, failures and a renamed binding; existing
selector/fingerprint and recovery fixtures cover the new connected input.
Parent review and exact recovery-pin refresh completed. All three registered
focused checks passed (206.423140s total); the plan retains the exact receipt.
Full affected integration and actual image qualification remain pending.
Physical production script lines rise from 93 to 117, net +24; this is shared
responsibility, not a net code-size reduction. Details and limits are in the plan.

### B03 implementation checkpoint

The existing `scripts/04.deploy/shared/provider-adapters/aws/response.py` owns one
exact ECS override predicate. Baseline historical import and feature exact-task
caller delegate to it, retaining feature identity checks, diagnostics and each
route's separate task lifecycle policies. Copied-consumer inputs, selection and
independent malformed-response fixtures are migrated. No extra helper module or
submission system was added. Production files grow by 10 physical lines because
of compatibility imports/metadata; duplicate override logic is removed. Final
parent review and all three registered focused checks passed; exact B03 receipt
and timings are recorded in the plan. Later connected input changes need fresh
matching evidence.

### B04 implementation checkpoint

All nine inventoried wrappers now use one private AWS `cli.py` invocation/JSON
owner beside `response.py`: baseline prepare, migrate, verify, retire, RDS-log
reconciliation, collector and observability; feature alignment and infrastructure
Provider (including inherited routes). The plan records each original timeout,
environment, empty-body/JSON and error/retry policy. Old wrapper mechanics are
removed, not retained as fallback. No workload-name selector was introduced.

Exact source/repair identities, copied fixtures and affected input/selection
rules include the helper. Outside-route bootstrap/foundation invocations are
explicitly not migrated; existing shared-consumer regression obligations remain.
The host's local-check bound is corrected to 900s without changing selected
checks, trusted input-bound reuse, ECS deadlines or AWS authority. Nine wrappers
plus helper grow by 48 physical lines (and two response relationship lines),
not a claimed size reduction. Parent source review and local actual-caller
exploratory checks are complete; batched registered integration and actual
images remain pending.

### B02, A08 and initial B01 connected checkpoint

B02 now shares reserved ECS execution/reconciliation/polling across the four
actual lifecycle consumers, reusing the verifier journal protocol for new baseline
migration/administration executions and retaining feature admission/store schema.
The six declared administration phases have mapped explicit predecessor inputs;
old receipts/read-only reconciliation remain readable. Failed migration requires
the existing fresh replay-permitted database-state receipt, never terminal task
status alone. Parent source review and actual-caller exploratory tests pass;
registered connected verification remains pending. B05 broader ordering work is
not claimed complete.

A08 uses one shared immutable ECR publication engine with two static bindings.
Baseline inline push mechanics are removed; feature schemas/selectors remain.
Both actual bindings and a renamed fixture pass local doubles, including failure
retention and native diagnostic cases. The bootstrap inline-publication contract
remains for its separate consumer. Source/selector/diagnostic closure is reviewed;
actual images/publication and final registered batch remain pending.

Initial B01 shares immutable resource reservation and change-set prepare/execute
mechanics. Baseline CREATE/execute now reserve before one call and check positive
token lineage; feature preserves its stronger resource/template/tag/rollback
policy. Explicit historical reconciliation still works without manufacturing
reservations. Independent old-envelope and foreign-completion negatives pass.
Remaining baseline update/incident callers are still B07/B11 work, not implicitly
covered. Exact changes, corrections, timings and limits are in the plan.

B06 implementation and parent source review close the normal-path original-task
reselection gap. Shared fresh-only replacement now serves both callers; the
baseline adds a closed existing-store binding and actual credential receipt
admissions for later revoke/restore replacements. The full controlled controller
fixture passed 46 tests in 2.480 seconds. Registered connected integration and
actual image/live proof remain pending; historical readers and accepted records
are unchanged. B09 snapshot implementation is now source-reviewed: shared
reserved submission serves both routes, while the baseline new-execution binding
adds source-incarnation/tag/time identity and retains explicit historical reads.
Three focused baseline tests passed in 0.029 seconds; feature resource tests pass.

B05/B08 comparison retains genuinely different orchestration rather than adding
a scheduler: baseline credential main replaces after revoke and after restore;
feature prerequisite validation retains the original server through revoke and
replaces after restore. Their actual effects use shared B02/B06 execution.
The actual baseline main fixture proves all three modes and stop-on-failure
ordering (0.023 seconds). Exact functions and proof ownership are in the plan.

B10 removes feature restore's duplicate reserved CloudFormation submission and
baseline restore's duplicate ECS task discovery. Both use existing shared owners.
Parent source review and actual restore/discovery fixtures pass. Direct-RDS clone
plus temporary IAM grant/cleanup remains distinct from feature eight-resource
CloudFormation clone plus original-reader/physical-map cleanup. This is an
explicit policy comparison, not a claim that legacy baseline restore acquired
feature durable resume semantics. B07 UPDATE callers also use common mechanics
while retaining explicit read-only interruption reconciliation. C06 source,
copied fixture, selector and partial diagnostic closure accompanies these slices;
registered connected verification and actual images are still pending.

Parent-owned C03 extraction now separates configuration selection from the
baseline runtime factory. Fresh feature compilation excludes four formerly
borrowed baseline application/runtime sources; Docker copies and omission tests
follow the new shared selector. Canonical configuration/credential/diagnostic
paths have not moved. The [prepared migration plan](../../../.agentic/04.deploy/plans/migration/shared-persistence-entrypoints.md)
maps current callers and three retained old-path export wrappers; its required
committed-plan checkpoint is not yet authorised. No completed C03 migration is
claimed.

B11 retired four obsolete incident executors in place (net 428 lines removed),
retaining typed historical readers and validated original-attempt reconciliation.
New launches under the frozen incident label are rejected by actual task/restore
callers. Parent and agent source reviews and controlled fixtures passed; accepted
evidence is unchanged. Remaining baseline UPDATE protocol still requires explicit
read-only reconciliation rather than acquiring automatic durable resume.

A01 common AWS transport is consolidated; the inspected foundation/database/
image alignment predicates and ordered observations remain distinct policy.
A02 already reuses ECS normalization. A03 retains workload-specific compilation
with C03's accidental dependencies removed. A07 retains distinct database/role/
TLS/volume proof setup while using common cleanup; no extra callback framework
is introduced solely for unlike command lists. These are compared dispositions,
not omitted source inventories or actual-image qualification.

Stage 4 now has a reviewed connected `ledger-probe` fixture: actual payload
assembly and isolated Node execution connect shared CloudFormation/ECS/snapshot
reservation operations to retained proof hashes and the existing candidate
constructor. The existing payload wrapper passed 23 Node cases (10.711 seconds)
and two connected Python cases (2.214 seconds). It rejects missing/changed package,
failed program, foreign task and altered proof, and reconciles a lost write
without a second write. This uses controlled provider/SQL doubles, not real
PostgreSQL, OCI qualification, arbitrary target CLI deployment or AWS evidence.

C06's expanded selector method passed in 348.005 seconds after exposing and
correcting one duplicate catalog input and two missing actual-caller task inputs.
Structural diagnostic coverage passed 729 sources with zero findings. These are
exploratory outcomes. No new registered batch is running while the authorised
independent reporting projection changes global selector inputs. Full affected
integration, package qualification and consolidation completion remain pending;
old receipts are reused only if their actual input hashes still match.

The plan records a cumulative pre-final-record snapshot: source/config net +1279,
tests net +2050, governance/docs net +3186 lines, with explicit classification
and unrelated education excluded. Consolidation is not presented as an overall
line-count reduction; the four-executor net removal is only that bounded slice.

### Remaining comparisons

The inventory is sufficient to start the bounded payload slice. Later execution
slices still need operation-level input/output and failure comparisons before
choosing the surviving implementation. In particular:

- Preserve the recorded B05/B08 route-owned ordering and typed admission differences; shared task effects are already migrated.
- Retain initial-release and subsequent-release recovery policies separately.
- Separate historical acceptance compatibility from live provider checks and
  from incident-specific repair effects.
- Measure actual verification/runtime costs; these file totals do not establish
  how many hours any one component caused or guarantee a speed improvement.

No files are marked safe for immediate deletion. Removal becomes concrete
inside the slice that migrates their callers and proves replacement behaviour.

## Ordered authorised follow-on scope

The existing plan now records three workstreams in order:

1. Complete the deployment-route consolidation inventoried here.
2. Complete the queued evidence-reporting safeguard using the existing selector,
   status/evidence owners and retained reports.
3. Implement declaration-derived build/packaging and its ongoing governance and
   enforcement, reusing the consolidated mechanisms rather than a new framework.

The third workstream must first extend this inventory across existing repository
build routes and their repeated mappings. Package manifests own package names,
public exports and dependencies; existing runnable-program declarations own the
selected program/approved dependency boundary; deployment configuration owns
deployment settings. Discovery does not automatically approve dependencies or
cloud access. Correct incomplete manifests and explicitly declare non-derivable
assets/dynamic requirements before removing superseded handwritten copies.

Extend existing product/build/package/feature standards and workflows, validators
and test selection. Prove add/change/remove, fresh output without stale files,
isolated execution, existing workloads and a differently named fixture. Preserve
legitimate frontend/backend differences; report adoption and exceptions per route
rather than inferring repository-wide coverage from `test-entity`. Independent
local implementation is now active after the reporting safeguard's focused
proof. Consolidation's C03 canonical migration and package qualification remain
pending their checkpoint boundaries; commit/publication/AWS limits are unchanged.

### Current declaration/build adoption inventory

The source census found 21 workspace manifests and 69 TypeScript configs, with
27 handwritten alias maps. Twenty-two workspace runtime/integration/check maps
now derive through the neutral compiler command. The remaining three program,
legacy shell image and diagnostic catalogue maps have also been migrated. Plain declaration-only library build
modes and npm command names/order remain unchanged. Four initial manifest gaps
were corrected; PostgreSQL integration then exposed four additional test-only
dependencies reached through relative entrypoint/application imports, now
declared as development dependencies with matching lock metadata.

The corrected source census is 27 callers: 21 workspace runtime/integration
dispatchers, four deployment preparers, one bootstrap runtime-boundary test and
one diagnostic exporter. The earlier25count omitted the feature's inline
preparer and one legacy/boundary consumer. Contracts, ECS Fargate and DynamoDB
rate-limiter dispatchers contain inline writers missed by the original symbol
search. The shared deployment assembler is the surviving consumer of the neutral
package mechanism, not another handwritten caller counted here. Its extraction
is source-reviewed. All 21 workspace dispatchers now use the shared mechanism;
their discovery/failure regression and two actual package test commands passed.
All four deployment preparers, the bootstrap runtime-boundary test and the
diagnostic exporter now use declaration-derived maps and the shared assembler.
The two installed external-dependency adapters also read their selected roots
from canonical program bindings; their lock traversal remains shared. Final
matching-input proof and packaging qualification are not complete.

Exploratory compiler evidence: 21 of 22 real workspace compiler children passed
in the initial 125.374-second batch; the failed PostgreSQL integration child
passed in 11.408 seconds after its declaration repair. Five CLI tests passed in
0.532 seconds. Three actual program compiler bindings passed independently.
These observations do not establish final matching registered integration,
fresh-output behavior for every route, real image qualification or live proof.
Detailed failure/correction timing and review status remain in the existing plan.

Latest focused proof: legacy shell compilation, preparation and isolated compiled
runtime check passed; diagnostic compiler, current-export check and disposable
regeneration/conflict fixture passed; both installed external-dependency adapters
resolved their actual lock closures without writes. The six-container boundary
check initially caught new helper allowances after final deny rules; moving the
exact allowances before those rules restored zero findings. No new OCI image or
AWS acceptance is claimed. The declaration-derived selector context and generic
program enforcement are implemented and source-reviewed; final matching-input
registered verification remains pending. Actual npm command/project selection
now supplies package inputs without a second unit map, including inherited npm
hook policy and manifest discovery. The generic program checker validates new
build declarations through the canonical reader while preserving legacy purely
structural records. Neutral compilation and projected plain `tsc` commands both
reject effective handwritten aliases, including inherited configurations.

The bootstrap observer's eight-workspace `PACKAGE_ROOTS` table and special export
path convention were removed. Canonical program bindings and Node's own builtin
projection now feed its independent literal-import, manifest, lock and compiled
output checks. Foreign-namespace rejection and the complete actual bootstrap
suite passed; exact evidence is recorded in the existing implementation plan.
All source-owned maps in the original census are migrated. This does not close
the C03 canonical-path migration or actual image qualification, both still
pending their checkpoint authority boundaries.
