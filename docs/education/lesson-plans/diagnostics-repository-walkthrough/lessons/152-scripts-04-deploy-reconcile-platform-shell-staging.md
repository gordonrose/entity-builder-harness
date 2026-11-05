<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l152
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/reconcile-platform-shell-staging.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L152 — scripts/04.deploy/reconcile-platform-shell-staging

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/reconcile-platform-shell-staging -->

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

<!-- course-file: scripts/04.deploy/reconcile-platform-shell-staging/release-control-test.py -->

### release-control-test.py

[Open current source](../../../../../scripts/04.deploy/reconcile-platform-shell-staging/release-control-test.py) · **Snapshot:** modified existing file; 21 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for deployment controllers and evidence readers.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. The newly visible named cases below provide concrete reading anchors. Connected proving scope (the review spans related files, not only this test): The actual release-control/staging reconciliation interfaces retain finite existing findings, original code/status and CAS/precondition semantics. Reviewed typed ValueError-compatible checked evidence propagation retains upstream failure identity without projecting arbitrary native/schema/YAML/time text, and failed provider observations remain uncertain rather than inventing absence or successful mutation.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Added named test anchors: `test_native_and_owned_failure_bridges_do_not_trust_exception_text`.

Owning registered proof: `shell-deployment-reconciliation-check`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=502bfe852583bae40fbb8f8b4d8149a8090f52ab296cdbf7a6f0f944ad479c3f after=694cc007e3ca2facc081843850172d46af0b46d2e2aca74ea0b74cfc82d4f74a -->

<!-- course-file: scripts/04.deploy/reconcile-platform-shell-staging/release_control.py -->

### release_control.py

[Open current source](../../../../../scripts/04.deploy/reconcile-platform-shell-staging/release_control.py) · **Snapshot:** modified existing file; 41 added / 21 removed lines. These are textual counts, not a count of new features.

**What it does:** Observe source-bound shell runtime and guard reviewed service mutations without replaying uncertain submissions.

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): The actual release-control/staging reconciliation interfaces retain finite existing findings, original code/status and CAS/precondition semantics. Reviewed typed ValueError-compatible checked evidence propagation retains upstream failure identity without projecting arbitrary native/schema/YAML/time text, and failed provider observations remain uncertain rather than inventing absence or successful mutation.

**Why:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

Current reading anchors (not all are new): `module`, `require`, `unique`, `__init__`, `aws`, `stack`, `sources`, `source_alignment`, `physical`, `resolve` (7 more in source).

Owning registered proof: `shell-deployment-reconciliation-check`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=57d70bd61b79d2ec38d902f54b47845a013067e7157c3565750148c4bb9cee5d after=f6dbe6cef117aa203ae9bcb7d2e7d3d1112f8ae2299738c2b1ae005e8c316a3b -->

<!-- course-file: scripts/04.deploy/reconcile-platform-shell-staging/script.py -->

### script.py

[Open current source](../../../../../scripts/04.deploy/reconcile-platform-shell-staging/script.py) · **Snapshot:** modified existing file; 19 added / 5 removed lines. These are textual counts, not a count of new features.

**What it does:** Safely reconcile declared Kanbien staging controls before mutation and on a recurring read-only cadence.

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): The actual release-control/staging reconciliation interfaces retain finite existing findings, original code/status and CAS/precondition semantics. Reviewed typed ValueError-compatible checked evidence propagation retains upstream failure identity without projecting arbitrary native/schema/YAML/time text, and failed provider observations remain uncertain rather than inventing absence or successful mutation.

**Why:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

Current reading anchors (not all are new): `error`, `parse_arguments`, `load_yaml`, `mapping`, `text`, `resolve_policy`, `run_aws`, `require`, `run_check`, `bootstrap_effects_receipt_path` (14 more in source).

Owning registered proof: `shell-deployment-reconciliation-check`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=0d9e2ef0b8df75f16bc9ce9cbd06ccbc129be32b9544f229b259e3f156897b42 after=207dfbff64fd27dd2770d084bc0ecedcd8e43db50480755bb0dd67da4eb56667 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must failure to read a failed task's log not replace the original verification failure?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local reader/controller fixtures do not prove live stream identity, rollout success or rollback compatibility; live checks belong to a separate chat. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/reconcile-platform-shell-staging) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L094 scripts/04.deploy/build-platform-shell-image](094-scripts-04-deploy-build-platform-shell-image.md) · [L110 scripts/04.deploy/smoke-test-platform-shell-image](110-scripts-04-deploy-smoke-test-platform-shell-image.md) · [L111 scripts/04.deploy/validate-container-boundaries](111-scripts-04-deploy-validate-container-boundaries.md) · [L112 scripts/04.deploy/inventory-deploy-control](112-scripts-04-deploy-inventory-deploy-control.md) · [L127 scripts/04.deploy](127-scripts-04-deploy.md) · [L153 scripts/04.deploy/shared](153-scripts-04-deploy-shared.md) · [L155 scripts/04.deploy/verify-platform-shell-deploy-readiness](155-scripts-04-deploy-verify-platform-shell-deploy-readiness.md) · [L168 scripts/04.deploy/verify-platform-shell-deployment-workflow](168-scripts-04-deploy-verify-platform-shell-deployment-workflow.md) · [L169 scripts/04.deploy/verify-platform-shell-infrastructure](169-scripts-04-deploy-verify-platform-shell-infrastructure.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
