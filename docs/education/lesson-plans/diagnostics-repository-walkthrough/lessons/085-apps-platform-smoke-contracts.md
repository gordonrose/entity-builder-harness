<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l085
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder apps/platform-smoke/contracts.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L085 — apps/platform-smoke/contracts

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: apps/platform-smoke/contracts -->

## What you will understand

Platform-smoke is a real example app that mounts routes/jobs and exercises persistence-backed work-item acceptance.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A work-item acceptance input fails an existing feature predicate. Preserve the business result; attach the app-owned safe reason. If the writer itself throws, retain selected source evidence separately rather than replacing it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The feature and its endpoints already existed. App-specific configuration and accepted-payload failures could be hidden behind generic platform errors.

**After:** The app declares its own diagnostic catalog and payload/configuration/acceptance observations; Platform and targets select and deliver them. Existing supported acceptance behavior remains.

**Why this was needed:** Only the feature can say what an invalid accepted work item means. Generic HTTP or database code should not own the app vocabulary.

This directory contains `catalog` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: apps/platform-smoke/contracts/diagnostics.v1.json -->

### diagnostics.v1.json

[Open current source](../../../../../apps/platform-smoke/contracts/diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 187 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected the sample app owns its feature meaning contract for non-TypeScript readers, including 5 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `platform-smoke.work-item-not-accepted` v1, `platform-smoke.attribute-invalid` v1, `platform-smoke.configuration-invalid` v1, `platform-smoke.accepted-payload-invalid` v1, `platform-smoke.accepted-payload-not-observed` v1.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=1edfd9d8d3c52675d5b3e4f6452fe555a59bdad1620f776a4573c6835c65973b -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which part of this explanation belongs to the app, and which belongs to Persistence?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** An acceptance diagnostic does not independently prove that a database commit happened. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../apps/platform-smoke/contracts) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L084 apps/platform-smoke](084-apps-platform-smoke.md) · [L086 apps/platform-smoke/src](086-apps-platform-smoke-src.md) · [L088 apps/platform-smoke/tests](088-apps-platform-smoke-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
