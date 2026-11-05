<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l082
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/observability/cloudwatch/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L082 — platform/adapters/aws/observability/cloudwatch/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/observability/cloudwatch/src -->

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

This directory contains `implementation`, `barrel-or-implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/observability/cloudwatch/src/configuration.ts -->

### configuration.ts

[Open current source](../../../../../platform/adapters/aws/observability/cloudwatch/src/configuration.ts) · **Snapshot:** added (absent from baseline); 46 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports the existing opentelemetry adapter at this layer.

**Before:** This implementation/helper file was absent at the baseline; its surrounding capability may already have existed.

**After:** Updates `validateCloudWatchOtelMetricsConfiguration` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Pure endpoint, region, resource and timing predicates compose the platform series validator before SDK allocation. Existing constructor APIs retain RangeError with validated safe detail; accepted plain configuration is preserved.

**Why:** A successful call to record is not proof that a collector accepted or exported a point. Diagnosing the adapter requires observing the later boundaries that the SDK actually exposes.

Changed declaration anchors: `validateCloudWatchOtelMetricsConfiguration`.

Added import edges: `@kanbien/core/config`, `@kanbien/core/shared`, `@kanbien/platform-observability`, `./index`.

Owning registered proof: `cloudwatch-observability-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=37d8dfa29e1212d723a1addff53dcf47bc3bcf8d4d5eb27ac875a56376698854 -->

<!-- course-file: platform/adapters/aws/observability/cloudwatch/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/adapters/aws/observability/cloudwatch/src/index.ts) · **Snapshot:** modified existing file; 106 added / 114 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports the existing opentelemetry adapter at this layer.

**Before:** The SDK integration already existed. Configuration and public collection/export/lifecycle failures were not consistently distinguished for agents. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `CloudWatchOtelMetricSeries`, `createCloudWatchOtelMetricsRuntime`, `createCloudWatchOtelMetrics`, `buildCloudWatchOtelMetrics`, `cloudWatchOtelMetricViews`, `assertPointMatchesSeries`, `validateCloudWatchOtelMetricsOptions` (2 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Pure endpoint, region, resource and timing predicates compose the platform series validator before SDK allocation. Existing constructor APIs retain RangeError with validated safe detail; accepted plain configuration is preserved.

**Why:** A successful call to record is not proof that a collector accepted or exported a point. Diagnosing the adapter requires observing the later boundaries that the SDK actually exposes.

Changed declaration anchors: `CloudWatchOtelMetricSeries`, `createCloudWatchOtelMetricsRuntime`, `createCloudWatchOtelMetrics`, `buildCloudWatchOtelMetrics`, `cloudWatchOtelMetricViews`, `assertPointMatchesSeries`, `validateCloudWatchOtelMetricsOptions`, `validateMetricSeries`, `runtimeLifecycle`.

New declarations within this existing file: `buildCloudWatchOtelMetrics`, `runtimeLifecycle`.

Added import edges: `@kanbien/platform-observability`, `./lifecycle-observation`, `./configuration`.

Declarations removed or relocated: `assertNonEmpty`, `assertPositiveInteger`, `assertAwsRegion`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `cloudwatch-observability-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=c2050120b72150e335e67706306249696bf1c9286c0a7823944e1c178f5ddf21 after=00a57ce96a56f52df7a2916826a26de09b386218f34a4d77c41450853bd2ca45 -->

<!-- course-file: platform/adapters/aws/observability/cloudwatch/src/lifecycle-observation.ts -->

### lifecycle-observation.ts

[Open current source](../../../../../platform/adapters/aws/observability/cloudwatch/src/lifecycle-observation.ts) · **Snapshot:** added (absent from baseline); 173 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Public SDK collection results/rejections, export callbacks/throws and exporter/runtime lifecycle failures are observed without changing SDK call counts, arguments, receiver, result/error identity, optional selectors, timeout or repeated shutdown semantics. Literal expectations, real pinned SDK and local HTTP fixtures prove failed export persists through resolved flush, returned errors do not imply total loss, timeout is not cancellation, independent bounded reporting cannot alter SDK outcomes and no native/metric values are emitted. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `intrinsicPromiseThen`, `ObservedPeriodicMetricReader`, `observeMetricExporter`, `observeMetricLifecycle`, `failureReason`, `safely`, `metricObservationContext`, `CloudWatchConstructionObservation`.

Added import edges: `@opentelemetry/sdk-metrics`, `@kanbien/platform-observability`.

Owning registered proof: `cloudwatch-observability-runtime`, `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=32f50621d1a05c8cd4381e41120018d059f2492d5b32ee85bff4faa6b133574b -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: How can collection return normally and still contain problems?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Do not read private SDK state or claim visibility into swallowed internal failures. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/observability/cloudwatch/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L081 platform/adapters/aws/observability/cloudwatch](081-aws-observability-cloudwatch.md) · [L083 platform/adapters/aws/observability/cloudwatch/tests](083-observability-cloudwatch-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
