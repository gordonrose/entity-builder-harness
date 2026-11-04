<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l174
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/00.chat/metrics/estimate-chat-cost.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L174 — scripts/00.chat/metrics/estimate-chat-cost

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/00.chat/metrics/estimate-chat-cost -->

## What you will understand

Chat/export/metrics tools and metadata utilities support agent work. Some are owned upstream by llm-workbench rather than by this repo.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A metadata update fails during its third write. Report the observed stage, completed returned-write count and uncertainty about the current write. Do not claim the whole update rolled back or print an arbitrary native exception.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Commands already worked, but failure paths could print arbitrary error messages, filenames, child output or submitted values.

**After:** Authorized paths use finite phases and fixed concerns while preserving intended successful reports, call order and existing outcomes. Six imported-file corrections were explicitly approved; wider upstream work is deferred.

**Why this was needed:** A command failure can leak information too. At the same time, sanitizing a failure must not erase the successful inventory the user deliberately asked the tool to produce.

This directory contains `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/00.chat/metrics/estimate-chat-cost/script.js -->

### script.js

[Open current source](../../../../../scripts/00.chat/metrics/estimate-chat-cost/script.js) · **Snapshot:** modified existing file; 28 added / 7 removed lines. These are textual counts, not a count of new features.

**What it does:** Estimate chat cost metadata from an estimated token count.

**Before:** Commands already worked, but failure paths could print arbitrary error messages, filenames, child output or submitted values. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `phase`, `main` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Explicit six-file local exception: the existing specialized cost interface retains token/rate grammar, provider-neutral defaults and successful report basis. Fixed logical concerns distinguish repository discovery and pricing read/parse/projection.

**Why:** A command failure can leak information too. At the same time, sanitizing a failure must not erase the successful inventory the user deliberately asked the tool to produce.

Changed declaration anchors: `phase`, `main`.

New declarations within this existing file: `phase`, `main`.

Declarations removed or relocated: `tokenValue`, `requestedProfile`, `tokenCount`, `repoRoot`, `pricingPath`, `pricing`, `profileName`, `profile`, `rate`, `currency` (4 more in source). Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `chat-commit-metrics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=9dd2b27de8e71a7cc0f57d5f538207b8f49c2c8a074d87b7a41cc5b74d923cff after=2dc02eaa618889642810e9060de228574eb5d87acf51400ca2264add50ff2af9 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: How can a tool preserve intentional successful source inventory while avoiding uncontrolled failure text?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No installation, ownership-hash reset, upstream change, real Git action or global timelog infrastructure is included in this course. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/00.chat/metrics/estimate-chat-cost) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
