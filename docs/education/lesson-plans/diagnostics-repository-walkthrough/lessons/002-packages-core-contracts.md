<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l002
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/contracts.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L002 — packages/core/contracts

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/contracts -->

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

This directory contains `catalog` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/contracts/diagnostics.v1.json -->

### diagnostics.v1.json

[Open current source](../../../../../packages/core/contracts/diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 2158 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected the diagnostic language contract for non-TypeScript readers, including 32 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `core.config.primitive-invalid` v1, `core.config.source-threw` v1, `core.config.declaration-invalid` v1, `core.config.relationship-declaration-invalid` v1, `core.shared.date-invalid` v1; 27 more definitions are in the export.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=2f7e1ce7faa198e5a7893205f727f5b6bcc8721fae51c42596e9bd9cb2e11f70 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must a schema-valid record from an arbitrary caller not automatically become trusted evidence about a database call?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Shape validation establishes admissible data, not truth, exhaustiveness or remote delivery. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/contracts) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L001 packages/core](001-packages-core.md) · [L003 packages/core/src](003-packages-core-src.md) · [L006 packages/core/tests](006-packages-core-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
