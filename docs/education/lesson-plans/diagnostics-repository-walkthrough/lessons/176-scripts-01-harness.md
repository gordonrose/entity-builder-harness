<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l176
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/01.harness.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L176 — scripts/01.harness

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/01.harness -->

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

This directory contains `implementation`, `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/01.harness/check-artifact-path-migration.sh -->

### check-artifact-path-migration.sh

[Open current source](../../../../../scripts/01.harness/check-artifact-path-migration.sh) · **Snapshot:** modified existing file; 47 added / 14 removed lines. These are textual counts, not a count of new features.

**What it does:** Validate that a path migration does not leave unapproved active old-path

**Before:** Commands already worked, but failure paths could print arbitrary error messages, filenames, child output or submitted values. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): The existing active migration checker and planner distinguish repository lookup/access, Git enumeration/reduction and reference-read failure from a successful empty result. Finite inline concerns exclude native streams, rejected plan values and checker matched source contents, while retaining accepted file:line finding locations.

**Why:** A command failure can leak information too. At the same time, sanitizing a failure must not erase the successful inventory the user deliberately asked the tool to produce.

Owning registered proof: `harness-artifact-migration-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=11055e5e971510dffe911d302fb31b8bf8f8012b00fa51134d222d2e7252c86e after=e2f9362befd88622d394a8c264c5d62e7ec8f169d2450424d33b0a3cc42948f3 -->

<!-- course-file: scripts/01.harness/plan-artifact-path-migration.sh -->

### plan-artifact-path-migration.sh

[Open current source](../../../../../scripts/01.harness/plan-artifact-path-migration.sh) · **Snapshot:** modified existing file; 45 added / 12 removed lines. These are textual counts, not a count of new features.

**What it does:** Inventory references before moving, renaming, retiring, or removing repository

**Before:** Commands already worked, but failure paths could print arbitrary error messages, filenames, child output or submitted values. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): The existing active migration checker and planner distinguish repository lookup/access, Git enumeration/reduction and reference-read failure from a successful empty result. Finite inline concerns exclude native streams, rejected plan values and checker matched source contents, while retaining accepted file:line finding locations.

**Why:** A command failure can leak information too. At the same time, sanitizing a failure must not erase the successful inventory the user deliberately asked the tool to produce.

Owning registered proof: `harness-artifact-migration-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=cd126929d86abe724a2c330f86a90c7ec939aa288bf27589ef1b3316b4cad09a after=80fef3bd513a3a14dd967d2f009632b44eb746bda6b569c06aefdcd598025574 -->

<!-- course-file: scripts/01.harness/smoke-test-artifact-path-migration.sh -->

### smoke-test-artifact-path-migration.sh

[Open current source](../../../../../scripts/01.harness/smoke-test-artifact-path-migration.sh) · **Snapshot:** modified existing file; 145 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for tooling and bounded imported exceptions.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): The existing active migration checker and planner distinguish repository lookup/access, Git enumeration/reduction and reference-read failure from a successful empty result. Finite inline concerns exclude native streams, rejected plan values and checker matched source contents, while retaining accepted file:line finding locations.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Owning registered proof: `harness-artifact-migration-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=99838526820c00de37a71a9839e2dc81b43272df6294131831c503c99169b72b after=f93a5142947b10990068789c8d6e3ee8e4733307422339bbe122a707c6e09b4e -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: How can a tool preserve intentional successful source inventory while avoiding uncontrolled failure text?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No installation, ownership-hash reset, upstream change, real Git action or global timelog infrastructure is included in this course. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/01.harness) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L127 scripts/04.deploy](127-scripts-04-deploy.md) · [L178 scripts/01.harness/artifact-metadata](178-scripts-01-harness-artifact-metadata.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
