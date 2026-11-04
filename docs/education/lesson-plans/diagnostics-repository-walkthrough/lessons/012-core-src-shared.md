<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l012
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/shared.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L012 — packages/core/src/shared

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/shared -->

## What you will understand

Shared primitives give other Core modules a small common vocabulary for success, failure and identifier validation.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Reject an identifier at its existing format check. Report the logical field and observed reason; keep the supplied identifier private. Contrast that with an injected getter throwing before the format check.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** A failed identifier or shared constructor could throw an ordinary error without a reusable record of the exact primitive predicate.

**After:** The existing guards gain closed observations and compatible error evidence, while primitive grammar, first failure and original thrown outcomes remain important.

**Why this was needed:** Repeatedly inventing identifier diagnostics in each adapter would couple basic rules to deployment choices and allow meanings to drift.

This directory contains `definition`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/shared/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/shared/diagnostics.ts) · **Snapshot:** added (absent from baseline); 50 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.shared.date-invalid`, `core.shared.date-normalization-threw`, `core.shared.json-invalid`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `classification`, `coreDateDiagnostic`, `coreDateNormalizationDiagnostic`, `coreJsonDiagnostic`, `coreSharedDiagnosticDefinitions`, `attachCoreDiagnosticRecord`, `coreDateRecord`, `coreDateNormalizationRecord`, `coreJsonRecord`.

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=d7da5d3f3917883615aba58b62778bdcfe660bfa5168c148b1051a45201244de -->

<!-- course-file: packages/core/src/shared/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/shared/index.ts) · **Snapshot:** modified existing file; 46 added / 9 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports shared results and identifiers at this layer.

**Before:** A failed identifier or shared constructor could throw an ordinary error without a reusable record of the exact primitive predicate. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `CoreError`, `copyJsonValue`, `isoDateTime`, `isoDateTimeFromDate`, `nativeJsonArrayMap`, `applyJsonArrayMap`, `mapWithJsonPosition` (2 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Preserve supplied diagnosticRecord through existing error factories and add the optional validation projection; CoreError declares bounded related observations, with affected persistence factories validating them against explicitly supplied definitions. Shared date/JSON guards now retain value-free positional evidence; overridden map semantics and unavailable callback locations are tested without replacing existing errors.

**Why:** Repeatedly inventing identifier diagnostics in each adapter would couple basic rules to deployment choices and allow meanings to drift.

Changed declaration anchors: `CoreError`, `copyJsonValue`, `isoDateTime`, `isoDateTimeFromDate`, `nativeJsonArrayMap`, `applyJsonArrayMap`, `mapWithJsonPosition`, `jsonCopyFailure`, `copyJsonValueInternal`.

New declarations within this existing file: `nativeJsonArrayMap`, `applyJsonArrayMap`, `mapWithJsonPosition`, `jsonCopyFailure`.

Added import edges: `./diagnostics`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=c488153546e4155103a13c8374de24a54f541572d0d95c720143707e0c6bd9bd after=dccf47177790f5d86fdfc611478b81603cffea22256bc44f2b78e7411ac04949 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Can an unreadable identifier honestly be labelled malformed?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No upward imports into Platform or deployment are needed to describe Core predicates. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/shared) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
