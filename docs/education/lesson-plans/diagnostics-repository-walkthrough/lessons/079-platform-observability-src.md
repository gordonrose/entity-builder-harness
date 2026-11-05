<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l079
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/observability/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L079 — platform/observability/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/observability/src -->

## What you will understand

Platform observability wraps logging, metrics, traces and readiness observation; it does not itself choose every provider or backend.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **16 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A metric recording throws and the optional diagnostic sink also rejects. Preserve the workload result and avoid recursive reporting. The bounded binding records attempts, not guaranteed delivery; suppression must not be called full coverage.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The observability slice already implemented telemetry. Several best-effort failures were swallowed or coarsely normalized, so lack of telemetry could be hard to explain.

**After:** Owned records distinguish configuration, preparation, validation, creation, recording, collection, export, flush/shutdown and wrapper failures. Bounded reporting stays independent of the failed telemetry operation.

**Why this was needed:** An agent must tell a rejected metric from a recording invocation, collection issue or exporter failure. None of those alone prove what the backend retained.

This directory contains `documentation`, `definition`, `observer`, `implementation`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/observability/src/README.md -->

### README.md

[Open current source](../../../../../platform/observability/src/README.md) · **Snapshot:** modified existing file; 71 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for diagnostics for telemetry itself; read the sections `Platform Observability Source Map`, `Detailed guide to the files`, `normalization.ts — the safety gateway for unknown values`, `logging.ts — safe writing, not log-provider selection`, `metrics.ts — small, aggregate measurements`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform Observability Source Map`; `Detailed guide to the files`; `normalization.ts — the safety gateway for unknown values`; `logging.ts — safe writing, not log-provider selection`; `metrics.ts — small, aggregate measurements`; `Metric lifecycle — evidence, not a delivery guarantee`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=f50eb902d651ee47e515aee7ec474bf0aa9f0e1506e5c837fb69b3979a00a5c7 after=05e8ebb86046f4fdc209b19a5ed42ba40d71c91e8f442d1955f1ecc22081495e -->

<!-- course-file: platform/observability/src/boundary-definitions.ts -->

### boundary-definitions.ts

[Open current source](../../../../../platform/observability/src/boundary-definitions.ts) · **Snapshot:** added (absent from baseline); 23 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `observability.boundary-failed`, `observability.diagnostic-reporting-suppressed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `platformObservationOperations`, `platformObservationBoundaryDiagnostic`, `PlatformObservationBoundaryDetail`, `platformDiagnosticReportingSuppressedDiagnostic`, `platformObservationDiagnosticDefinitions`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`, `persistence-composition`, `platform-shell-payload`, `platform-health-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=4cd36a6483f5d4d3ef77752ccf8afef631cd986809a47ba35a8f4f236f915bbe -->

<!-- course-file: platform/observability/src/boundary-observation.ts -->

### boundary-observation.ts

[Open current source](../../../../../platform/observability/src/boundary-observation.ts) · **Snapshot:** added (absent from baseline); 55 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Delivers wrapper-local and selected source observations without recursive self-reporting.

**Before:** This dedicated observation helper was absent.

**After:** Implements selected boundary/source delivery and bounded suppression control around optional reporting. It does not implement the readiness probe itself.

**Why:** A wrapper failure and source evidence must be independently retained, and failed logging must not recursively diagnose itself through the same path.

Changed declaration anchors: `PlatformObservationDiagnostics`, `reporting`, `reportPlatformObservationBoundary`, `reportPlatformObservationSources`, `reportObservation`.

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `@kanbien/platform-contracts`, `./configuration`, `./diagnostics`, `./boundary-definitions`.

Connected review context (`platform-observability-diagnostic-delivery`; this review may span several files): Validated catalog-selected reporting, safe logger provenance and bounded related-record delivery preserve exact records and existing metric labels. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=65c4eba8703b5a587d5e2314f143d519bf98ebb08bcc8dc527204c72e46af056 -->

<!-- course-file: platform/observability/src/configuration.ts -->

### configuration.ts

[Open current source](../../../../../platform/observability/src/configuration.ts) · **Snapshot:** added (absent from baseline); 114 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns provider-neutral telemetry configuration and construction observations.

**Before:** No dedicated shared module existed at this path.

**After:** Defines logical setting/reason/position records, merges bounded issue collections and separates invalid configuration from uncertain runtime construction.

**Why:** Targets and adapters can reuse policy without leaking environment contents or provider exceptions.

Changed declaration anchors: `observabilityConfigurationReasons`, `ObservabilityConfigurationReason`, `ObservabilityConfigurationIssue`, `ObservabilityConfigurationFailure`, `observabilityConfigurationSettings`, `observabilityConfigurationDiagnostic`, `observabilityConstructionDiagnostic`, `platformObservabilityDiagnosticCatalog`, `observabilityConfigurationRecord`, `mergeObservabilityConfigurationFailures`, `observabilityConstructionRecord`, `observabilityConfigurationObject` (7 more in source).

Added import edges: `@kanbien/core/config`, `@kanbien/core/diagnostics`, `@kanbien/core/shared`, `./metric-diagnostics`, `./metric-lifecycle-diagnostics`, `./readiness-diagnostics`, `./boundary-definitions`.

Connected review context (`platform-observability-configuration`; this review may span several files): Pure shared metric-series/readiness configuration predicates produce closed logical reasons and zero-based positions, independent comparisons, bounded explicit overflow and no supplied values. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`, `shell-package-source`, `platform-observability-runtime`, `cloudwatch-observability-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=5d10687ffb942c621be6f9c640e50cf5ee723359ad56b4b2193d7db43616b0a3 -->

<!-- course-file: platform/observability/src/diagnostic-log.ts -->

### diagnostic-log.ts

[Open current source](../../../../../platform/observability/src/diagnostic-log.ts) · **Snapshot:** added (absent from baseline); 18 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Marks records created by the validated diagnostic-log path.

**Before:** This internal origin-tracking helper was absent.

**After:** Tracks validated log objects privately so the safe logger can distinguish the reviewed diagnostic path from arbitrary caller-shaped log fields.

**Why:** Shape resemblance alone is not permission to bypass ordinary logging normalization.

Changed declaration anchors: `validatedLogs`, `validatedDiagnosticLog`, `hasValidatedDiagnosticLogOrigin`.

Added import edges: `@kanbien/core/logging`.

Connected review context (`platform-observability-diagnostic-delivery`; this review may span several files): Validated catalog-selected reporting, safe logger provenance and bounded related-record delivery preserve exact records and existing metric labels. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=14174749d94307c146f29f5a3aaf02cb7deac517382aab8b8b2e5ed2c9b4eb4d -->

<!-- course-file: platform/observability/src/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../platform/observability/src/diagnostics.ts) · **Snapshot:** added (absent from baseline); 104 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Selects and reports internal records through a chosen logger.

**Before:** This dedicated reporter module was absent.

**After:** Validates selected catalogs, records and context; writes the fixed platform.diagnostic.observed event; isolates throwing/rejecting sinks and reads error evidence through own data descriptors.

**Why:** Reporting must neither expose arbitrary exception data nor change the original workload outcome or replay work.

Changed declaration anchors: `intrinsicPromiseThen`, `observePlatformSinkCompletion`, `reportPlatformDiagnostic`, `createPlatformDiagnosticReporter`, `reportPlatformErrorDiagnostic`.

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/core/shared`, `./diagnostic-log`, `@kanbien/platform-contracts`.

Connected review context (`platform-observability-diagnostic-delivery`; this review may span several files): Validated catalog-selected reporting, safe logger provenance and bounded related-record delivery preserve exact records and existing metric labels. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=f26126c88d1b0570e4ea6365c317e91bd0b63576e80c39a03561d2d5c4250235 -->

<!-- course-file: platform/observability/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/observability/src/index.ts) · **Snapshot:** modified existing file; 23 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./metric-diagnostics`, `./metric-lifecycle-diagnostics`, `./diagnostics`, `./boundary-observation`, `./boundary-definitions`, `./readiness-diagnostics`, `./configuration`, `./metric-series-configuration`, `@kanbien/platform-contracts`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./metric-diagnostics`, `./metric-lifecycle-diagnostics`, `./diagnostics`, `./boundary-observation`, `./boundary-definitions`, `./readiness-diagnostics`, `./configuration`, `./metric-series-configuration`, `@kanbien/platform-contracts`.

Owning registered proof: `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=58539213b20780efdc1b7479bb9fa3ef2317f56aa9370842e9b0cb9d0ed38984 after=b4acb0d5c60ccd66c00670d256677a88f5c1b24cacb1d1944bb76ebed3b75d4e -->

<!-- course-file: platform/observability/src/logging.ts -->

### logging.ts

[Open current source](../../../../../platform/observability/src/logging.ts) · **Snapshot:** modified existing file; 47 added / 14 removed lines. These are textual counts, not a count of new features.

**What it does:** Normalizes ordinary logs and writes through an injected Core logger.

**Before:** The best-effort logging wrapper existed but some normalization/write failures disappeared.

**After:** Adds optional owned boundary observations around normalization/write and preserves the validated diagnostic-log origin path. Throwing/rejecting sinks cannot change business work.

**Why:** The agent needs the actual failed logging step without arbitrary fields being treated as trusted diagnostic data.

Changed declaration anchors: `createPlatformSafeLogger`, `writePlatformLog`.

Added import edges: `./diagnostic-log`, `./diagnostics`, `./boundary-observation`, `./boundary-definitions`.

Connected review context (`platform-observability-diagnostic-delivery`; this review may span several files): Validated catalog-selected reporting, safe logger provenance and bounded related-record delivery preserve exact records and existing metric labels. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=2d7ba79ba5e627034d9a2a57a709aeb9d90c8946acf3d781bba059a99cc087f8 after=04e3dd7ebcfbd8e56ccf7ad3f05482b6c920fda27267a08393e3f27290d224bd -->

<!-- course-file: platform/observability/src/metric-diagnostics.ts -->

### metric-diagnostics.ts

[Open current source](../../../../../platform/observability/src/metric-diagnostics.ts) · **Snapshot:** added (absent from baseline); 141 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `observability.metric-preparation-failed`, `observability.metric-rejected`, `observability.metric-instrument-creation-failed`, `observability.metric-recording-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `classification`, `metricPreparationDiagnostic`, `metricRejectionReasons`, `metricRejectionDiagnostic`, `metricCreationDiagnostic`, `metricRecordingDiagnostic`, `platformMetricDiagnosticDefinitions`, `metricPreparationRecord`, `metricRejectionRecord`, `metricCreationRecord`, `metricRecordingRecord`, `requiredRecord` (14 more in source).

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/core/monitoring`, `@kanbien/platform-contracts`, `./metric-lifecycle-diagnostics`, `./diagnostics`, `./boundary-definitions`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=8cff130c4441baf77739ee868f839339879c12655dc6d340162e0e5eeb133622 -->

<!-- course-file: platform/observability/src/metric-lifecycle-diagnostics.ts -->

### metric-lifecycle-diagnostics.ts

[Open current source](../../../../../platform/observability/src/metric-lifecycle-diagnostics.ts) · **Snapshot:** added (absent from baseline); 49 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `observability.metric-collection-issues`, `observability.metric-collection-failed`, `observability.metric-export-failed`, `observability.metric-flush-failed`, `observability.metric-shutdown-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `classification`, `metricCollectionDiagnostic`, `metricCollectionFailureDiagnostic`, `metricExportDiagnostic`, `lifecycleDetail`, `metricFlushDiagnostic`, `metricShutdownDiagnostic`, `platformMetricLifecycleDiagnosticDefinitions`, `metricCollectionIssuesRecord`, `metricCollectionFailureRecord`, `metricExportFailureRecord`, `metricLifecycleFailureRecord` (1 more in source).

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-contracts-runtime`, `platform-observability-runtime`, `diagnostic-catalog-readers`, `cloudwatch-observability-runtime`, `persistence-composition`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=f0461a0f37c9480b57fa2be832db8f14e17517ca01836b5719008b86a7f43c3b -->

<!-- course-file: platform/observability/src/metric-series-configuration.ts -->

### metric-series-configuration.ts

[Open current source](../../../../../platform/observability/src/metric-series-configuration.ts) · **Snapshot:** added (absent from baseline); 78 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Validates declared metric-series policy.

**Before:** Series checks were not shared through this dedicated module.

**After:** Provides indexed validation reused by adapters for supported labels, cardinality and bucket declarations.

**Why:** One upstream rule avoids divergent adapter checks; it is not a redesign of metric collection.

Changed declaration anchors: `PlatformMetricSeries`, `validatePlatformMetricSeries`.

Added import edges: `@kanbien/core/config`, `@kanbien/core/monitoring`, `@kanbien/core/shared`, `./configuration`.

Connected review context (`platform-observability-configuration`; this review may span several files): Pure shared metric-series/readiness configuration predicates produce closed logical reasons and zero-based positions, independent comparisons, bounded explicit overflow and no supplied values. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=54219151ed79362d37acaa6f9f731a53410d19b709285c1a02f57ebdd6667170 -->

<!-- course-file: platform/observability/src/metrics.ts -->

### metrics.ts

[Open current source](../../../../../platform/observability/src/metrics.ts) · **Snapshot:** modified existing file; 113 added / 25 removed lines. These are textual counts, not a count of new features.

**What it does:** Prepares and records metrics, including request/job/health timing helpers.

**Before:** The helpers already measured work, but preparation, raw access and recording failures were not precisely separated.

**After:** Distinguishes exact Core validation, raw-access/clock preparation, trusted same-port creation evidence and invocation failure. Independent bounded diagnostic bindings preserve void return and no-replay behavior.

**Why:** Metric-recording failure must be diagnosable without treating it as a business failure or confusing it with export.

Changed declaration anchors: `intrinsicPromiseThen`, `recordPlatformMetric`, `recordPlatformRequestMetric`, `recordPlatformJobMetric`, `recordPlatformHealthMetric`, `elapsedMilliseconds`.

New declarations within this existing file: `intrinsicPromiseThen`.

Added import edges: `@kanbien/platform-contracts`, `./metric-diagnostics`, `./boundary-observation`, `./boundary-definitions`.

Connected review context (`platform-local-metric-diagnostics`; this review may span several files): Four additive code-owned definitions distinguish current Core preparation predicates and precise raw-access locations, trusted same-port adapter rejections, creation not-attempted and invocation unknown effect. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=c16c0a94b9d908ee2f41fc25e896390e3f5dfce56e0a0caa1c11c371c09bf65c after=1e4274c005086f4cf100640c2d83faeaf8e0a0868699cce8fb4cb5d95b88e552 -->

<!-- course-file: platform/observability/src/normalization.ts -->

### normalization.ts

[Open current source](../../../../../platform/observability/src/normalization.ts) · **Snapshot:** modified existing file; 34 added / 32 removed lines. These are textual counts, not a count of new features.

**What it does:** Normalizes unknown log/trace values and classifies safe errors.

**Before:** The existing normalizer used its older error-name/code projection.

**After:** Retains bounded normalization and adds reviewed finite error-class selection rather than treating arbitrary name/code strings as approved telemetry classes.

**Why:** An arbitrary code string may contain sensitive text or create unbounded metric classes.

Changed declaration anchors: `PlatformValueNormalizationOptions`, `normalizePlatformError`, `platformErrorClass`, `nativeErrorClass`, `createNormalizationState`, `normalizeUnknown`.

New declarations within this existing file: `nativeErrorClass`.

Added import edges: `@kanbien/platform-contracts`.

Declarations removed or relocated: `hasStringProperty`. Read the current exports/consumer tests before assuming the public API was removed.

Connected review context (`platform-observability-error-classification`; this review may span several files): The explicitly approved finite classification policy preserves normalized error field structure while admitting only actual native runtime-type groups and exact owner/app-declared members. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-observability-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6784b333d32858be208fbc61c39403a315c837b76e18b15cea85958daecd257f after=36d692014649da9442337e2a44ce96c3a4d564e6cc6069332bf0bff324945a18 -->

<!-- course-file: platform/observability/src/readiness-diagnostics.ts -->

### readiness-diagnostics.ts

[Open current source](../../../../../platform/observability/src/readiness-diagnostics.ts) · **Snapshot:** added (absent from baseline); 39 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `observability.readiness-configuration-invalid`, `observability.readiness-probe-not-ready`, `observability.readiness-probe-threw`, `observability.readiness-probe-rejected`, `observability.readiness-probe-deadline-observed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `classification`, `readinessConfigurationDiagnostic`, `readinessNotReadyDiagnostic`, `readinessInvocationDiagnostic`, `readinessRejectionDiagnostic`, `readinessDeadlineDiagnostic`, `platformReadinessDiagnosticDefinitions`, `readinessDiagnosticRecord`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=524d8cd19dad5c3c2dc6e85dd2bf51b6bb28c944ab8711d052b13e623f980459 -->

<!-- course-file: platform/observability/src/readiness-observation.ts -->

### readiness-observation.ts

[Open current source](../../../../../platform/observability/src/readiness-observation.ts) · **Snapshot:** modified existing file; 131 added / 29 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs bounded readiness probes and emits the existing observation event/gauge.

**Before:** The probe and event path existed, but timeout/throw/rejection/not-ready could collapse into similar outcomes.

**After:** Reports the observed deadline or failure type and retains selected upstream evidence while preserving bounded wait and existing event/metric behavior.

**Why:** A deadline is not transport evidence, and timeout observation does not establish cancellation.

Changed declaration anchors: `intrinsicPromiseThen`, `PlatformReadinessProbeResult`, `PlatformReadinessObserverOptions`, `createPlatformReadinessObserver`, `emitPlatformReadinessObservation`, `boundedProbe`, `ProbeObservation`, `requiredReadinessEvent`, `checkedReadinessEvent`, `allowedDiagnosticCode`.

New declarations within this existing file: `intrinsicPromiseThen`, `ProbeObservation`, `checkedReadinessEvent`.

Added import edges: `@kanbien/core/diagnostics`, `./diagnostics`, `./metric-diagnostics`, `./readiness-diagnostics`, `./boundary-observation`, `./boundary-definitions`.

Connected review context (`platform-observability-diagnostic-delivery`; this review may span several files): Validated catalog-selected reporting, safe logger provenance and bounded related-record delivery preserve exact records and existing metric labels. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=48ffae8dac2f1fc6768d9c0854ae87defcc0dad6b4405079315adbbc0af8fcb2 after=92c2f4116524b117f0d5096aa124498cf98133a6383399151d934fa96bf4ade6 -->

<!-- course-file: platform/observability/src/tracing.ts -->

### tracing.ts

[Open current source](../../../../../platform/observability/src/tracing.ts) · **Snapshot:** modified existing file; 79 added / 41 removed lines. These are textual counts, not a count of new features.

**What it does:** Normalizes trace attributes and safely starts/ends injected spans.

**Before:** Trace helpers already existed with best-effort failure handling.

**After:** Observes attribute/start/returned-span/end boundaries and selected sources, preserving existing profile permission and optional behavior.

**Why:** A failed start, invalid returned span and failed end are different observations; none alone proves remote trace delivery.

Changed declaration anchors: `platformTraceFields`, `platformTraceAttributes`, `startPlatformTraceSpan`, `endPlatformTraceSpan`.

Added import edges: `@kanbien/platform-contracts`, `./diagnostics`, `./boundary-observation`, `./boundary-definitions`.

Connected review context (`platform-observability-diagnostic-delivery`; this review may span several files): Validated catalog-selected reporting, safe logger provenance and bounded related-record delivery preserve exact records and existing metric labels. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6614ba5f5fe2cc9acbf1aad4febea00670d8852713bdb958d420fc99b9351824 after=9e162b08d91e859c7a841eaaf043ff575243a638ab2c3aae8bd85f513c2c24b8 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why would sending a logger-failed diagnostic through the same failed logger recursively be dangerous?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No SDK or metrics backend is introduced here. SDK-internal failures that never cross observable public boundaries cannot be invented as observed facts. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/observability/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L077 platform/observability](077-platform-observability.md) · [L078 platform/observability/contracts](078-platform-observability-contracts.md) · [L080 platform/observability/tests](080-platform-observability-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 16 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
