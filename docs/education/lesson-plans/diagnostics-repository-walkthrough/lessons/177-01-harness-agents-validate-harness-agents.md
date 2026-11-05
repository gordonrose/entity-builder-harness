<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l177
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/01.harness/agents/validate-harness-agents.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L177 — scripts/01.harness/agents/validate-harness-agents

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/01.harness/agents/validate-harness-agents -->

## What you will understand

Chat/export/metrics tools and metadata utilities support agent work. Some are owned upstream by llm-workbench rather than by this repo.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A metadata update fails during its third write. Report the observed stage, completed returned-write count and uncertainty about the current write. Do not claim the whole update rolled back or print an arbitrary native exception.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Commands already worked, but failure paths could print arbitrary error messages, filenames, child output or submitted values.

**After:** Authorized paths use finite phases and fixed concerns while preserving intended successful reports, call order and existing outcomes. Six imported-file corrections were explicitly approved; wider upstream work is deferred.

**Why this was needed:** A command failure can leak information too. At the same time, sanitizing a failure must not erase the successful inventory the user deliberately asked the tool to produce.

This directory contains `test`, `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/01.harness/agents/validate-harness-agents/diagnostic-test.js -->

### diagnostic-test.js

[Open current source](../../../../../scripts/01.harness/agents/validate-harness-agents/diagnostic-test.js) · **Snapshot:** added (absent from baseline); 212 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for tooling and bounded imported exceptions.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): The actual task-token comparison command retains its existing successful JSON/numerical behavior and fail()/exit1 interface. Native repository-discovery and input-read failures now select finite owning concerns without paths or native message text.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `assert`, `fs`, `os`, `path`, `repoRoot`, `fixtureRoot`, `wrapper`, `canary`, `rubric`, `singleWorkflow`, `boardWorkflow`, `scorecardExample` (6 more in source).

Added import edges: `assert/strict`, `fs`, `os`, `path`, `child_process`.

Owning registered proof: `harness-agent-validator-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=e043b1cff7c5c7bfbd4fc9e1404ab2160bcd86df9dc881410a535a4b30b847a9 -->

<!-- course-file: scripts/01.harness/agents/validate-harness-agents/diagnostic-test.sh -->

### diagnostic-test.sh

[Open current source](../../../../../scripts/01.harness/agents/validate-harness-agents/diagnostic-test.sh) · **Snapshot:** added (absent from baseline); 21 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for tooling and bounded imported exceptions.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): The actual task-token comparison command retains its existing successful JSON/numerical behavior and fail()/exit1 interface. Native repository-discovery and input-read failures now select finite owning concerns without paths or native message text.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Owning registered proof: `harness-agent-validator-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=7f2774b941b35a69c9f6c1dd1aa600dabe2ec2be77ec7697427530caee0fee3c -->

<!-- course-file: scripts/01.harness/agents/validate-harness-agents/script.js -->

### script.js

[Open current source](../../../../../scripts/01.harness/agents/validate-harness-agents/script.js) · **Snapshot:** modified existing file; 134 added / 118 removed lines. These are textual counts, not a count of new features.

**What it does:** Implement harness review-agent validation checks.

**Before:** Commands already worked, but failure paths could print arbitrary error messages, filenames, child output or submitted values. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `parseArgs`, `read`, `parseJsonCompatiblePath`, `parseJsonCompatibleContent`, `parseWorkflowJsonBlock`, `validateRoutingConfig`, `selectedAgentsForFixture` (5 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): The actual existing agent-validator command reports fixed code-owned parsing, regular-expression compilation and I/O concerns at the observed logical location rather than native exception messages or submitted filenames/patterns. Input grammar, valid regex recompilation/matching, routing, scorecards, accepted examples and original exits remain.

**Why:** A command failure can leak information too. At the same time, sanitizing a failure must not erase the successful inventory the user deliberately asked the tool to produce.

Changed declaration anchors: `parseArgs`, `read`, `parseJsonCompatiblePath`, `parseJsonCompatibleContent`, `parseWorkflowJsonBlock`, `validateRoutingConfig`, `selectedAgentsForFixture`, `selectedAgentsFromComposition`, `validateBoardCompositionConfig`, `walkScorecardFiles`, `validateCliScorecards`, `validateCfoFixture`.

Declarations removed or relocated: `labelForPath`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `harness-agent-validator-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=bc055247eba8d34150a6ec0fb37527212e87a02a4614b18777213fae7d9be5c2 after=89ad78f572b3dae3fd8b2943b15557cde43f163e98646c9d7bd9e6e5dca4e110 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: How can a tool preserve intentional successful source inventory while avoiding uncontrolled failure text?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No installation, ownership-hash reset, upstream change, real Git action or global timelog infrastructure is included in this course. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/01.harness/agents/validate-harness-agents) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
