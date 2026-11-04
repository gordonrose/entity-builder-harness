<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l018
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/files.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L018 — packages/core/src/files

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/files -->

## What you will understand

Core file helpers represent and operate on file-related data through supplied storage behavior; they do not choose an AWS bucket.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a local file attribute rejection with a storage callback throwing after invocation. Ask what is known about progress, and what cannot be inferred about stored bytes.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** File validation, copying and storage operations already existed. Raw failures did not always identify whether local validation, projection or a provider call had failed.

**After:** Owned definitions and optional observers distinguish local predicates, preparation and external invocation boundaries with bounded source evidence.

**Why this was needed:** A rejected file attribute and an uncertain storage write have different safe next actions. Logging content, filenames or provider exception prose is not required to distinguish them.

This directory contains `definition`, `barrel-or-implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/files/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/files/diagnostics.ts) · **Snapshot:** added (absent from baseline); 65 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.files.validation-rejected`, `core.files.operation-rejected`, `core.files.boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `validationOperations`, `fields`, `coreFileValidationDiagnostic`, `coreFileOperationDiagnostic`, `coreFileBoundaryDiagnostic`, `coreFileDiagnosticDefinitions`, `CoreFileValidationDetail`, `CoreFileOperationDetail`, `CoreFileBoundaryDetail`, `CoreFileDiagnosticContext`, `CoreFileDiagnosticOptions`, `CoreFileDiagnosticEvidence` (4 more in source).

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=32124370b9dae859fa75f50c550a1ba8c16889e0038a54030dbd266d71f600a6 -->

<!-- course-file: packages/core/src/files/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/files/index.ts) · **Snapshot:** modified existing file; 304 added / 210 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports file capabilities at this layer.

**Before:** File validation, copying and storage operations already existed. Raw failures did not always identify whether local validation, projection or a provider call had failed. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `fileName`, `fileContentType`, `fileSizeBytes`, `fileChecksumAlgorithm`, `fileChecksumValue`, `fileChecksum`, `fileStorageKey` (20 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Existing Files predicates retain exact order, coercion, closed scan/access membership, checksum forwarding and first rejected storage-segment visit ordinal. Custom aggregate truthiness without a rejecting callback has predicate-rejected with no fabricated position.

**Why:** A rejected file attribute and an uncertain storage write have different safe next actions. Logging content, filenames or provider exception prose is not required to distinguish them.

Changed declaration anchors: `fileName`, `fileContentType`, `fileSizeBytes`, `fileChecksumAlgorithm`, `fileChecksumValue`, `fileChecksum`, `fileStorageKey`, `fileMetadata`, `fileScanResult`, `fileStorageRef`, `fileRetentionPolicy`, `fileObject` (15 more in source).

New declarations within this existing file: `copyStoredFile`, `projectPutFileInput`.

Added import edges: `./observations`, `./diagnostics`.

Added named test anchors: `empty-segment`; `dot-segment`; `parent-segment`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=d9b9dceb70812062395835f3b01fdfb5fedb7efc88fb8bb39c7f07ddb61ca9ff after=ede565db39e000a47d6c230010cbcc0b3a0968402aac963d54ace351e8553c31 -->

<!-- course-file: packages/core/src/files/observations.ts -->

### observations.ts

[Open current source](../../../../../packages/core/src/files/observations.ts) · **Snapshot:** added (absent from baseline); 92 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Existing Files predicates retain exact order, coercion, closed scan/access membership, checksum forwarding and first rejected storage-segment visit ordinal. Custom aggregate truthiness without a rejecting callback has predicate-rejected with no fabricated position. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `selectCoreFileDiagnosticEvidence`, `nativeThen`, `isolate`, `observeCoreFileDiagnostic`, `selectedFileCompanions`, `FileObservation`.

Added import edges: `../diagnostic-catalog`, `../diagnostics/index`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=6cb5cb5b9d6c81d2bdc06172f95cffd9438cf611f9d2e046192b785aa5f1c061 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which observation would justify fixing input, and which requires investigating an uncertain storage effect?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** These changes are not a new upload security, retention or storage durability policy. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/files) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
