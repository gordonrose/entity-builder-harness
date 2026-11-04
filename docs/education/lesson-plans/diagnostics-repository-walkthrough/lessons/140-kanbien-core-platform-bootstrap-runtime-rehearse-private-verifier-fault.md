<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l140
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L140 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault -->

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

This directory contains `implementation`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/script.py -->

### script.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/script.py) · **Snapshot:** modified existing file; 102 added / 60 removed lines. These are textual counts, not a count of new features.

**What it does:** Run one fixed private-verifier rejection or controller-timeout rehearsal without changing the accepted service or accepting arbitrary commands.

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Actual replacement/private-verifier fault controllers preserve positively known task/operation identity independently from malformed definition/cardinality evidence and retain native/provider uncertainty. Invalid observations cannot manufacture an ok outcome; original stop/replay/admission and call order remain unchanged.

**Why:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

Current reading anchors (not all are new): `load_module`, `report`, `aws`, `outputs`, `fault_override`, `task_log_contains`, `task_exit_code`, `wait_for_cleanup_stop`, `service_unchanged`, `run_fault` (1 more in source).

Owning registered proof: `bootstrap-target-controls-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ff74961452b45e9bedda91900c8c2d8136f62d6677563659d93032290730db17 after=5265e2898c35703204be10c1c33b9d5530d2d53581358a65dc6a510a915593cd -->

<!-- course-file: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/smoke-test.sh -->

### smoke-test.sh

[Open current source](../../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/smoke-test.sh) · **Snapshot:** modified existing file; 72 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Owning registered proof: `bootstrap-target-controls-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=a439dee1f2d5a3295ca458f988ed64e111314495f666e61d35e28a2d414186c6 after=30156aacc204cf0d684b083a046b05c39f7f69c93ec930c20faa5e5853aa2f6e -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must failure to read a failed task's log not replace the original verification failure?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local reader/controller fixtures do not prove live stream identity, rollout success or rollback compatibility; live checks belong to a separate chat. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L139 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement](139-kanbien-core-platform-bootstrap-runtime-rehearse-accepted-workload-replacement.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
