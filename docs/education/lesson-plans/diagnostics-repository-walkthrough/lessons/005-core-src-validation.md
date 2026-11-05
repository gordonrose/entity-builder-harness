<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l005
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/validation.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L005 — packages/core/src/validation

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/validation -->

## What you will understand

Core defines provider-independent facts and their allowed shapes. It must remain usable without a server, AWS account or particular database.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a raw exception with an object carrying code, definitionVersion, schema and detail. Add an undeclared detail property: parsing must reject that record. A valid shape still does not prove that the claimed event happened; the producer must have observed it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The baseline already had diagnostic classifications and monitoring concepts. Those useful abstractions did not, by themselves, give every capability a closed, versioned record that a reader could validate.

**After:** Definitions declare a stable code, version, classification and permitted detail. Constructors copy and validate records; selectors accept only explicitly selected evidence. Shared helpers bound related evidence to eight records.

**Why this was needed:** A description written by an agent is not a runtime contract. Code-owned definitions let producers and readers agree without interpreting prose or trusting an arbitrary error object.

This directory contains `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/validation/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/validation/index.ts) · **Snapshot:** modified existing file; 8 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports the diagnostic language at this layer.

**Before:** The baseline already had diagnostic classifications and monitoring concepts. Those useful abstractions did not, by themselves, give every capability a closed, versioned record that a reader could validate. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `Validator`, `validationDiagnostic`, `invalidResult`, `invalidResult` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Preserve supplied diagnosticRecord through existing error factories and add the optional validation projection; CoreError declares bounded related observations, with affected persistence factories validating them against explicitly supplied definitions. Shared date/JSON guards now retain value-free positional evidence; overridden map semantics and unavailable callback locations are tested without replacing existing errors.

**Why:** A description written by an agent is not a runtime contract. Code-owned definitions let producers and readers agree without interpreting prose or trusting an arbitrary error object.

Changed declaration anchors: `Validator`, `validationDiagnostic`, `invalidResult`, `invalidResult`.

New declarations within this existing file: `validationDiagnostic`.

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=43ee5d75ad3035e66a719c0cbbeeed66051427a31f34dfaf6f8c4d659a688129 after=9be4026d135bf73038704e54618e8eb685f82dfc77f7b5432ad1ff3649927b5f -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must a schema-valid record from an arbitrary caller not automatically become trusted evidence about a database call?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Shape validation establishes admissible data, not truth, exhaustiveness or remote delivery. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/validation) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
