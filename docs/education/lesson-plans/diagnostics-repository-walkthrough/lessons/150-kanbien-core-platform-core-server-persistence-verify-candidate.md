<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l150
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L150 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate -->

## What you will understand

Controllers orchestrate existing deployment and verification steps; readers interpret the receipts and task output on which later decisions rely.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

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

<!-- course-file: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/operation-test.py -->

### operation-test.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/operation-test.py) · **Snapshot:** modified existing file; 54 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for deployment controllers and evidence readers.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. The newly visible named cases below provide concrete reading anchors. Connected proving scope (the review spans related files, not only this test): Retain historical rejection, success, restore-v2 and original exit/result behavior. A failed task with a positively validated exact target task ARN and existing stream permits only the approved single get-log-events read limited to 100; successful verification calls remain unchanged.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Added named test anchors: `test_aws_native_failures_and_anchored_denial_preserve_one_call`; `test_failed_task_one_bounded_read_retains_source_nine_and_late_frame`; `test_failed_task_log_denial_does_not_replace_original_failure_or_identity`.

Owning registered proof: `persistence-provider-regression`, `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=3cc5ffeb43492f0ab2e9c189d8ab4e535a5ee47de8c276f3d4318fe158a20ed2 after=d5935723bc2683799d11e42f7d6534a7f8f7cb4e1207b3ea79ce5e0d32f29236 -->

<!-- course-file: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.py -->

### script.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.py) · **Snapshot:** modified existing file; 46 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements the owning deployment controllers and evidence readers command or helper.

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Retain historical rejection, success, restore-v2 and original exit/result behavior. A failed task with a positively validated exact target task ARN and existing stream permits only the approved single get-log-events read limited to 100; successful verification calls remain unchanged.

**Why:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

Current reading anchors (not all are new): `aws`, `report`, `proof_receipts`, `failed_task_log`, `outputs`, `deadline`, `parsed`, `duration`, `exited_zero`, `current_reconciliation_task` (20 more in source).

Owning registered proof: `persistence-provider-regression`, `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=3f7aeb9c7cbbef7e3bff06c975f336e98168d4e434a83d952d114dac9b8f281c after=d4811bc006e4466d4595ebf6c7a7758e7a2973830abca9ecc278fe1db2b93804 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must failure to read a failed task's log not replace the original verification failure?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local reader/controller fixtures do not prove live stream identity, rollout success or rollback compatibility; live checks belong to a separate chat. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L141 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence](141-targets-kanbien-core-platform-core-server-persistence.md) · [L142 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal](142-kanbien-core-platform-core-server-persistence-acceptance-route-rehearsal.md) · [L143 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence](143-kanbien-core-platform-core-server-persistence-collect-acceptance-evidence.md) · [L144 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore](144-kanbien-core-platform-core-server-persistence-rehearse-isolated-database-restore.md) · [L145 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness](145-kanbien-core-platform-core-server-persistence-rehearse-observability-readiness.md) · [L146 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle](146-kanbien-core-platform-core-server-persistence-rehearse-runtime-credential-lifecycle.md) · [L147 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement](147-kanbien-core-platform-core-server-persistence-rehearse-server-replacement.md) · [L148 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration](148-kanbien-core-platform-core-server-persistence-run-administration.md) · [L149 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration](149-kanbien-core-platform-core-server-persistence-run-migration.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
