<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l081
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/observability/cloudwatch.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L081 — platform/adapters/aws/observability/cloudwatch

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/observability/cloudwatch -->

## What you will understand

The CloudWatch observability adapter connects the provider-neutral ports to the already-present OpenTelemetry SDK and selected export behavior.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Public collect returns an object containing collection errors. Preserve that object and report the safe issue count. Do not claim all metrics were lost, and do not copy the SDK error array into logs.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The SDK integration already existed. Configuration and public collection/export/lifecycle failures were not consistently distinguished for agents.

**After:** Configuration validation and lifecycle observations wrap supported public boundaries. Collection issues, collection rejection, export, flush and shutdown each retain their actual meaning and uncertainty.

**Why this was needed:** A successful call to record is not proof that a collector accepted or exported a point. Diagnosing the adapter requires observing the later boundaries that the SDK actually exposes.

This directory contains `documentation`, `dependency`, `compiler` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/observability/cloudwatch/README.md -->

### README.md

[Open current source](../../../../../platform/adapters/aws/observability/cloudwatch/README.md) · **Snapshot:** modified existing file; 69 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for the existing opentelemetry adapter; read the sections `AWS CloudWatch OpenTelemetry Metrics Adapter`, `Files`, `What the adapter does`, `Guardrails`, `How target composition consumes it`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `AWS CloudWatch OpenTelemetry Metrics Adapter`; `Files`; `What the adapter does`; `Guardrails`; `How target composition consumes it`; `Verification`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=3cfd1fae3a54ecd501ca307ebe13003f46037ef702b30ff14a4f62138bd2940b after=46098cfd63f8f9f1a216e06836e0f3951179a2542c6b8538565e5995b326917b -->

<!-- course-file: platform/adapters/aws/observability/cloudwatch/package.json -->

### package.json

[Open current source](../../../../../platform/adapters/aws/observability/cloudwatch/package.json) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Declares package dependencies used by the changed code.

**Before:** The package did not declare the newly added internal import edge(s).

**After:** Adds `@kanbien/platform-observability` to the package graph.

**Why:** Explicit dependencies keep source imports, build resolution and packaged runtime agreement honest. This is not an unrelated library installation.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=9f88e96b5562bf3cf5be3062198c7c15b8dddc09c56cf632ae0fb4b93ae40a77 after=3e12ce179aa9718d791e7523f40c772b906d4fbfe271624a407e852ad75f6e0a -->

<!-- course-file: platform/adapters/aws/observability/cloudwatch/tsconfig.runtime-test.json -->

### tsconfig.runtime-test.json

[Open current source](../../../../../platform/adapters/aws/observability/cloudwatch/tsconfig.runtime-test.json) · **Snapshot:** modified existing file; 2 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Configures which sources/dependencies the test compiler can resolve.

**Before:** The existing compiler scope did not include all newly referenced diagnostic/security dependencies.

**After:** Extends the relevant compilation inputs or aliases for the tests; the JSON diff is the exact declaration change.

**Why:** Runtime tests must exercise the implementation that consumers actually import, rather than fail resolution or omit the new modules.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=ca58d05df31a1d5a7d5710364f24e256948b4f8a7b5170a325e7c2a5a2658241 after=74ea0b569f7991275de6f54866ad50da97979ce4ad7fe72f5d53cf9aabd46902 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: How can collection return normally and still contain problems?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Do not read private SDK state or claim visibility into swallowed internal failures. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/observability/cloudwatch) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L082 platform/adapters/aws/observability/cloudwatch/src](082-observability-cloudwatch-src.md) · [L083 platform/adapters/aws/observability/cloudwatch/tests](083-observability-cloudwatch-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
