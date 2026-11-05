<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l181
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/01.harness/artifact-metadata/update-lifecycle.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L181 — scripts/01.harness/artifact-metadata/update-lifecycle

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/01.harness/artifact-metadata/update-lifecycle -->

## What you will understand

Chat/export/metrics tools and metadata utilities support agent work. Some are owned upstream by llm-workbench rather than by this repo.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A metadata update fails during its third write. Report the observed stage, completed returned-write count and uncertainty about the current write. Do not claim the whole update rolled back or print an arbitrary native exception.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Commands already worked, but failure paths could print arbitrary error messages, filenames, child output or submitted values.

**After:** Authorized paths use finite phases and fixed concerns while preserving intended successful reports, call order and existing outcomes. Six imported-file corrections were explicitly approved; wider upstream work is deferred.

**Why this was needed:** A command failure can leak information too. At the same time, sanitizing a failure must not erase the successful inventory the user deliberately asked the tool to produce.

This directory contains `implementation`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/01.harness/artifact-metadata/update-lifecycle/script.sh -->

### script.sh

[Open current source](../../../../../scripts/01.harness/artifact-metadata/update-lifecycle/script.sh) · **Snapshot:** modified existing file; 274 added / 99 removed lines. These are textual counts, not a count of new features.

**What it does:** Report or apply bounded artifact lifecycle metadata updates without staging or committing.

**Before:** Commands already worked, but failure paths could print arbitrary error messages, filenames, child output or submitted values. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Existing PlanError distinctions and report fields retain numerical/date/history/path/reference, HEAD, concurrent-selection and planned-write semantics. Finite stage/field/condition reports distinguish repository/clock/support/selection/planning/reference/recheck/write/preparation-receipt failures.

**Why:** A command failure can leak information too. At the same time, sanitizing a failure must not erase the successful inventory the user deliberately asked the tool to produce.

Owning registered proof: `harness-lifecycle-metadata-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=57aa491d2633ae9c5a5e6a441479a13bff9ec8660f3af5465cb16038a1403fa7 after=c66d3f29558ba033c72171a2a6cfad8d2615ec4b3ff39226696673668b65560c -->

<!-- course-file: scripts/01.harness/artifact-metadata/update-lifecycle/smoke-test.sh -->

### smoke-test.sh

[Open current source](../../../../../scripts/01.harness/artifact-metadata/update-lifecycle/smoke-test.sh) · **Snapshot:** modified existing file; 187 added / 7 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Owning registered proof: `harness-lifecycle-metadata-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f838062ebe9575e231d474bfaed77e91ec371effa33a7d0c6f693e91933596ea after=fdb099a9b340d7c02f820137240656cb29398468e878173455f936f335530f96 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: How can a tool preserve intentional successful source inventory while avoiding uncontrolled failure text?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No installation, ownership-hash reset, upstream change, real Git action or global timelog infrastructure is included in this course. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/01.harness/artifact-metadata/update-lifecycle) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L178 scripts/01.harness/artifact-metadata](178-scripts-01-harness-artifact-metadata.md) · [L179 scripts/01.harness/artifact-metadata/backfill-v2-headers](179-01-harness-artifact-metadata-backfill-v2-headers.md) · [L180 scripts/01.harness/artifact-metadata/generate-index](180-01-harness-artifact-metadata-generate-index.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
