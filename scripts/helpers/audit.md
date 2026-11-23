<!-- agentic-artifact:
schema: agentic-artifact/v3
id: repo.report.helpers-audit
version: 9
status: draft
created_on: "2026-11-23"
updated_on: "2026-11-23"
layer: 06.shared
domain: scripts.catalogue
disciplines: [architecture, agentic]
kind: report
purpose: Record evidence-backed decisions about candidate helpers without moving source files.
portability: {class: internal, targets: []}
used_by:
- id: repo.script.helpers.catalog
  path: scripts/helpers/catalog.py
-->

# Helper audit

This is the human-reviewed companion to `catalog.md`. The catalogue identifies
possible helpers structurally; this audit records what each reviewed module
actually does, who uses it, and whether it should move.

“Lifecycle relationship” means the deployment lifecycle: local qualification,
build, deployment, or runtime verification. It does not mean the chat session
lifecycle.

## Audited helpers

| Module | Harness owner | Lifecycle relationship | Evidence | Decision | Confidence |
| --- | --- | --- | --- | --- | --- |
| `scripts/00.chat/session-log/paths/lib.sh` | `00.chat` — session-log capability | Outside deployment lifecycle | Its declared purpose and [contract](../00.chat/session-log/paths/README.md) define canonical session identifiers and log paths. It has 23 non-test shell callers across startup, session-log maintenance, reporting, recovery, cleanup, and local merge work. | Retain in place as the canonical session-log helper library. Do not extract individual functions. | Confirmed |
| `scripts/00.chat/worktree/paths/lib.sh` | `00.chat` — worktree capability | Outside deployment lifecycle | Its declared purpose and [contract](../00.chat/worktree/paths/README.md) define deterministic worktree paths and resolve registered worktrees. It has six non-test shell callers covering session startup, worktree creation, reporting, recovery, and merge readiness. | Retain in place as the canonical worktree-path helper library. Do not extract individual functions. | Confirmed |

## Boundary observed

These are already correctly scoped capability libraries. `scripts/helpers/` is
only the cross-repository inventory and audit workspace; it is not a reason to
move working helpers away from their owning capability.

## `04.deploy/shared/` audit

Every module below is owned by the `04.deploy` harness. The audit used each
module's declared purpose and exact non-test references. “Shared” means a
mechanism is reused while its caller keeps the stage-specific policy and proof;
it does not mean every module belongs to every lifecycle stage.

| Module | Actual role | Lifecycle relationship evidenced by callers | Decision | Confidence |
| --- | --- | --- | --- | --- |
| `safe-command-diagnostics.sh` | Redacts bounded command failure diagnostics. | Package image-build and package-custody scripts; also supports the retained diagnostics module. | Retain as a package-facing diagnostic helper. | Confirmed |
| `deployment-operation-diagnostics.py` | Builds safe deployment-operation reports and classifies bounded provider failures. | Used by package publication, deploy transition/create-change-set, and runtime evidence/rehearsal scripts. | Retain as a cross-stage diagnostics module; audit its internal size separately before extracting anything. | Confirmed |
| `postgresql-version.py` | Separates declared PostgreSQL compatibility from the exact qualification version. | Referenced by target alignment, package custody, image qualification, and runtime restore control. | Retain as a cross-stage database-version helper. | Confirmed |
| `provider-adapters/aws/cli.py` | Executes one caller-approved AWS CLI request without granting authority or retrying. | Referenced by target alignment, deployment, and runtime scripts. | Retain as a cross-stage AWS invocation helper. | Confirmed |
| `provider-adapters/aws/response.py` | Classifies safe AWS CLI outcomes and validates bounded task overrides. | Referenced by target alignment, deployment, runtime, and retained platform-shell scripts. | Retain as a cross-stage AWS response helper; keep legacy callers separate from core-platform work. | Confirmed |
| `provider-adapters/aws/change_sets.py` | Performs a reserved, single CloudFormation change-set submission. | Referenced by target alignment, deployment, and runtime control. | Retain as a cross-stage deployment-operation helper. | Confirmed |
| `provider-adapters/aws/tasks.py` | Submits or observes a reserved ECS task without replaying an uncertain operation. | Referenced by target alignment, deployment regression, and runtime task control. | Retain as a cross-stage task-operation helper. | Confirmed |
| `provider-adapters/aws/ecr-scan.py` | Obtains and validates the exact image scan result. | Referenced by target alignment, package custody, deployment preparation, runtime, and publication workflows. | Retain as a cross-stage image-assurance helper. | Confirmed |
| `provider-adapters/aws/foundation-checks.py` | Validates shared AWS foundation and private-network observations. | Referenced by target alignment, deployment preparation, and runtime scripts. | Retain as a cross-stage foundation-observation helper. | Confirmed |
| `provider-adapters/aws/cloudformation-template.py` | Normalizes CloudFormation templates for exact comparison. | Referenced by target alignment, package custody, deployment, runtime, and retained platform-shell release control. | Retain as a cross-stage template-comparison helper; keep legacy callers separate from core-platform work. | Confirmed |
| `provider-adapters/aws/ecr_publication.py` | Publishes one qualified immutable ECR image. | Referenced by two package-custody publication modules. | Retain as a package-only publication helper. | Confirmed |
| `provider-adapters/aws/ecr_publication_contract.py` | Produces the bounded ECR publication command contract. | Referenced by one current package-custody workflow verifier. | Retain in place as a narrow package workflow helper; do not claim broader reuse until another real consumer exists. | Confirmed narrow scope |
| `provider-adapters/docker/disposable-cleanup.py` | Removes declared disposable Docker effects and proves their absence. | Referenced by package image qualification and custody workflows. | Retain as a package-only disposable-cleanup helper. | Confirmed |
| `provider-adapters/aws/resource_reservation.py` | Retains immutable resource-operation intent before submission. | Referenced by entity-smoke target alignment and runtime resource control. | Retain as an alignment-and-runtime resource helper. | Confirmed |
| `provider-adapters/aws/snapshots.py` | Submits one reserved snapshot without adopting or deleting objects. | Referenced by entity-smoke target alignment and runtime resource control. | Retain as an alignment-and-runtime snapshot helper. | Confirmed |
| `provider-adapters/aws/task_journal.py` | Preserves a locked task-operation journal and predecessor protocol. | Referenced by core-server-persistence runtime candidate verification. | Retain as a narrow runtime helper; do not promote it to a general lifecycle library without another real consumer. | Confirmed narrow scope |
| `provider-adapters/aws/cognito-provisioning.py` | Observes bounded Cognito provisioning effects. | Referenced only by retained platform-shell client-provisioning scripts outside the lifecycle tree. | Retain as a legacy provisioning helper, separate from kanbien-core-platform lifecycle work. | Confirmed |

## Function-level audit: deployment-operation diagnostics

`deployment-operation-diagnostics.py` is not a single helper. It joins a
general retained-report capability to a core-server-persistence runtime binding.
The following boundary is based on source responsibility and direct callers,
not its directory name.

| Lines and functions | Actual responsibility | Consumers | Ownership decision |
| --- | --- | --- | --- |
| 50–78: `runtime_contract`, `validate_runtime_diagnostic`, `validate_related_diagnostics` | Converts the executable diagnostic contract into the module's safe failure vocabulary. | Core-server-persistence runtime scripts use the validation functions; generic report validation also relies on the same contract shape. | Retain with the general diagnostics capability for now. |
| 79–297: `validate_persistence_task_failure`, `collect_persistence_task_failure`, `validate_persistence_controller_checkpoint` | Validates and collects one target's task evidence. The source hard-codes the core-server-persistence scope, its report schemas, command paths, task ARN form, account, and receipt location. | Only core-server-persistence runtime verification, administration, and rehearsal scripts. | This is a target-specific binding, not a general shared helper. It is the primary future extraction candidate. |
| 304–362: safe values, timestamps, facts, and execution validation | Rejects unsafe identifiers, evidence, timestamps, and execution vocabulary before a report is retained. | Used by the general report validator and builder. | Retain as shared report-validation mechanics. |
| 364–396: `validate_verifier_result` | Validates the persistence restore-verifier envelope. | Only core-server-persistence acceptance and restore rehearsal scripts. | Belongs with the target-specific binding above, not the general helper. |
| 398–531: `validate`, `build_report`, `write_report` | Defines, validates, and atomically writes the general retained deployment-operation report. | The package diagnostic CLI, deployment change-set scripts, and runtime evidence/rehearsal scripts. | Retain as a genuinely cross-stage shared capability. |
| 533–623: AWS and CloudFormation classification/collection | Safely classifies an existing provider failure without retaining raw provider text. | Core-server-persistence deployment transition and change-set scripts. | Retain as deployment diagnostics; it is provider-specific but not target-specific. |
| 625–698: CLI adapter | Offers the generic report capability to shell/package workflows. | The shared safe-command wrapper and the observability-collector publication workflow. | Retain with the general report capability. |

### Extraction decision

No code moves now. The evidence establishes a real split, but not a safe
mechanical one: the general `validate` and `build_report` functions currently
call the target-specific task-failure validator. Moving only the obvious
functions would leave the general report schema coupled to a hidden target
binding.

Before extraction, design one explicit boundary: the general report capability
must either stop carrying `task_failure`, or receive a caller-owned validator
for that optional evidence. Only then can the persistence-specific functions
move as one cohesive binding to the core-server-persistence runtime area.

## Lifecycle-local JavaScript audit

The structural catalogue flagged these modules because they export functions.
That is only a starting signal: an export can be test support, a capability
contract, a target binding, or a shared mechanism. The decisions below are
based on their declared purpose and direct non-test callers.

| Module | Actual role | Lifecycle relationship evidenced by callers | Decision | Confidence |
| --- | --- | --- | --- | --- |
| `20-build/core-server-persistence-composition/fixture-runtime.mjs` | Disposable compiled-fixture support: it copies, fingerprints, and cleans a test fixture. | Used by the core-server-persistence composition smoke test and its focused test programs. | Retain with the composition capability as test support. It is not a general helper and does not warrant a shared move. A future capability-folder migration may place it under `tests/`, but no move is justified now. | Confirmed |
| `20-build/runnable-program-contract/build-inputs.mjs` | Reads the declared runnable-program contract and produces approved compiler/package inputs. | Used by the runnable-program compiler and by core/entity package preparation and verification callers. | Retain in the runnable-program-contract capability as its cross-stage input boundary. It should not become a generic helper: its value is enforcing this particular declared contract. | Confirmed |
| `20-build/runnable-program-contract/compile.mjs` | Converts the declared program inputs into one bounded workspace-compiler invocation and finite diagnostics. | Used by runnable-program compilation and current package image preparation paths. | Retain beside `build-inputs.mjs` as the matching compiler adapter. The pair is a cohesive build contract, not a reason to create another shared compiler wrapper. | Confirmed |
| `40-package/build-core-server-persistence-image/runtime-contract.mjs` | Defines the core-server-persistence executable wrapper names and wrapper source. | Used only by that image capability's runtime preparation and validation. | Retain as a target-specific package binding. It must not be promoted to `shared`. | Confirmed |
| `40-package/prepare-runtime-dependencies/prepare.mjs` | Safely selects and copies a workload-bound installed dependency closure. | Used by both entity-smoke and core-server-persistence image preparation. | Retain in this package-stage capability as a shared package mechanism. Callers supply the workload binding; the helper does not choose a target. | Confirmed |
| `40-package/prepare-runtime-payload/assemble.mjs` | Safely writes validated runtime package mappings, wrappers, and a payload manifest. | Used by entity-smoke and core-server-persistence image preparation, over the lower-level workspace package implementation. | Retain in this package-stage capability as a shared payload-assembly mechanism. Do not duplicate it per image. | Confirmed |

### Boundary observed

This group supplies three different roles, despite every file containing
exports: one test-support module, two build-contract modules, one target
binding, and two reusable package mechanisms. The catalogue therefore remains
an index rather than a move list. No source code changed as part of this audit.

## Repository workspace-build audit

These seven modules total 930 lines. They are not seven copies of the same
check: five make up one reusable build foundation, while two serve distinct
repository-control capabilities. The distinction comes from their direct
callers and responsibilities, rather than their common folder.

| Module | Actual role | Lifecycle relationship evidenced by callers | Decision | Confidence |
| --- | --- | --- | --- | --- |
| `workspace-build/declarations.mjs` | Reads the workspace graph and derives an explicitly selected package closure, compiler paths, source files, and runtime package mappings. | Used by runnable-program build inputs, image preparation, package custody, and module-structure inspection. | Retain as the shared, read-only workspace-declaration foundation. It is genuine reuse, not duplicated policy. | Confirmed |
| `workspace-build/compile.mjs` | Invokes TypeScript once for an already selected workspace closure and returns bounded diagnostics. | Used by the runnable-program compiler, the workspace command adapter, and package-image qualification. | Retain as the shared compiler mechanism. Callers continue to own which project is selected and where output is published. | Confirmed |
| `workspace-build/runtime-packages.mjs` | Plans and writes validated CommonJS shims and declared JSON assets into a runtime payload. | Used by the current core-server, core-server-persistence, and entity-smoke image paths, plus the retained platform-shell image path. | Retain as a shared package-assembly mechanism. It prevents each image capability from implementing its own filesystem safety rules. | Confirmed |
| `workspace-build/script.mjs` | Converts a bounded command-line request into a selected workspace compile. | The repository's focused runtime-test and image-build commands invoke it for many independent packages. | Retain as the public command adapter for this foundation. It is an operation wrapper, not another check. | Confirmed |
| `workspace-build/project-selection.mjs` | Derives workspace roots for the older `--project-roots` image-build route without approving imports merely because they resolve. | Used by the workspace command adapter and retained platform-shell image preparation. | Retain as a narrow compatibility adapter within workspace build. Do not extend it to new routes; future work can retire it when that image route is retired. | Confirmed narrow scope |
| `workspace-build/check-inputs.mjs` | Reads supported npm check commands to report their actual source and installation inputs without running them. | Called by `scripts/repo/check-selection/workspace_context.py`. | Retain for now as a check-selection adapter, not as a general workspace-build mechanism. A future bounded relocation should move it with its sole owner, `check-selection`. | Confirmed ownership mismatch |
| `workspace-build/dependencies.mjs` | Scans literal imports across workspace source and reports undeclared, unresolved, or test-only runtime dependencies. | Imported only by `scripts/repo/module-structure/check.mjs`. | Retain for now as module-structure inspection support, not as a build helper. A future bounded relocation should move it with module structure and its tests. | Confirmed ownership mismatch |

### Boundary observed

`declarations`, `compile`, `runtime-packages`, `script`, and the limited
`project-selection` adapter form a coherent shared build foundation. They are
changed only when their common build contract changes, and focused callers can
prove those changes.

`check-inputs` and `dependencies` are different. The former supports test
selection; the latter supports a broad architecture scan. Their current folder
creates a misleading impression that every `workspace-build` change is a build
change. Their eventual moves should be small owner migrations, including their
direct caller and focused tests—not a rewrite of the workspace foundation.

The import scanner is particularly relevant to verification cost: it inspects
workspace source as part of the module-structure capability. Whether it runs
on a normal change, only when architecture inputs change, or as scheduled
hygiene is a selection-policy decision to audit separately. This audit changes
neither the scanner nor its scheduling.

## Remaining repository-control candidates

The last two structural candidates are not general helpers. They export
functions because their own focused fixtures need to exercise their rules, not
because other capabilities should import them freely.

| Module | Actual role and named risk | Direct callers and proof | Lifecycle relationship | Decision | Confidence |
| --- | --- | --- | --- | --- | --- |
| `scripts/repo/diagnostic-coverage/compatibility.mjs` | Protects the versioned diagnostic-catalogue reader contract. Its named risk is changing, deleting, or duplicating an existing diagnostic identity while retaining the same code-and-version address. | `export-catalogs.mjs` is the only production caller; its focused cases in `smoke-test.py` reject changed definition content, deletion, version replacement, and duplicate identity. | Local diagnostic-catalogue generation and verification, not product build or deployment. | Retain beside the diagnostic catalogue exporter as a narrow compatibility guard. It is not a cross-repository helper and must not move to `scripts/helpers/`. | Confirmed narrow scope |
| `scripts/repo/module-structure/check.mjs` | Implements the repository's public-index, configuration-access, module-boundary, and workspace-dependency scan. Its named risk is repository architecture drift that a normal capability proof cannot see. | `module-structure/script.sh` is its public operation; `smoke-test.mjs` imports its functions only for controlled fixtures. The selector's repository-contract tests bind that operation and its focused regression. | Retained architecture hygiene. The complete scan is manually selectable; its fixture regression remains the automatic proof when its own checker or fixtures change. | Retain as one owned module-structure capability. Do not split exported fixture functions into a shared helper library or restore the complete scan to ordinary commit/merge selection. | Confirmed |

## Milestone-three completion

All 34 catalogue candidates now have an audited owner, responsibility,
lifecycle relationship, caller evidence, and disposition:

| Group | Candidates | Disposition summary |
| --- | ---: | --- |
| Chat capability libraries | 2 | Retain in their existing `00.chat` capability homes. |
| Deployment shared and provider modules | 17 | Retain in their evidenced shared, stage-specific, narrow, or legacy homes; the mixed diagnostics module proceeds to the separate boundary-design milestone. |
| Lifecycle-local JavaScript modules | 6 | Retain as test support, build contract, target binding, or package mechanism; no shared move follows merely from exports. |
| Repository workspace-build modules | 7 | Retain the shared build foundation; record the two owner mismatches for later bounded relocation. |
| Repository-control modules | 2 | Retain with their own diagnostic-export and architecture-inspection capabilities. |
| **Total** | **34** | **No extraction, move, deletion, or new shared library is authorised by this audit.** |

This completes the helper audit. It has identified one genuine mixed-boundary
candidate—deployment-operation diagnostics—and two eventual folder ownership
mismatches. Those are deliberately separate from this milestone: the next
step is to design the diagnostics boundary before moving any code.

## Milestone-four design: deployment-operation diagnostics

This is a design record only. It does not move code, alter a report, change a
check, or add a compatibility wrapper.

### Current boundary and risk

`scripts/04.deploy/shared/deployment-operation-diagnostics.py` owns the
general `deploy/deployment-operation-diagnostic/v1` report: its base fields,
safe report writing, command-line record/validation route, and safe AWS and
CloudFormation failure classification. Its optional `task_failure` report
field is different: it is meaningful only for Core Server Persistence task
evidence, but the shared `validate` and `build_report` functions currently
call that target-specific validator directly.

The named risk is a future shared report change silently changing, accepting,
or rejecting Core Server Persistence task evidence—or a persistence change
needlessly forcing package and deployment-report callers through target-only
logic.

The tracked retained operation reports were inspected: none contains
`task_failure`. Current production callers also do not pass `task_failure` to
`build_report`; it exists in the general format only because the shared module
contains the target reader. This is evidence to remove the hidden dependency,
not authority to discard historical reports or task evidence.

### Direct consumer map

| Consumer group | Current use | Ownership after the designed split |
| --- | --- | --- |
| `safe-command-diagnostics.sh` and `provider-adapters/aws/ecr_publication.py` | Invoke the shared `record` command to retain a generic package failure report. | Shared report command, unchanged. |
| Core Server Persistence `create-change-set` and `transition-qualified-release` | Classify a named CloudFormation failure, then build and write a deploy report. | Shared report and CloudFormation classifier, unchanged. |
| `rehearse-isolated-database-restore` | Builds/writes a general run report; separately validates the persistence restore-verifier result. | General report calls remain shared; verifier-result reader moves to the target binding. |
| `collect-acceptance-evidence` | Validates a persistence restore-verifier result. | Target binding. |
| `rehearse-observability-readiness` | Selects a safe persistence controller checkpoint. | Target binding. |
| `rehearse-runtime-credential-lifecycle` | Selects controller checkpoints and merges bounded persistence task failures. | Target binding. |
| `run-administration` | Collects an administration task failure, then separately uses the generic runtime-diagnostic reader. | Task-failure collection moves to target binding; generic runtime-diagnostic reader stays shared. |
| `verify-candidate` | Collects a verification task failure from a bounded task-log response. | Target binding. |
| `run-migration` | Validates generic runtime and related diagnostic records only. | Shared diagnostic-record readers, unchanged. |

The current shared smoke test covers both groups. Existing focused caller proof
also includes the `verify-candidate` operation test. No caller outside the
Core Server Persistence runtime capability uses the persistence-only functions.

### Chosen interface

Use a caller-owned extension profile rather than changing or replacing the
general report schema.

The shared report capability will own only its base fields. It will accept an
explicit profile consisting of exact extension-field names and validators. Its
default profile has no extensions, so the shared command and ordinary report
callers remain unable to admit target evidence accidentally.

The Core Server Persistence binding will own a profile for the one extension:

```text
task_failure -> validate_persistence_task_failure
```

That binding will also own these target-only functions together:

- `validate_persistence_task_failure`;
- `collect_persistence_task_failure`;
- `validate_persistence_controller_checkpoint`; and
- `validate_verifier_result`.

The shared validator will no longer name `task_failure` or call any
persistence-specific function. The target binding will call the shared report
validator with its explicit profile when it needs to read a report containing
that extension. A generic report without target evidence remains valid through
the current shared public command.

This is preferable to simply deleting the field because it keeps a bounded
reader for any real Core Server Persistence report that contains task evidence,
without making every generic caller load the persistence contract. It is also
preferable to a new global diagnostics registry: the profile is a local
binding supplied at the real target boundary.

### Planned canonical home and migration order

The target binding's proposed home is:

```text
scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/
  core-server-persistence/deployment-diagnostics/
    binding.py
    tests/binding-test.py
```

This is a proposed M5 capability unit, not a created folder. It will require
approval before creating source files over the repository's 50-line limit.

M5 must proceed in this order:

1. Add the target binding and transfer the existing persistence-only fixture
   cases from the shared smoke test; do not duplicate them.
2. Add the explicit extension-profile seam to the shared report engine and
   prove its default profile rejects target-only fields.
3. Move all listed target callers together to the binding; retain the generic
   runtime-diagnostic calls at their current shared owner.
4. Transfer generic report, AWS/CloudFormation, and command-line cases to the
   shared test; transfer task-failure, controller-checkpoint, and verifier
   cases to the binding test.
5. Update the existing selector inputs and focused repository-contract proof
   to follow the two canonical owners, then remove the target-only functions
   from the shared module in the same slice.

### Proof and rollback

The focused proof set for M5 is deliberately the existing proof set divided by
responsibility, not a new suite:

- shared report/CLI and CloudFormation fixtures retain their current smoke
  coverage;
- transferred persistence fixtures prove extension admission, malformed task
  evidence rejection, bounded observation merge, controller checkpoint
  selection, and verifier-result rejection;
- `verify-candidate/operation-test.py` proves the target binding through a
  real caller; and
- the existing `deployment-operation-diagnostics-regression` proves the
  connected catalogue and declared controller inputs after the canonical paths
  are updated.

Before removal, a source search must show that no production caller imports
the old target functions. A generic report test must reject a supplied
`task_failure` without the target profile, while the target binding test must
accept only its validated form.

If the migration fails before acceptance, retain the current shared module and
do not publish a partial path move. If an accepted M5 commit needs reversal,
revert that bounded commit; do not rewrite retained reports, relax validation,
or introduce a compatibility wrapper without a concrete remaining caller.

## Milestone-five migration: Core Server Persistence deployment diagnostics

The proposed capability is now the canonical implementation at
`scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/deployment-diagnostics/`.

`binding.py` owns the four persistence-only readers: task-failure validation,
task-failure collection, controller-checkpoint selection, and restore-verifier
result validation. The six mapped target callers load that binding for these
functions. `rehearse-isolated-database-restore` and `run-administration` keep
their genuinely generic report and diagnostic-record calls in the shared
module.

The shared module now knows only the base deployment report. Its default
validator rejects `task_failure`; the target binding supplies that one field's
validator explicitly through `report_extension_validators()`. This is a local
binding, not a registry or a compatibility path.

The old mixed smoke fixture was divided without adding a selector entry:

- the retained shared test proves generic reports, CloudFormation handling,
  command-line behaviour, and wrapper dispatch;
- `deployment-diagnostics/tests/binding-test.py` proves malformed evidence
  rejection, bounded task-log merge, checkpoint selection, verifier envelopes,
  and the affected direct controllers; and
- the existing `deployment-operation-diagnostics-regression` still runs both,
  with the binding and its test declared as direct inputs.

Focused proof passed for the shared wrapper, target binding test,
`verify-candidate/operation-test.py`, and the selector's repository-contract
test. A source audit confirms no persistence-only function definition remains
in the shared module and all six mapped callers name the target binding.

The retained risk is limited: third-party or untracked historical reports with
`task_failure` must be read through this Core Server Persistence binding, not
the generic command-line validator. No tracked retained report has that field,
and no compatibility wrapper was added.

## Admission standard recorded after the first bounded migration

The diagnostics migration showed that an executable file cannot be placed or
selected safely from its filename or legacy path alone. The new harness
standard, `.agentic/01.harness/standards/script-admission.md`, records the
small decision needed before a future script is created: its role, owner and
capability, purpose, direct consumer, named risk, proof lane, reuse decision,
and why an existing capability cannot own it unchanged.

It does not create another inventory or scheduling mechanism. The existing
catalogue remains structural evidence, this audit remains the human decision
ledger, and the existing selector remains the only ordinary selection owner.
Until the owner/domain/capability folder migration reaches a relevant area,
the admission record requires a conservative existing-home decision or an
approved proposal for a new capability folder.
