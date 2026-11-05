<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l070
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/workers.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L070 — platform/workers

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/workers -->

## What you will understand

Workers receive jobs, validate payloads, coordinate durable claims, invoke handlers and settle delivery. Queue adapters implement transport operations.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A handler returns successfully, then acknowledgement throws. Describe the observed acknowledgement invocation with uncertain effect. Do not report handler rejection or replay it merely to obtain a diagnostic.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Worker processing and queues already existed. Invalid payload, lost claim, handler failure and acknowledgement uncertainty could lose their distinct locations and source facts.

**After:** Closed worker/queue records describe actual validation, coordination, handler and settlement boundaries. Optional reporting preserves attempt multiplicity, profile opt-outs and original business results.

**Why this was needed:** A failed acknowledgement may follow successful business work. Treating it as handler-not-run could duplicate effects on recovery.

This directory contains `documentation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/workers/README.md -->

### README.md

[Open current source](../../../../../platform/workers/README.md) · **Snapshot:** modified existing file; 58 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for worker processing and queue delivery; read the sections `Platform Workers`, `Responsibility map`, `Optional durable-outbox processing`, `Runtime and process evidence`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform Workers`; `Responsibility map`; `Optional durable-outbox processing`; `Runtime and process evidence`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=8eb68e511e6004859665005d439a5478dc198170e8daf29bdd812c23f7d90841 after=195585c3739b78fc1cf9fd4f9f7d510b1b83e4761d5a8a3be0c36421fc97b510 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What must an agent investigate before retrying a delivery whose settlement failed?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** This is not a new exactly-once policy, retry policy or queue backend. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/workers) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L008 platform/config](008-platform-config.md) · [L023 platform/contracts](023-platform-contracts.md) · [L030 platform/runtime](030-platform-runtime.md) · [L034 platform/testing](034-platform-testing.md) · [L037 platform/server](037-platform-server.md) · [L043 platform/health](043-platform-health.md) · [L053 platform/security](053-platform-security.md) · [L058 platform/persistence](058-platform-persistence.md) · [L071 platform/workers/contracts](071-platform-workers-contracts.md) · [L072 platform/workers/src](072-platform-workers-src.md) · [L073 platform/workers/tests](073-platform-workers-tests.md) · [L077 platform/observability](077-platform-observability.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
