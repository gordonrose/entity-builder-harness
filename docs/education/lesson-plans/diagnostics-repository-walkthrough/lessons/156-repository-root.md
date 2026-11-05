<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l156
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder ..
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L156 — Repository root

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: . -->

## What you will understand

The harness tells agents what complete work requires, who owns it, which compatibility boundaries to preserve and what proof must be recorded.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A change adds a new integration call. Locate the actual failure observation, upstream definition, adapter mapping, selected catalog, delivery reader and tests before calling the change complete. Do not start the expensive full gate while a required consumer is still being edited.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Existing governance required safety and verification, but did not make connected diagnostic producers, consumers and source-matched review explicit enough.

**After:** The shared workflow/standard requires bounded responsibility and consumer inventories, upstream ownership, safe detail, source review and stopped inputs before expensive final verification.

**Why this was needed:** A schema with no producer or a producer with no reader is incomplete. More written instructions alone cannot establish compliance, so executable checks complement human review.

This directory contains `documentation`, `dependency` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: AGENTS.md -->

### AGENTS.md

[Open current source](../../../../../AGENTS.md) · **Snapshot:** modified existing file; 4 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Routes agents to the shared diagnostic workflow.

**Before:** The compact entry router did not name that workflow.

**After:** Adds the coding-work pointer; the detailed rules stay in their owning workflow, not in this small router.

**Why:** Future sessions need to encounter the standard without turning AGENTS into a second implementation manual.

Reading anchors: `AGENTS.md`; `Purpose`; `Before Acting`; `llm-workbench`; `Operating Layers`; `Source of Truth`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=b501345e152f831614b0f3c618f58c4f105196b830a3dbcd990da6a90a98b5ec after=011224843510a902b8602b33596b1bfba926ceeab5986a0269e6dbcbc541628d -->

<!-- course-file: package-lock.json -->

### package-lock.json

[Open current source](../../../../../package-lock.json) · **Snapshot:** modified existing file; 2 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Records workspace dependency edges, not a new SDK installation.

**Before:** The two adapter workspace entries did not declare these added internal edges.

**After:** Adds CloudWatch → platform-observability and PostgreSQL → platform-security edges. No new OpenTelemetry or AWS SDK is introduced by this diff.

**Why:** The package graph must reflect the upstream code actually imported by those adapters.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=f04ecd0bd3191ce6c2d37650aea6885de3ee4519d923c26d748da90160d74bc8 after=7f5d040377f20dcd681308878ec4b440008c538c8c2a73491cdde4e8db5d220c -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which requirements can a script check, and which need architectural judgment about what the operation actually knows?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Governance cannot guarantee that an agent never makes mistakes or that every possible future failure is already covered. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../AGENTS.md) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L171 bin](171-bin.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
