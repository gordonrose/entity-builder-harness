<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l019
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/i18n.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L019 — packages/core/src/i18n

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/i18n -->

## What you will understand

Internationalization prepares code to handle languages; localization supplies locale-specific formatting or messages.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Let a formatter throw after its inputs pass existing validation. Preserve the original throw and report the formatting boundary, not a fabricated missing translation. Contrast that with a declaration rejected before formatting.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Locale/message/format constructors and callbacks already existed. Validation and formatting failures could lose their precise location or source evidence.

**After:** Closed capability records identify actual locale, message and formatting predicates and callback boundaries without including translated text or arguments.

**Why this was needed:** An agent needs to separate a bad locale declaration from a formatter failure, and must not expose customer text while doing it.

This directory contains `definition`, `barrel-or-implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/i18n/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/i18n/diagnostics.ts) · **Snapshot:** added (absent from baseline); 56 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.i18n.validation-rejected`, `core.i18n.selection-observed`, `core.i18n.boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `validationOperations`, `validationFields`, `ordinal`, `coreI18nValidationDiagnostic`, `coreI18nSelectionDiagnostic`, `coreI18nBoundaryDiagnostic`, `coreI18nDiagnosticDefinitions`, `CoreI18nValidationDetail`, `CoreI18nSelectionDetail`, `CoreI18nBoundaryDetail`, `CoreI18nDiagnosticContext`, `CoreI18nDiagnosticOptions` (4 more in source).

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=3669d26e4270abc49a0483044540872bb27230cdfbe43d500698b026a92c3bde -->

<!-- course-file: packages/core/src/i18n/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/i18n/index.ts) · **Snapshot:** modified existing file; 144 added / 47 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports internationalization and localization at this layer.

**Before:** Locale/message/format constructors and callbacks already existed. Validation and formatting failures could lose their precise location or source evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `MessageTranslator`, `localeTag`, `messageTemplate`, `messageTemplateAt`, `translationCatalog`, `safeTranslationParams`, `defaultMessageTranslator` (5 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Closed existing locale/template/catalog/unsafe-or-missing-parameter predicates retain syntax-only acceptance, eager entries before validation, original final missing sentinel and last missing callback ordinal. Selection records distinguish requested/fallback/default source, actual candidate ordinal and captured miss counts before rendering, never successful translation.

**Why:** An agent needs to separate a bad locale declaration from a formatter failure, and must not expose customer text while doing it.

Changed declaration anchors: `MessageTranslator`, `localeTag`, `messageTemplate`, `messageTemplateAt`, `translationCatalog`, `safeTranslationParams`, `defaultMessageTranslator`, `catalogMessageTranslator`, `interpolateMessageTemplate`, `i18nError`, `translateDefaultMessage`, `translatedParamKeys`.

New declarations within this existing file: `messageTemplateAt`.

Added import edges: `./observations`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=1cefbddbf6643a36938afe992f504f02e9549bd8011fcc7e99fd60bb51b6693e after=ba2290086c56b1324d471338ecf8a87163bb3e8143ef4be5e4bac95b10802b63 -->

<!-- course-file: packages/core/src/i18n/observations.ts -->

### observations.ts

[Open current source](../../../../../packages/core/src/i18n/observations.ts) · **Snapshot:** added (absent from baseline); 67 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Closed existing locale/template/catalog/unsafe-or-missing-parameter predicates retain syntax-only acceptance, eager entries before validation, original final missing sentinel and last missing callback ordinal. Selection records distinguish requested/fallback/default source, actual candidate ordinal and captured miss counts before rendering, never successful translation. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `nativeThen`, `observe`, `I18nObservation`.

Added import edges: `../diagnostic-catalog`, `../diagnostics/index`, `../shared/diagnostics`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=f45ca540413f459b6f8a227447293e79837bf7212f5fa91c7ccb8c507b77f480 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why should translated message content not be used as a diagnostic code or metric label?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No new language catalog, translation backend or locale acceptance policy is implied. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/i18n) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
