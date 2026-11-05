<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l155
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/verify-platform-shell-deploy-readiness.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L155 — scripts/04.deploy/verify-platform-shell-deploy-readiness

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/verify-platform-shell-deploy-readiness -->

## What you will understand

Controllers orchestrate existing deployment and verification steps; readers interpret the receipts and task output on which later decisions rely.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A verifier task fails; its safe existing log record identifies the operation. The controller may retain that checked record, but a failed or partial log read cannot turn failure into success. A remote side effect remains uncertain unless separate evidence proves it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress.

**After:** Readers validate selected generated contracts and preserve primary failure plus bounded source observations. The failed-verifier path permits one bounded read of the failed task's existing stream after exact identity validation; successful verification remains unchanged.

**Why this was needed:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

This directory contains `test`, `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/verify-platform-shell-deploy-readiness/release-evidence-test.py -->

### release-evidence-test.py

[Open current source](../../../../../scripts/04.deploy/verify-platform-shell-deploy-readiness/release-evidence-test.py) · **Snapshot:** modified existing file; 56 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for deployment controllers and evidence readers.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Retain the release evidence reader and actual shell wrapper's specialized protocol, ValueError compatibility and upstream typed failure code. Only checked owned failure context crosses the boundary; arbitrary validation/native text is not parsed as proof or echoed.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Current reading anchors (not all are new): `command`, `observed`, `promote`, `package`, `prepare`, `tests`, `ready`.

Owning registered proof: `shell-release-evidence-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=31fe45f93ebdbdcdcdc7cf0369585d55ab5992c01d343b8104054b173ff8d423 after=ea439bd88ba9b6a50c981baeccef9cf6e5ee47d364c70feecd26ad69deb6ef94 -->

<!-- course-file: scripts/04.deploy/verify-platform-shell-deploy-readiness/release_evidence.py -->

### release_evidence.py

[Open current source](../../../../../scripts/04.deploy/verify-platform-shell-deploy-readiness/release_evidence.py) · **Snapshot:** modified existing file; 78 added / 68 removed lines. These are textual counts, not a count of new features.

**What it does:** Bind shell readiness to producer-observed current state and immutable generic release succession without overwriting historical evidence.

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Retain the release evidence reader and actual shell wrapper's specialized protocol, ValueError compatibility and upstream typed failure code. Only checked owned failure context crosses the boundary; arbitrary validation/native text is not parsed as proof or echoed.

**Why:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

Current reading anchors (not all are new): `succession_call`, `digest`, `source_inputs`, `succession`, `within`, `identity`, `observation`, `package_receipt`, `validate_candidate`, `write_candidate` (2 more in source).

Owning registered proof: `shell-release-evidence-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=a452262e49cfe1421c7bb484b8625f8e7e8ff68d8bd5203d837600825f278a9e after=069128169b964690c17267610177d9814c00bf5c5af8a86debd979b448c399e3 -->

<!-- course-file: scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh -->

### script.sh

[Open current source](../../../../../scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh) · **Snapshot:** modified existing file; 224 added / 44 removed lines. These are textual counts, not a count of new features.

**What it does:** Validate platform shell deploy-readiness evidence without mutating GitHub or AWS.

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Retain the release evidence reader and actual shell wrapper's specialized protocol, ValueError compatibility and upstream typed failure code. Only checked owned failure context crosses the boundary; arbitrary validation/native text is not parsed as proof or echoed.

**Why:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

Owning registered proof: `shell-release-evidence-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f2f11698dc505f33ef862b9009faee84e697266e46308fcab399aa8a9f842305 after=9c0fc6daa80601a91a895ab5ca393503dfe5b32797b94952e49298eb3189dba0 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must failure to read a failed task's log not replace the original verification failure?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local reader/controller fixtures do not prove live stream identity, rollout success or rollback compatibility; live checks belong to a separate chat. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/verify-platform-shell-deploy-readiness) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L094 scripts/04.deploy/build-platform-shell-image](094-scripts-04-deploy-build-platform-shell-image.md) · [L110 scripts/04.deploy/smoke-test-platform-shell-image](110-scripts-04-deploy-smoke-test-platform-shell-image.md) · [L111 scripts/04.deploy/validate-container-boundaries](111-scripts-04-deploy-validate-container-boundaries.md) · [L112 scripts/04.deploy/inventory-deploy-control](112-scripts-04-deploy-inventory-deploy-control.md) · [L127 scripts/04.deploy](127-scripts-04-deploy.md) · [L152 scripts/04.deploy/reconcile-platform-shell-staging](152-scripts-04-deploy-reconcile-platform-shell-staging.md) · [L153 scripts/04.deploy/shared](153-scripts-04-deploy-shared.md) · [L168 scripts/04.deploy/verify-platform-shell-deployment-workflow](168-scripts-04-deploy-verify-platform-shell-deployment-workflow.md) · [L169 scripts/04.deploy/verify-platform-shell-infrastructure](169-scripts-04-deploy-verify-platform-shell-infrastructure.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
