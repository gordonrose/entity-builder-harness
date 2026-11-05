<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l083
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/observability/cloudwatch/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L083 — platform/adapters/aws/observability/cloudwatch/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/observability/cloudwatch/tests -->

## What you will understand

The CloudWatch observability adapter connects the provider-neutral ports to the already-present OpenTelemetry SDK and selected export behavior.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **4 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Public collect returns an object containing collection errors. Preserve that object and report the safe issue count. Do not claim all metrics were lost, and do not copy the SDK error array into logs.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The SDK integration already existed. Configuration and public collection/export/lifecycle failures were not consistently distinguished for agents.

**After:** Configuration validation and lifecycle observations wrap supported public boundaries. Collection issues, collection rejection, export, flush and shutdown each retain their actual meaning and uncertainty.

**Why this was needed:** A successful call to record is not proof that a collector accepted or exported a point. Diagnosing the adapter requires observing the later boundaries that the SDK actually exposes.

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/observability/cloudwatch/tests/cloudwatch-otel-adapter-boundaries.test.mjs -->

### cloudwatch-otel-adapter-boundaries.test.mjs

[Open current source](../../../../../platform/adapters/aws/observability/cloudwatch/tests/cloudwatch-otel-adapter-boundaries.test.mjs) · **Snapshot:** modified existing file; 5 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for the existing opentelemetry adapter.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Pure endpoint, region, resource and timing predicates compose the platform series validator before SDK allocation. Existing constructor APIs retain RangeError with validated safe detail; accepted plain configuration is preserved.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `allowedSourceImportPattern`.

Owning registered proof: `cloudwatch-observability-runtime`, `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ca3593dc7a89e955d7c035c6429391b7b41cd7236a9cfa1ab649b10201b0c406 after=90c2380548e12cb2f4c1df1607e6eb315d3abafaa6b48d2c96e2956a054e704e -->

<!-- course-file: platform/adapters/aws/observability/cloudwatch/tests/cloudwatch-otel-adapter-runtime.test.ts -->

### cloudwatch-otel-adapter-runtime.test.ts

[Open current source](../../../../../platform/adapters/aws/observability/cloudwatch/tests/cloudwatch-otel-adapter-runtime.test.ts) · **Snapshot:** modified existing file; 204 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for the existing opentelemetry adapter.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Pure endpoint, region, resource and timing predicates compose the platform series validator before SDK allocation. Existing constructor APIs retain RangeError with validated safe detail; accepted plain configuration is preserved.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `configuration`, `rejectedOptions`, `providerGetterReads`, `hostileOptions`, `basic`, `creations`, `invocations`, `isolatedMeter`, `checkedPort`, `gaugeSeries`, `gaugePort`, `sourceNine` (23 more in source).

New declarations within this existing file: `configuration`, `rejectedOptions`, `providerGetterReads`, `hostileOptions`, `basic`, `creations`, `invocations`, `isolatedMeter` (27 more in source).

Added import edges: `@kanbien/platform-observability`, `@opentelemetry/sdk-metrics`, `@kanbien/core/diagnostics`.

Owning registered proof: `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=7ef94c20fd8be1186d15cb161dfe05f0d759cb8d97c2cf85394f4a08c3a0513e after=afa01f710833e82cfa2bf77c94fb72ecb8122f750ebcace97681c4677b9e3005 -->

<!-- course-file: platform/adapters/aws/observability/cloudwatch/tests/cloudwatch-otel-lifecycle-runtime.test.ts -->

### cloudwatch-otel-lifecycle-runtime.test.ts

[Open current source](../../../../../platform/adapters/aws/observability/cloudwatch/tests/cloudwatch-otel-lifecycle-runtime.test.ts) · **Snapshot:** added (absent from baseline); 360 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for the existing opentelemetry adapter.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Pure endpoint, region, resource and timing predicates compose the platform series validator before SDK allocation. Existing constructor APIs retain RangeError with validated safe detail; accepted plain configuration is preserved.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `sdkBoundaryBaseline`, `capture`, `envelope`, `wrapperPreservation`, `collectionAndSdkObservation`, `httpExporterObservation`, `runnerDispatchProof`, `independentPublicSources`, `main`.

Added import edges: `node:assert/strict`, `node:http`, `node:child_process`, `node:fs`, `node:os`, `node:path`, `@opentelemetry/resources`, `@opentelemetry/sdk-metrics`, `@kanbien/core/diagnostics`, `@kanbien/core/monitoring` (more in source).

Owning registered proof: `cloudwatch-observability-runtime`, `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=5d9fc0ed4a94e5de5d8d9dd48ac4c1c01908fe6df31ea133619a096da3df05eb -->

<!-- course-file: platform/adapters/aws/observability/cloudwatch/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../platform/adapters/aws/observability/cloudwatch/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 7 added / 7 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Declarations removed or relocated: `result`. Read the current exports/consumer tests before assuming the public API was removed.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=fb2f575ac2e892c0f46f0f5f14941d399ad2df5439f00161185f2ba351ff2706 after=2e6b4f57516d5af5555fb780e0d2aeacaffdfe390863d98164a733443adb7e90 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: How can collection return normally and still contain problems?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Do not read private SDK state or claim visibility into swallowed internal failures. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/observability/cloudwatch/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L081 platform/adapters/aws/observability/cloudwatch](081-aws-observability-cloudwatch.md) · [L082 platform/adapters/aws/observability/cloudwatch/src](082-observability-cloudwatch-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 4 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
