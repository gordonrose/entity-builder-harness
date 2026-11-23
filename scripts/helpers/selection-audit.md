<!-- agentic-artifact:
schema: agentic-artifact/v3
id: repo.report.verification-selection-audit
version: 5
status: draft
created_on: "2026-11-23"
updated_on: "2026-11-23"
layer: 06.shared
domain: scripts.catalogue
disciplines: [architecture, agentic, sre]
kind: report
purpose: Record the normal verification-selection baseline and evidence-backed deferred checks.
portability: {class: internal, targets: []}
used_by:
- id: repo.check-selection.catalog
  path: scripts/repo/check-selection/checks.yml
-->

# Verification-selection audit

This is the milestone-one decision record for normal verification selection.
It does not add a second selector or scheduler. `scripts/repo/check-selection`
remains the execution authority.

## Catalogue baseline

The catalogue contains 178 checks.

| Boundary | Before this slice | After this slice | Meaning |
| --- | --- | --- | --- |
| Commit | 2 candidate local checks | 1 candidate, 1 deferred | The PostgreSQL-version policy check remains focused commit proof. The whole-repository module-structure scan is retained but no longer executes automatically. |
| Integration / merge | 171 candidates and 5 hygiene checks | 171 candidates and 5 deferred checks | Focused local, package, deploy, and acceptance candidates keep their declared direct-input selection. The five checks already labelled hygiene no longer execute automatically on merge. |

The 171 unchanged integration candidates are declared by lifecycle stage:

| Stage | Count | Normal lane |
| --- | --- | --- |
| Local | 147 | Focused code-change or merge proof, according to direct inputs. |
| Package | 8 | Package/artifact qualification. |
| Deploy | 4 | Declared deployment transition/alignment. |
| Acceptance | 12 | Deployed runtime/acceptance evidence. |

This is a declaration-level map, not a claim that all 171 run for one change.
The selector still uses each check's direct inputs to choose the relevant small
subset.

## Deferred checks

`deferred` means retained, visible in a selection report, and runnable by an
explicit named request, but never executed by ordinary commit or integration
selection. It is not a pass, deletion, or a scheduler.

| Check | Named risk | Former automatic route | Retained manual route |
| --- | --- | --- | --- |
| `module-index-structure` | Whole-repository public-index, configuration-access, module-boundary, and declared-import drift. | Commit and merge when any broad source root changed. | `--checks module-index-structure` |
| `diagnostic-adoption` | Broad diagnostic-adoption coverage drift. | Integration/merge when its diagnostic coverage inputs changed. | `--checks diagnostic-adoption` |
| `diagnostic-runtime-contracts` | Aggregate diagnostic runtime-contract drift. | Integration/merge when its aggregate inputs changed. | `--checks diagnostic-runtime-contracts` |
| `check-selection-repository-contracts` | Full selection-catalogue and repository-contract consistency. | Integration/merge when its selector inputs changed. | `--checks check-selection-repository-contracts` |
| `check-selection-regression` | Broad selector regression suite. | Integration/merge when its selector inputs changed. | `--checks check-selection-regression` |
| `package-custody-regression` | Broad package-custody receipt regression. | Integration/merge when its package-custody inputs changed. | `--checks package-custody-regression` |

The existing exact request form is:

```bash
python3 -B scripts/repo/check-selection/script.py \
  --checks <check-id> --execute-local --json
```

The module-structure fixture regression remains a candidate when its own
implementation or fixtures change. That proves changes to the scanner without
rerunning the repository-wide scan for every ordinary source change.

## Evidence

- The original catalogue had two commit candidates and 176 integration checks;
  five integration checks carried the existing `hygiene` cadence.
- The module-structure check declared broad `scripts`, `packages`, `platform`,
  `apps`, `products`, and `infra` inputs, while its implementation scans those
  areas as one architecture report.
- A focused selector test proves a deferred check is not executed at either
  normal boundary but does execute when explicitly named.
- The module-structure catalogue contract and its focused workspace-dependency
  regression remain covered by their existing tests.

## Deliberate deferrals

This slice does not schedule, delete, weaken, or reclassify the 171 focused
candidate checks. Their lane suitability needs evidence from representative
product, deployment, and package changes in milestone two.

## Milestone-two probe — not yet accepted

The following are real, non-executing plans through the existing selector with
the recorded-promotion (`ci` and `changed-only`) inputs. They establish that
the first deferral slice removed broad scans, but did **not** yet establish a
lean normal lane. No selected test command ran.

| Representative changed file | Candidate proof selected at its local stage | Deferred checks shown in the report | Result |
| --- | ---: | ---: | --- |
| `packages/core/src/index.ts` | 21 | 2 | Too broad. Most candidates share `packages/core` as a declared input, so one Core file is still treated as potentially affecting many runtime areas. |
| `scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/assemble.mjs` | 7 | 4 | Stage separation works: two container checks are held for the package stage. Seven local candidates still need a direct-consumer review. |
| `scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.sh` | 0 at the probe | 2 | The probe exposed a missing direct proof. The correction below now selects one existing focused proof. |

The two deferred checks in the first and third rows are
`check-selection-repository-contracts` and `module-index-structure`; they are
reported but do not execute automatically. The package row additionally holds
the two container checks because the requested stage was local, not package.

This is a useful negative result. The next selection correction must be based
on a direct risk-and-caller audit of the broad `packages/core` input contracts.
It must not simply turn off the remaining checks or make the deferred scans
candidate checks again.

## Direct-contract corrections found during the probe

| Changed input | Named risk | Direct callers/proof | Selection correction | Current normal behaviour |
| --- | --- | --- | --- | --- |
| `core-server-persistence/prepare-candidate/` | A candidate preparation change could alter target, receipt, or provider-precondition handling without its existing local control proof running. | The persistence smoke test invokes the public wrapper; its controller regression imports `prepare-candidate/script.py` repeatedly for the same operation boundary. | Added one direct selector rule for this folder to `persistence-provider-regression`. The unrelated shared deployment-diagnostics regression is deliberately not selected. | A wrapper-only change plans exactly `persistence-provider-regression`, plus reported-but-not-run deferred hygiene scans. |
| `platform/adapters/aws/persistence/postgresql/` | PostgreSQL adapter changes could alter the assembled core-server-persistence composition or its packaged image while only narrower diagnostics checks ran. | `persistence-composition` declares this adapter as an input, and the existing repository-contract test already required both composition and container qualification for a PostgreSQL error-path change. | Added `persistence-composition` and `persistence-container` to the existing PostgreSQL selector rule. | Adapter changes select the two PostgreSQL diagnostics proofs and composition locally; the existing container proof is held for the package stage. No broad hygiene scan executes. |

Both corrections use existing checks and existing caller proofs. They add no
wrapper, scheduler, registry, runtime command, or new test program.

The unresolved Core result remains: ordinary files such as
`packages/core/src/persistence/transactions.ts` still select 20 candidate
checks, while an exported-index or configuration-reader change selects 21.
The common cause is that all active workload scopes declare the whole
`packages/core` directory as a source input. It is a coarse shared-boundary
contract and needs source-to-consumer evidence before it can be narrowed.

## Core fan-out disposition

The 20 checks selected for `packages/core/src/persistence/transactions.ts`
are not broad hygiene scans leaking back into the normal lane:

- ten explicitly declare `packages/core` as an input; and
- ten are package checks whose existing workspace declaration identifies
  `@kanbien/core` as a direct dependency.

That makes them real package-level consumers, not arbitrary path matches. The
problem is granularity: the current declaration can say that a consumer needs
the Core package, but cannot say which Core public module or internal source
file it needs. Therefore an internal persistence change and a public-index
change look almost identical to selection.

The safe disposition is **retain for now, do not defer**. Narrowing this set
would need a source-to-consumer dependency boundary that distinguishes public
Core modules from internal implementation. The repository has a small
Core-only runtime-test selector, but no proven cross-package equivalent. Adding
one would be a separate approved capability, not an incidental change to this
milestone.

## Largest remaining candidate contracts

The remaining large input sets were reviewed as capability boundaries, not by
file count alone. None is a repository-wide hygiene scan selected by an
unrelated change.

| Capability | Why it has many inputs | Current disposition |
| --- | --- | --- |
| Entity Smoke composition | It compiles the feature and proves its public wiring, controlled infrastructure route, payload, and runtime controls. Its 70 listed inputs are the declared feature closure; its two member proofs permit focused route feedback and receipt reuse. | Retain as a named feature-composition proof. Any further split belongs to a later bounded Entity Smoke capability change, not selector deferral. |
| Deployment-operation diagnostics | It covers the shared diagnostic report mechanism plus the Core persistence bindings that currently live together. | Retain; its mixed responsibility is the separately planned milestone-four boundary design. |
| Core-server-persistence composition | It proves one declared persistence workload across its entrypoint, adapter, configuration, package and target bindings. | Retain as the workload composition proof. PostgreSQL adapter selection now reaches it directly. |
| Runtime payload assembly | It verifies the package payload closure spanning declared workspace packages and workload entrypoints. | Retain in the package/build lane; it is not selected by unrelated ordinary product changes. |
| Acceptance-route regression | It checks the declared acceptance handoff and receipt route for the persistence target. | Retain in its target-control lane; no broad root selects it. |

This closes the selection mapping for known broad or dense normal candidates:
each is either deferred hygiene, an isolated retained legacy system, or a
named direct capability/consumer proof. The audit does not claim that every
focused proof is fast; its timing and execution behaviour are the subject of
the next milestone.

## Milestone-two initial observations — superseded

All observations below used unchanged representative paths at the current
revision. They are *as-if changed* selector inputs, not a claim that a source
edit was made or qualified in this slice. No package image, provider command,
or live deployment was run.

| Representative path | Local proof selected for development | Declared budget | Actual observation | Decision evidence |
| --- | ---: | ---: | --- | --- |
| `apps/entity-smoke/features/test-entity/domain/retention.ts` | 5 checks | 120 seconds | The runner had only reached the first 15-second check when the execution environment stopped the observation after 30 seconds; it produced no completed run report. | Not lean enough to accept. The product path still brings the complete Entity Smoke local proof set. |
| `platform/adapters/aws/persistence/dynamodb/src/transactions.ts` | 6 checks | 150 seconds | Its direct adapter command reached TypeScript compilation/build but did not complete in the 30-second observation window. | Not lean enough to accept. It unexpectedly shares the Entity Smoke local proof set as well as its adapter proof. |
| `scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/publication.py` | 5 checks | 120 seconds | The selector's explicit runner stopped with `selection-input-or-runtime-invalid` (`OSError`). The underlying named package-custody smoke command passed in 2.3 seconds. | The package-custody risk remains directly testable, but its ordinary impact selection is not yet bounded. |
| `scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.sh` | 1 candidate check | No budget declared | Planning selects only `persistence-provider-regression`; the two broad checks are reported as deferred and would not run. The selected regression is a large combined shell test with no declared duration, so it was not run unbounded. | Routing is focused, but the deployment proof cannot yet be accepted as a controlled normal-lane check. |

The completed package-custody smoke command proved its named risk: it passed
workflow ordering, provider-free negative cases, immutable reservation,
lost-response, reconciliation, and typed-digest fixtures. Its direct inputs
are the package-custody operation and associated pipeline contracts; changes
there invalidate that result. It neither proves nor invalidates the Entity
Smoke feature, adapter, provider, container, or live-runtime boundaries.

The M1 deferral works in every probe: `module-index-structure` and
`check-selection-repository-contracts` are shown for transparency but did not
execute. That is positive evidence for the hygiene split, not evidence that
the remaining candidate lanes are lean.

### Initial disposition

The initial M2 observations were **not sufficient**. They established three bounded
follow-ups before it can be accepted:

1. trace why an Entity Smoke source, a DynamoDB adapter source, and an Entity
   Smoke package-custody source all select the same Entity Smoke local proofs;
   retain only callers with an evidenced direct risk;
2. repair the selector's explicit local execution `OSError` without treating a
   direct runner pass as a selector pass; and
3. split or budget `persistence-provider-regression` before using it as normal
   deployment-change feedback. Its named risk and manual route remain intact
   until then.

None of these facts authorised disabling a check. The next change mapped the
specific selection edges and direct callers, then made one focused correction.

## Milestone-two final record — complete

All final observations below used representative paths at the current revision
as *as-if changed* selector inputs. They prove selection and bounded local
verification; no image publication, cloud-provider mutation, or live deployment
was performed.

### Correction

The selector previously treated a matching workload scope as a reason to run
every required proof in that scope. That was too broad: a scope tells the
selector where to look, not that every proof consumes every changed file.

For development feedback, the selector now keeps a required scope proof when
one of these is true:

- the proof directly declares the changed source, configuration, or command
  directory as an input;
- the scope declaration or scope index changed; or
- the check catalogue changed, all checks were explicitly requested, or the
  proof explicitly opts into whole-scope inputs.

The focused regression proves both sides: a package-custody publication change
selects its publication proof without Entity Smoke runtime or acceptance proofs;
a changed Entity Smoke scope declaration selects the complete scope proof.

The Entity Smoke acceptance control also stopped claiming all of
`scripts/04.deploy`, `infra/04.deploy/03.product`, and `.agentic/04.deploy` as
direct inputs. Its inputs now name the operation, target scope, and diagnostic
schema it actually consumes. This prevents unrelated deployment work selecting
that acceptance proof.

### Before and after

| Representative changed path | Before | After | Named risk retained | Evidence |
| --- | ---: | ---: | --- | --- |
| `apps/entity-smoke/features/test-entity/domain/retention.ts` | 5 checks / 120 seconds | 3 checks / 100 seconds | Feature composition, controlled infrastructure route, and runtime behaviour. | A real selector plan; deferred hygiene is reported but not pending. The remaining three checks are the declared Entity Smoke aggregate boundary, not unrelated selection. |
| `platform/adapters/aws/persistence/dynamodb/src/transactions.ts` | 6 checks / 150 seconds | 1 check / 30 seconds | DynamoDB adapter build, runtime, and dependency boundary. | The registered `dynamodb-persistence-runtime` command passed in about 30 seconds. |
| `scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/publication.py` | 5 checks / 120 seconds | 1 check / 5 seconds | Package-custody workflow and publication contracts. | The direct package-custody smoke command passed in 2.0 seconds. |
| `scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.sh` | 1 check / no declared budget | 1 check / 90 seconds | Candidate preparation, failed-candidate, migration, verifier, and recovery controls without AWS. | The retained `persistence-provider-regression` command completed inside a 90-second cap; captured output contains its passing controlled test groups. |

For package custody, the selector's execute-local route could not create its
private cache in this terminal sandbox because the active worktree's private
Git directory was mounted read-only. That is an execution-environment limit,
not a selector result or repository failure. The existing public smoke command
was therefore run directly and passed. The selection plan itself is covered by
the focused repository-contract regression.

### Invalidation and retained limits

- A change to a proof's direct declared input invalidates that proof's prior
  evidence. A change to a workload scope declaration, scope index, or the
  catalogue invalidates the complete scope proof.
- DynamoDB source changes no longer select Entity Smoke merely because they
  occur under a generally relevant platform scope. The adapter's registered
  runtime proof remains selected.
- A package-custody publication change no longer selects feature runtime or
  acceptance proof; its publication contract remains selected.
- The deployment candidate proof now declares a 90-second feedback budget.
  Broad catalogue and module-structure scans remain visible as deferred
  hygiene and do not run on this path.
- Entity Smoke feature work still selects three aggregate proofs with a
  100-second declared budget. Those proofs share a documented feature input
  closure. Their further division is a capability-boundary question for a
  later audited migration, not a reason to weaken them in selection.

### Milestone-two disposition

Milestone two is **complete**. Ordinary representative code, package, and
deployment paths now select only their declared direct evidence; broad hygiene
does not execute. The next milestone is the remaining helper audit. It uses
this selection model as evidence, but does not modify it unless an audited
capability exposes another direct-caller error.
