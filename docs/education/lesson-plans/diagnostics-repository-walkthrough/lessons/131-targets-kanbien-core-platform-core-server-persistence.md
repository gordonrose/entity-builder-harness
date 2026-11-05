<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l131
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L131 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence -->

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

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/controller-regression.py -->

### controller-regression.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/controller-regression.py) · **Snapshot:** modified existing file; 68 added / 6 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for deployment controllers and evidence readers.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. The newly visible named cases below provide concrete reading anchors. Connected proving scope (the review spans related files, not only this test): Reviewed prepare/create/deploy/retire boundaries retain actual parameter and provider call order, finite code/status observations and known operation identity without echoing native failures, private child output or rejected values. Retire distinguishes positively classified missing from unavailable provider observations; failed submit/read responses do not establish no effect.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Added named test anchors: `test_native_reconciliation_shapes_are_unknown_without_mutations`; `test_create_parameter_file_failures_preserve_submission_boundary`.

Owning registered proof: `persistence-provider-regression`, `diagnostic-catalog-readers`, `deployment-operation-diagnostics-regression`, `persistence-diagnostic-mapping-regression`, `restore-connection-diagnostics`, `persistence-payload-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f4d07a55c8b8dcce8fd9835d3bba31b63c8e0c2f1be0bb78e39dc8e4c05ecb56 after=eeaee2fa43bb9a1f101d278ccd1eb5546521ca6173e9e2eb313a3039bdedc6e3 -->

<!-- course-file: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/smoke-test.sh -->

### smoke-test.sh

[Open current source](../../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/smoke-test.sh) · **Snapshot:** modified existing file; 85 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Owning registered proof: `persistence-provider-regression`, `deployment-operation-diagnostics-regression`, `runtime-credential-lifecycle-regression`, `diagnostic-catalog-readers`, `persistence-diagnostic-mapping-regression`, `restore-connection-diagnostics`, `persistence-payload-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6db83e1e635a5c3ef3add4484ffb175473aa106abcd03584ff1f8296e06b8661 after=7d17abb0efff8c702cdfea2f76cbb64d8fbcf7a5788b323cd6ef884d1752babe -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must failure to read a failed task's log not replace the original verification failure?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local reader/controller fixtures do not prove live stream identity, rollout success or rollback compatibility; live checks belong to a separate chat. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L128 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime](128-targets-kanbien-core-platform-bootstrap-runtime.md) · [L132 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface](132-kanbien-core-platform-core-server-persistence-apply-restoration-verifier-surface.md) · [L133 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set](133-kanbien-core-platform-core-server-persistence-create-change-set.md) · [L134 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate](134-kanbien-core-platform-core-server-persistence-deploy-candidate.md) · [L135 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate](135-kanbien-core-platform-core-server-persistence-prepare-candidate.md) · [L136 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/reconcile-rds-log-export-surface](136-kanbien-core-platform-core-server-persistence-reconcile-rds-log-export-surface.md) · [L137 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate](137-kanbien-core-platform-core-server-persistence-retire-failed-candidate.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
