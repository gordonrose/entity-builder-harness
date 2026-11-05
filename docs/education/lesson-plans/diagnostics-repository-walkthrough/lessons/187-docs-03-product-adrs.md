<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l187
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder docs/03.product/adrs.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L187 — docs/03.product/adrs

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: docs/03.product/adrs -->

## What you will understand

Plans, decisions and session records preserve why work was done and what evidence actually exists. They are not application runtime.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Read the retained failed full-gate attempt alongside the corrected passing run. Explain why the failure stays a failure, even though later source and evidence passed. A timestamped image record is not proof of today's live deployment.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The baseline did not contain this project's new plan, decisions or qualification records. Historical observability implementation and older session records already existed elsewhere.

**After:** The record captures scope, approvals, failed attempts, corrections, timings, local proof and explicit deferrals. Image records describe particular observed artifacts, not every future build.

**Why this was needed:** An agent returning later needs to distinguish a passed check from a planned check, and a user-approved deferral from a silently omitted requirement.

This directory contains `documentation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: docs/03.product/adrs/0043-own-diagnostic-contracts-in-runtime-code.md -->

### 0043-own-diagnostic-contracts-in-runtime-code.md

[Open current source](../../../../03.product/adrs/0043-own-diagnostic-contracts-in-runtime-code.md) · **Snapshot:** added (absent from baseline); 109 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Records the ownership decision.

**Before:** The diagnostic ownership decision was not written as this ADR.

**After:** Places meaning in upstream runtime packages and generated reader contracts downstream, while the harness governs adoption.

**Why:** Future refactors need the reasoning, not only a list of files that happened to change.

Reading anchors: `ADR 0043 Own diagnostic contracts in runtime code`; `Status`; `Context`; `Decision`; `Consequences`.

Proving boundary: source/document consistency and the actual evidence referenced by this record. Reading a plan or finding a valid metadata header is not runtime proof.

<!-- course-source-sha256: before=absent after=7eea7a1f77a76ae3fb131ef78eef06590964266ed9f9cd32543d7c4be53dd616 -->

<!-- course-file: docs/03.product/adrs/README.md -->

### README.md

[Open current source](../../../../03.product/adrs/README.md) · **Snapshot:** modified existing file; 4 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for history, decisions and qualification records; read the sections `03.product ADRs`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `03.product ADRs`.

Proving boundary: source/document consistency and the actual evidence referenced by this record. Reading a plan or finding a valid metadata header is not runtime proof.

<!-- course-source-sha256: before=4a1c3b56fc01a8abdc5336e1066eecedbe371ff2ff2395062c423545df19083e after=eae312b0ef52a329bdb6e912df1870c73af1ac7c5c011000b4e19eaddda9b674 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must a newer success not rewrite the historical failed attempt as a success?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Raw log or provider identities are not copied into this course; follow local source links when needed. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../03.product/adrs) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
