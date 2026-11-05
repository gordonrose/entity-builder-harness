<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l153
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/shared.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L153 — scripts/04.deploy/shared

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/shared -->

## What you will understand

Controllers orchestrate existing deployment and verification steps; readers interpret the receipts and task output on which later decisions rely.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **5 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

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

<!-- course-file: scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.py -->

### deployment-operation-diagnostics-smoke-test.py

[Open current source](../../../../../scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.py) · **Snapshot:** modified existing file; 250 added / 9 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for deployment controllers and evidence readers.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Restoration surface deletion failure and bounded unconfirmed absence retain known operation/change-set/digest/mode identity and exact restrictions without claiming cleanup completed. Historical provider reads/order and reconciliation admission remain unchanged.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Current reading anchors (not all are new): `valid`, `fails`, `timeout_provider`, `event_collection_fails`, `source`, `event`, `load_controller`, `provider`, `restricted`, `interrupted_stop`.

Owning registered proof: `persistence-composition`, `restore-connection-diagnostics`, `platform-shell-payload`, `deployment-operation-diagnostics-regression`, `diagnostic-catalog-readers`, `persistence-provider-regression`, `runtime-credential-lifecycle-regression`, `acceptance-route-regression`, `persistence-diagnostic-mapping-regression`, `persistence-payload-regression`, `security-cognito-diagnostics`, `security-shared-rate-limit-diagnostics`, `cloudwatch-observability-runtime`, `ecs-fargate-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b125972ccddf8f89d62b541f57008f530e23408433f3c96db77b589dc4885359 after=abc1f56f01028374d3a1226dda78e510aba32fde9689f862738a81c1619c54cb -->

<!-- course-file: scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.sh -->

### deployment-operation-diagnostics-smoke-test.sh

[Open current source](../../../../../scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.sh) · **Snapshot:** modified existing file; 3 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for deployment controllers and evidence readers.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Existing safe-command interfaces preserve original child status, quiet success and a separate collection verdict; neither child nor failed secondary writer stdout/stderr is retained. The actual registered wrapper now dispatches both existing Python and Bash suites and fail-stops with exact child status.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Owning registered proof: `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=4a7411d63871c415693bbebf185e987fe036046b5619528999bd3429b87370e0 after=526f5829ecefdfd4cc2696bb8c44bfef26f1a7e997b8dc74d6b6bb09a6a0fc34 -->

<!-- course-file: scripts/04.deploy/shared/deployment-operation-diagnostics.py -->

### deployment-operation-diagnostics.py

[Open current source](../../../../../scripts/04.deploy/shared/deployment-operation-diagnostics.py) · **Snapshot:** modified existing file; 288 added / 27 removed lines. These are textual counts, not a count of new features.

**What it does:** Construct and validate safe retained deployment-operation reports and bounded CloudFormation failure classifications.

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Restoration surface deletion failure and bounded unconfirmed absence retain known operation/change-set/digest/mode identity and exact restrictions without claiming cleanup completed. Historical provider reads/order and reconciliation admission remain unchanged.

**Why:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

Current reading anchors (not all are new): `runtime_contract`, `validate_runtime_diagnostic`, `validate_related_diagnostics`, `validate_persistence_task_failure`, `source_bundle`, `collect_persistence_task_failure`, `omitted`, `validate_persistence_controller_checkpoint`, `__init__`, `now` (16 more in source).

Owning registered proof: `persistence-provider-regression`, `deployment-operation-diagnostics-regression`, `runtime-credential-lifecycle-regression`, `acceptance-route-regression`, `bootstrap-target-controls-regression`, `diagnostic-catalog-readers`, `persistence-diagnostic-mapping-regression`, `restore-connection-diagnostics`, `persistence-payload-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=e3bb62c2d8d03304f9dd683c745d3fc62f324d02801877617dc60809e83165df after=1f8df4d2695bbf67a0a06b077062a635e4e3590323cd979a922b477370e46548 -->

<!-- course-file: scripts/04.deploy/shared/safe-command-diagnostics-smoke-test.sh -->

### safe-command-diagnostics-smoke-test.sh

[Open current source](../../../../../scripts/04.deploy/shared/safe-command-diagnostics-smoke-test.sh) · **Snapshot:** modified existing file; 38 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for deployment controllers and evidence readers.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Existing safe-command interfaces preserve original child status, quiet success and a separate collection verdict; neither child nor failed secondary writer stdout/stderr is retained. The actual registered wrapper now dispatches both existing Python and Bash suites and fail-stops with exact child status.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Owning registered proof: `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=22b6972b7fa320d1920b071adf084650c27df87fa3308961bc142a3322c6e38d after=fb8e6a03a1f86a8b60dfe4d585dae3a93028541214118cc3b77ba351f7ceeea7 -->

<!-- course-file: scripts/04.deploy/shared/safe-command-diagnostics.sh -->

### safe-command-diagnostics.sh

[Open current source](../../../../../scripts/04.deploy/shared/safe-command-diagnostics.sh) · **Snapshot:** modified existing file; 2 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Preserve bounded redacted child-command diagnostics for lifecycle scripts.

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Existing local compiler/preparation/validation/Docker child boundaries use fixed concern/stage summaries and preserve exact child status and fail-stop ordering. No child output is disclosed.

**Why:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

Owning registered proof: `core-package-custody-regression`, `package-custody-regression`, `delivery-access-contract-regression`, `persistence-payload-regression`, `bootstrap-payload-regression`, `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=e071dd8db44e7f49428757f001bff426f93035a027229ea927f17e04c73ec10b after=3eb4218560e177d67a3b7a8cb0353268fd4004b13d769d193ec879d86d9c4e9f -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must failure to read a failed task's log not replace the original verification failure?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local reader/controller fixtures do not prove live stream identity, rollout success or rollback compatibility; live checks belong to a separate chat. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/shared) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L094 scripts/04.deploy/build-platform-shell-image](094-scripts-04-deploy-build-platform-shell-image.md) · [L110 scripts/04.deploy/smoke-test-platform-shell-image](110-scripts-04-deploy-smoke-test-platform-shell-image.md) · [L111 scripts/04.deploy/validate-container-boundaries](111-scripts-04-deploy-validate-container-boundaries.md) · [L112 scripts/04.deploy/inventory-deploy-control](112-scripts-04-deploy-inventory-deploy-control.md) · [L127 scripts/04.deploy](127-scripts-04-deploy.md) · [L152 scripts/04.deploy/reconcile-platform-shell-staging](152-scripts-04-deploy-reconcile-platform-shell-staging.md) · [L155 scripts/04.deploy/verify-platform-shell-deploy-readiness](155-scripts-04-deploy-verify-platform-shell-deploy-readiness.md) · [L168 scripts/04.deploy/verify-platform-shell-deployment-workflow](168-scripts-04-deploy-verify-platform-shell-deployment-workflow.md) · [L169 scripts/04.deploy/verify-platform-shell-infrastructure](169-scripts-04-deploy-verify-platform-shell-infrastructure.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 5 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
