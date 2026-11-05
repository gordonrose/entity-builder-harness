<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l121
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L121 — scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence -->

## What you will understand

Alignment tooling compares declared target requirements and observed provider conditions before build or deployment.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a supported DescribeDBInstances not-found response with a bare error-code string or a failure from another operation. Only the exact supported observation can establish the declared absence condition.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The declarations and read-only checks already existed. Unreadable files, malformed provider responses and command failures could be confused with a valid empty observation.

**After:** Finite diagnostics distinguish declaration/shape/predicate/native-command boundaries while preserving existing comparison rules and actual command order.

**Why this was needed:** If an AWS observation fails, the agent must not conclude the resource is absent or aligned. Unknown is materially different from a checked negative result.

This directory contains `implementation`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.py -->

### script.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.py) · **Snapshot:** modified existing file; 5 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Validate safe, provider-neutral evidence for a provider-controlled asynchronous condition, including freshness, validity boundaries, and an explicit waiver's expiry.

**Before:** The declarations and read-only checks already existed. Unreadable files, malformed provider responses and command failures could be confused with a valid empty observation. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Retain waiting/verified/waiver status and timestamp policies; malformed status is an owned invalid observation, never an invented provider condition or copied rejected ID. Existing positive, stale/temporal/waiver, malformed and argument-canary fixtures preserve the accepted evidence contract.

**Why:** If an AWS observation fails, the agent must not conclude the resource is absent or aligned. Unknown is materially different from a checked negative result.

Current reading anchors (not all are new): `timestamp`, `parsed_timestamp`, `safe_string`, `main`.

Owning registered proof: `provider-condition-evidence-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=3ebb1c7033637d6b8c885d431042bfaf67fca70848d88b12f3e09b33f540fb86 after=0bb847039dee4d8320998ef13124ac3f44871083a91402ed80333f01f6830b01 -->

<!-- course-file: scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/smoke-test.sh -->

### smoke-test.sh

[Open current source](../../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/smoke-test.sh) · **Snapshot:** modified existing file; 15 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Owning registered proof: `provider-condition-evidence-regression`, `bootstrap-target-controls-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=bf974725bcd09740dbfb739d7e7dd19f4c91005d49364d8626668940036e3b6d after=d8053fd25ea228bc1cee77d95474a88d1032d6e708ca6cb087c2093319217277 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: When is an empty result evidence of absence, and when is it evidence that observation failed?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Fixtures prove local classification. No live AWS observation was executed to prepare this course. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L113 scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration](113-lifecycle-00-target-alignment-core-platform-target-declaration.md) · [L114 scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage](114-lifecycle-00-target-alignment-declaration-coverage.md) · [L119 scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement](119-lifecycle-00-target-alignment-validate-artifact-placement.md) · [L120 scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration](120-lifecycle-00-target-alignment-validate-observability-mvp-declaration.md) · [L122 scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration](122-lifecycle-00-target-alignment-validate-secret-dependency-declaration.md) · [L123 scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment](123-lifecycle-00-target-alignment-validate-target-alignment.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
