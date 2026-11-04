<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l097
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/40-package/build-core-server-image.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L097 — scripts/04.deploy/lifecycle/40-package/build-core-server-image

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/40-package/build-core-server-image -->

## What you will understand

Build and image tooling turns source into a runnable artifact. The payload is the compiled files and dependencies actually included in that artifact.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **4 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Remove either core-server diagnostic module from an assembled test payload. The import-closure check must reject it with its fixed code. A Dockerfile mentioning a source file is not, by itself, proof that the resulting image runs.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work.

**After:** Packaging includes required diagnostic modules and checks actual import closure. Existing registered checks are reused with source identity, and omission counterexamples prove missing modules are caught.

**Why this was needed:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

This directory contains `implementation`, `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs -->

### prepare-runtime.mjs

[Open current source](../../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs) · **Snapshot:** modified existing file; 22 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Add only the generated CommonJS package shims required by the compiled Kanbien core-server payload.

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `compiledRoot`, `preparationPhase`, `preparationLocation`, `writesStarted`, `writePackageShim` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Expose the public security package's actual Core security dependency in all three prepared runtime payloads; derive missing core exports from compiled imports and reject them before image construction. B10 preserves these exact physical owners and bounds image-script child execution; direct preparation/verification CLI native failures remain separately reviewable.

**Why:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

Changed declaration anchors: `compiledRoot`, `preparationPhase`, `preparationLocation`, `writesStarted`, `writePackageShim`.

New declarations within this existing file: `preparationPhase`, `preparationLocation`, `writesStarted`.

Declarations removed or relocated: `coreModules`, `packages`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `bootstrap-payload-regression`, `persistence-payload-regression`, `shell-package-source`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6bb01f75b65f6729286ee42629f584f4a7ef432b83146178b00f6d4451cce5db after=397d43925c1226f258cc2856c5e4f26d10f83cce4359eb21700a16e7f14bfdee -->

<!-- course-file: scripts/04.deploy/lifecycle/40-package/build-core-server-image/runtime-preparation-diagnostic-test.py -->

### runtime-preparation-diagnostic-test.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-image/runtime-preparation-diagnostic-test.py) · **Snapshot:** added (absent from baseline); 149 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for assembled image and payload safety.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. The newly visible named cases below provide concrete reading anchors. Connected proving scope (the review spans related files, not only this test): Expose the public security package's actual Core security dependency in all three prepared runtime payloads; derive missing core exports from compiled imports and reject them before image construction. B10 preserves these exact physical owners and bounds image-script child execution; direct preparation/verification CLI native failures remain separately reviewable.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Added import edges: `, (compiled / `.

Added named test anchors: `test_actual_argument_and_presence_rejections_before_writes`; `test_actual_directory_and_write_failures_preserve_partial_effect`; `test_successful_actual_preparation_and_late_wrapper_failure`; `test_actual_payload_cli_and_native_read_boundaries`.

Owning registered proof: `bootstrap-payload-regression`, `persistence-payload-regression`, `shell-package-source`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=9b4f55d8afc8fa4fe413cc5e6818a666de8e27dcdb77d37d168140c9d4a03ffc -->

<!-- course-file: scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh -->

### script.sh

[Open current source](../../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh) · **Snapshot:** modified existing file; 10 added / 9 removed lines. These are textual counts, not a count of new features.

**What it does:** Qualify the core-server compiled payload, then build its local-only candidate image without publishing or selecting a target.

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Existing local compiler/preparation/validation/Docker child boundaries use fixed concern/stage summaries and preserve exact child status and fail-stop ordering. No child output is disclosed.

**Why:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

Owning registered proof: `package-custody-regression`, `bootstrap-payload-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ff93bc6dfc355eba2f07ac042376bf2ea40371e8daf650d38226c8e2bbb2c644 after=7f040575557148fa17990a017940e541ff2129d7bc65943314b69b3562f9fe8a -->

<!-- course-file: scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py -->

### verify-payload.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py) · **Snapshot:** modified existing file; 42 added / 6 removed lines. These are textual counts, not a count of new features.

**What it does:** Fail closed when a compiled core-server package payload disagrees with its declared image or dependency boundary.

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Expose the public security package's actual Core security dependency in all three prepared runtime payloads; derive missing core exports from compiled imports and reject them before image construction. B10 preserves these exact physical owners and bounds image-script child execution; direct preparation/verification CLI native failures remain separately reviewable.

**Why:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

Current reading anchors (not all are new): `__init__`, `error`, `load_document`, `validate_source_contracts`, `validate_docker_boundary`, `validate_payload`, `main`.

Owning registered proof: `bootstrap-payload-regression`, `persistence-payload-regression`, `shell-package-source`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=d3b6f6fbf71215025c6685de7cda519f03cdd5387fea4dba7dbd751e212ac7f9 after=932b20900f35d7b0d2b22ad20d00394a98516d9dcda918469efc64fb5bd00acc -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why could TypeScript compilation pass while the deployed image fails at startup?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local image qualification is not publication, target alignment or live acceptance. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-image) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L098 scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image](098-lifecycle-40-package-build-core-server-persistence-image.md) · [L099 scripts/04.deploy/lifecycle/40-package/package-custody-receipt](099-lifecycle-40-package-package-custody-receipt.md) · [L101 scripts/04.deploy/lifecycle/40-package/qualify-retained-persistence-rollback-image](101-lifecycle-40-package-qualify-retained-persistence-rollback-image.md) · [L102 scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image](102-lifecycle-40-package-smoke-test-core-server-image.md) · [L103 scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image](103-lifecycle-40-package-smoke-test-core-server-persistence-image.md) · [L109 scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract](109-lifecycle-40-package-validate-delivery-access-contract.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 4 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
