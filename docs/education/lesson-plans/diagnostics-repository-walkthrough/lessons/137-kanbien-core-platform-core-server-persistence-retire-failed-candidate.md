<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l137
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L137 — scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate -->

## What you will understand

Controllers orchestrate existing deployment and verification steps; readers interpret the receipts and task output on which later decisions rely.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A verifier task fails; its safe existing log record identifies the operation. The controller may retain that checked record, but a failed or partial log read cannot turn failure into success. A remote side effect remains uncertain unless separate evidence proves it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress.

**After:** Readers validate selected generated contracts and preserve primary failure plus bounded source observations. The failed-verifier path permits one bounded read of the failed task's existing stream after exact identity validation; successful verification remains unchanged.

**Why this was needed:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

This directory contains `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate/script.py -->

### script.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate/script.py) · **Snapshot:** modified existing file; 22 added / 11 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements the owning deployment controllers and evidence readers command or helper.

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Reviewed prepare/create/deploy/retire boundaries retain actual parameter and provider call order, finite code/status observations and known operation identity without echoing native failures, private child output or rejected values. Retire distinguishes positively classified missing from unavailable provider observations; failed submit/read responses do not establish no effect.

**Why:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

Current reading anchors (not all are new): `aws`, `report`, `failed_candidate_database`, `no_active_service`, `protected_target_database`, `observed_retirement`, `main`, `protected_target_database_after_unlock`.

Owning registered proof: `persistence-provider-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=a2630fc71aee9fec9e3328af7845dd55f84a8faeb9696f1469704b234d2c3488 after=11309d992a55957edcbd37a4138b4a8a92d44dd70d2de947b2a3c6fd62a6068e -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must failure to read a failed task's log not replace the original verification failure?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local reader/controller fixtures do not prove live stream identity, rollout success or rollback compatibility; live checks belong to a separate chat. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L131 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence](131-targets-kanbien-core-platform-core-server-persistence.md) · [L132 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface](132-kanbien-core-platform-core-server-persistence-apply-restoration-verifier-surface.md) · [L133 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set](133-kanbien-core-platform-core-server-persistence-create-change-set.md) · [L134 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate](134-kanbien-core-platform-core-server-persistence-deploy-candidate.md) · [L135 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate](135-kanbien-core-platform-core-server-persistence-prepare-candidate.md) · [L136 scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/reconcile-rds-log-export-surface](136-kanbien-core-platform-core-server-persistence-reconcile-rds-log-export-surface.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
