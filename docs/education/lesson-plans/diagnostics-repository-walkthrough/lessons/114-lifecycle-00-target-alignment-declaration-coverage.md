<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l114
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L114 — scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage -->

## What you will understand

Alignment tooling compares declared target requirements and observed provider conditions before build or deployment.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a supported DescribeDBInstances not-found response with a bare error-code string or a failure from another operation. Only the exact supported observation can establish the declared absence condition.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The declarations and read-only checks already existed. Unreadable files, malformed provider responses and command failures could be confused with a valid empty observation.

**After:** Finite diagnostics distinguish declaration/shape/predicate/native-command boundaries while preserving existing comparison rules and actual command order.

**Why this was needed:** If an AWS observation fails, the agent must not conclude the resource is absent or aligned. Unknown is materially different from a checked negative result.

This directory contains `test`, `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime-configuration-test.py -->

### runtime-configuration-test.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime-configuration-test.py) · **Snapshot:** modified existing file; 27 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for target declarations and provider observation.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. The newly visible named cases below provide concrete reading anchors. Connected proving scope (the review spans related files, not only this test): Retain requirement/check chains, legitimate missing paths, applicability and configuration projection. Rejected references cannot reappear through inputs/consumers/findings, and invalid logical identities use fixed report markers without changing admission.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Added named test anchors: `test_b10_rejected_reference_projection`.

Owning registered proof: `delivery-inventory-regression`, `persistence-composition`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=4a367df9461244d222265c8c47435e1118f8485d5776772b9243e2dac19449a0 after=796d1d155214ba413e7dcec793e2719503f6eaa55b5f4ca9329942a1ae4837ad -->

<!-- course-file: scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime_configuration.py -->

### runtime_configuration.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime_configuration.py) · **Snapshot:** modified existing file; 2 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Compare workload requirements with normalized package and provider configuration facts.

**Before:** The declarations and read-only checks already existed. Unreadable files, malformed provider responses and command failures could be confused with a valid empty observation. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Retain requirement/check chains, legitimate missing paths, applicability and configuration projection. Rejected references cannot reappear through inputs/consumers/findings, and invalid logical identities use fixed report markers without changing admission.

**Why:** If an AWS observation fails, the agent must not conclude the resource is absent or aligned. Unknown is materially different from a checked negative result.

Current reading anchors (not all are new): `inspect`, `gap`, `supplied_by_command`, `names`.

Owning registered proof: `delivery-inventory-regression`, `persistence-composition`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ca416350747310f4320968cb18c4cea4c79f6f14eeca340649bd62002fd1a350 after=fac762e656f6490c2dfff72c5e59d0272ef73891e54d640f05fa9a38ad6bc16f -->

<!-- course-file: scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py -->

### script.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py) · **Snapshot:** modified existing file; 35 added / 13 removed lines. These are textual counts, not a count of new features.

**What it does:** Validate existing target scope requirement chains and referenced implementation and proof paths offline.

**Before:** The declarations and read-only checks already existed. Unreadable files, malformed provider responses and command failures could be confused with a valid empty observation. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Retain requirement/check chains, legitimate missing paths, applicability and configuration projection. Rejected references cannot reappear through inputs/consumers/findings, and invalid logical identities use fixed report markers without changing admission.

**Why:** If an AWS observation fails, the agent must not conclude the resource is absent or aligned. Unknown is materially different from a checked negative result.

Current reading anchors (not all are new): `document`, `safe_path`, `within`, `strings`, `report_identity`, `check_applicability`, `inspect_declaration`, `gap`, `reference`, `inspect` (4 more in source).

Owning registered proof: `delivery-inventory-regression`, `persistence-composition`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=8ed8641f1755c04cc92a085d168717c3a9898c3a28489f98d4292e12894b759b after=666cd462eb80bda03511d8b0fb91c1f689fe5ce5bba60a2038f29e266ec69c1d -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: When is an empty result evidence of absence, and when is it evidence that observation failed?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Fixtures prove local classification. No live AWS observation was executed to prepare this course. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L113 scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration](113-lifecycle-00-target-alignment-core-platform-target-declaration.md) · [L119 scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement](119-lifecycle-00-target-alignment-validate-artifact-placement.md) · [L120 scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration](120-lifecycle-00-target-alignment-validate-observability-mvp-declaration.md) · [L121 scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence](121-lifecycle-00-target-alignment-validate-provider-condition-evidence.md) · [L122 scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration](122-lifecycle-00-target-alignment-validate-secret-dependency-declaration.md) · [L123 scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment](123-lifecycle-00-target-alignment-validate-target-alignment.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
