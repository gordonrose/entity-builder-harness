<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l098
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L098 — scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image -->

## What you will understand

Build and image tooling turns source into a runnable artifact. The payload is the compiled files and dependencies actually included in that artifact.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Remove either core-server diagnostic module from an assembled test payload. The import-closure check must reject it with its fixed code. A Dockerfile mentioning a source file is not, by itself, proof that the resulting image runs.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work.

**After:** Packaging includes required diagnostic modules and checks actual import closure. Existing registered checks are reused with source identity, and omission counterexamples prove missing modules are caught.

**Why this was needed:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

This directory contains `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs -->

### prepare-runtime.mjs

[Open current source](../../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs) · **Snapshot:** modified existing file; 29 added / 6 removed lines. These are textual counts, not a count of new features.

**What it does:** Add CommonJS workspace shims and executable wrappers to the persistence candidate payload.

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `compiledRoot`, `preparationPhase`, `preparationLocation`, `writesStarted`, `writePackageShim` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Expose the public security package's actual Core security dependency in all three prepared runtime payloads; derive missing core exports from compiled imports and reject them before image construction. B10 preserves these exact physical owners and bounds image-script child execution; direct preparation/verification CLI native failures remain separately reviewable.

**Why:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

Changed declaration anchors: `compiledRoot`, `preparationPhase`, `preparationLocation`, `writesStarted`, `writePackageShim`.

New declarations within this existing file: `preparationPhase`, `preparationLocation`, `writesStarted`.

Declarations removed or relocated: `coreModules`, `packages`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `bootstrap-payload-regression`, `persistence-payload-regression`, `shell-package-source`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=fadd19cca8523065d86fbc7489c7886acc137294fc68e06d1fca56a6b5f0094f after=91a5dd6eb3aed7eea8b552117bfe01455fed00c73302733c4656c9b9e372e7ea -->

<!-- course-file: scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh -->

### script.sh

[Open current source](../../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh) · **Snapshot:** modified existing file; 4 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile and build only the local PostgreSQL-backed core-server candidate image; it never publishes or deploys.

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Retain exact persistence build and runtime payload requirements, original role/setup/program predicates and cleanup precedence. Fixed child codes identify TLS/setup/resources/HTTP/digest/receiver/removal and each retained operation separately; failed observations never prove operation nonacceptance.

**Why:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

Owning registered proof: `package-custody-regression`, `persistence-payload-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f6ff3fbb1f9c809a6c99eadfae37bda2ab95c76f91344125f09428b9bd6b6a44 after=140e3e9a73836983c6904c2c16cea242d773f701af900c5357324274c31f20e8 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why could TypeScript compilation pass while the deployed image fails at startup?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local image qualification is not publication, target alignment or live acceptance. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L097 scripts/04.deploy/lifecycle/40-package/build-core-server-image](097-lifecycle-40-package-build-core-server-image.md) · [L099 scripts/04.deploy/lifecycle/40-package/package-custody-receipt](099-lifecycle-40-package-package-custody-receipt.md) · [L101 scripts/04.deploy/lifecycle/40-package/qualify-retained-persistence-rollback-image](101-lifecycle-40-package-qualify-retained-persistence-rollback-image.md) · [L102 scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image](102-lifecycle-40-package-smoke-test-core-server-image.md) · [L103 scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image](103-lifecycle-40-package-smoke-test-core-server-persistence-image.md) · [L109 scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract](109-lifecycle-40-package-validate-delivery-access-contract.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
