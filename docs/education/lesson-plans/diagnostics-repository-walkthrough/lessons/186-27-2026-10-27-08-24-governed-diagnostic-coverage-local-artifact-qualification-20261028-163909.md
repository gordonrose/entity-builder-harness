<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l186
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L186 — commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909 -->

## What you will understand

Plans, decisions and session records preserve why work was done and what evidence actually exists. They are not application runtime.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Read the retained failed full-gate attempt alongside the corrected passing run. Explain why the failure stays a failure, even though later source and evidence passed. A timestamped image record is not proof of today's live deployment.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The baseline did not contain this project's new plan, decisions or qualification records. Historical observability implementation and older session records already existed elsewhere.

**After:** The record captures scope, approvals, failed attempts, corrections, timings, local proof and explicit deferrals. Image records describe particular observed artifacts, not every future build.

**Why this was needed:** An agent returning later needs to distinguish a passed check from a planned check, and a user-approved deferral from a silently omitted requirement.

This directory contains `receipt` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/core-image.json -->

### core-image.json

[Open current source](../../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/core-image.json) · **Snapshot:** added (absent from baseline); 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Historical local image-qualification record.

**Before:** This dated image record did not exist in the baseline.

**After:** Preserves the observed qualification result for the named image at that point in the project. Inspect schema, status and source/artifact identity before interpreting it.

**Why:** It separates evidence about a particular local artifact from plans, later source changes and live deployment proof.

Proving boundary: source/document consistency and the actual evidence referenced by this record. Reading a plan or finding a valid metadata header is not runtime proof.

<!-- course-source-sha256: before=absent after=e232eeacb7c68ab4561e4a9d188ec15f799d3582e741a515b7052b12dd38c2cd -->

<!-- course-file: commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/persistence-image.json -->

### persistence-image.json

[Open current source](../../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/persistence-image.json) · **Snapshot:** added (absent from baseline); 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Historical local image-qualification record.

**Before:** This dated image record did not exist in the baseline.

**After:** Preserves the observed qualification result for the named image at that point in the project. Inspect schema, status and source/artifact identity before interpreting it.

**Why:** It separates evidence about a particular local artifact from plans, later source changes and live deployment proof.

Proving boundary: source/document consistency and the actual evidence referenced by this record. Reading a plan or finding a valid metadata header is not runtime proof.

<!-- course-source-sha256: before=absent after=7efec7e70115adf9ae35e4bc705e1b982be60e13304c51fc46a68d35f167e0bb -->

<!-- course-file: commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/shell-image.json -->

### shell-image.json

[Open current source](../../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909/shell-image.json) · **Snapshot:** added (absent from baseline); 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Historical local image-qualification record.

**Before:** This dated image record did not exist in the baseline.

**After:** Preserves the observed qualification result for the named image at that point in the project. Inspect schema, status and source/artifact identity before interpreting it.

**Why:** It separates evidence about a particular local artifact from plans, later source changes and live deployment proof.

Proving boundary: source/document consistency and the actual evidence referenced by this record. Reading a plan or finding a valid metadata header is not runtime proof.

<!-- course-source-sha256: before=absent after=c4fbeddc3ee41238fdf839ce0c354784624c343f446b649eea2c41727b1bb3c8 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must a newer success not rewrite the historical failed attempt as a success?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Raw log or provider identities are not copied into this course; follow local source links when needed. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage/local-artifact-qualification-20261028-163909) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L185 commitLogs/2026/oct/27/2026-10-27-08-24-governed-diagnostic-coverage](185-oct-27-2026-10-27-08-24-governed-diagnostic-coverage.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
