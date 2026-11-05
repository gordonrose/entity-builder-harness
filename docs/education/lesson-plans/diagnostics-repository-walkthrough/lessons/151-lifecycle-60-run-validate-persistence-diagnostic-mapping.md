<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l151
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L151 — scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping -->

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

This directory contains `implementation`, `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.py -->

### script.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.py) · **Snapshot:** modified existing file; 9 added / 9 removed lines. These are textual counts, not a count of new features.

**What it does:** Fail closed when a scope omits, weakens, or makes unsafe its persistence diagnostic mapping.

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Retain validated source/content and operation-bound persistence/security records, require a TLS primary for bounded peer companions and preserve historical envelopes and unsuccessful/unknown outcomes without replay. Recovery mapping covers only the runtime-exported operation family; additive configuration definitions cannot require, extend or substitute for an operation mapping.

**Why:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

Current reading anchors (not all are new): `load`, `text`, `add`, `persistence_dependencies`, `persistence_workload_usage`, `health_workloads`, `binding_ids`, `validate_not_applicable`, `validate_entry`, `validate_declared` (1 more in source).

Owning registered proof: `diagnostic-catalog-readers`, `deployment-operation-diagnostics-regression`, `persistence-diagnostic-mapping-regression`, `restore-connection-diagnostics`, `persistence-payload-regression`, `persistence-provider-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=8ab72f0083a668a6f0f3e2647eb501c1336fc96975417b340cff41fc62ee4584 after=395c2c3405206309f7d4a6292bed6c5f789a594234fccf3ced4be9a44b72aa46 -->

<!-- course-file: scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/smoke-test.py -->

### smoke-test.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/smoke-test.py) · **Snapshot:** modified existing file; 13 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for deployment controllers and evidence readers.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Retain validated source/content and operation-bound persistence/security records, require a TLS primary for bounded peer companions and preserve historical envelopes and unsuccessful/unknown outcomes without replay. Recovery mapping covers only the runtime-exported operation family; additive configuration definitions cannot require, extend or substitute for an operation mapping.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Current reading anchors (not all are new): `mappings`, `valid_documents`, `run`, `require`, `finding`, `main`.

Owning registered proof: `diagnostic-catalog-readers`, `deployment-operation-diagnostics-regression`, `persistence-diagnostic-mapping-regression`, `restore-connection-diagnostics`, `persistence-payload-regression`, `persistence-provider-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f64b03d9a8345eb5e8b83960f015eec0e27ba42aa6f9cec3d6c0133dfa81097b after=7c14207823a5179515b747bc4a96a5c1f38714b0d7bc5afd35b4868089d62d19 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must failure to read a failed task's log not replace the original verification failure?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local reader/controller fixtures do not prove live stream identity, rollout success or rollback compatibility; live checks belong to a separate chat. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
