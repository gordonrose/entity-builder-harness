<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l126
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder .agentic/04.deploy/schemas.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L126 — .agentic/04.deploy/schemas

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: .agentic/04.deploy/schemas -->

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

This directory contains `documentation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: .agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.guide.md -->

### deployment-operation-diagnostic.v1.guide.md

[Open current source](../../../../../.agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.guide.md) · **Snapshot:** modified existing file; 46 added / 7 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for deployment controllers and evidence readers; read the sections `Deployment Operation Diagnostic v1 Guide`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Deployment Operation Diagnostic v1 Guide`.

Proving boundary: source/document consistency and the actual evidence referenced by this record. Reading a plan or finding a valid metadata header is not runtime proof.

<!-- course-source-sha256: before=07db56105c60556b57e15d4150c0a37dab52853080a3bdbc11202b926b9423c3 after=7d001a458836ceb4d0af3dd9a53dccd1a450715a425a8b307a95e945a1d5e024 -->

<!-- course-file: .agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.schema.yml -->

### deployment-operation-diagnostic.v1.schema.yml

[Open current source](../../../../../.agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.schema.yml) · **Snapshot:** modified existing file; 34 added / 9 removed lines. These are textual counts, not a count of new features.

**What it does:** Machine-readable rule/schema or workflow declaration.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Reconciles the declaration for deployment controllers and evidence readers; read the sections `id: deploy.schema.deployment-operation-diagnostic.v1`, `version: 2`, `status: draft`, `created_on: "2026-10-25"`, `updated_on: "2026-10-31"`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `agentic-artifact:`; `schema: agentic-artifact/v3`; `id: deploy.schema.deployment-operation-diagnostic.v1`; `version: 2`; `status: draft`; `created_on: "2026-10-25"`.

Owning registered proof: `diagnostic-catalog-readers`, `deployment-operation-diagnostics-regression`, `persistence-diagnostic-mapping-regression`, `restore-connection-diagnostics`, `persistence-payload-regression`, `persistence-provider-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=d6acea39517ef253785a1f8afd9f166b2037be3f2b63f7226f766292a80a9e4d after=3886a64cf82ac17440b8ac49323427a927480596ec79933d1e714abcbd2e2590 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must failure to read a failed task's log not replace the original verification failure?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local reader/controller fixtures do not prove live stream identity, rollout success or rollback compatibility; live checks belong to a separate chat. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../.agentic/04.deploy/schemas) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
