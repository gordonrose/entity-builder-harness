<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l022
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/monitoring.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L022 — packages/core/src/monitoring

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/monitoring -->

## What you will understand

Core exposes health, metrics, tracing and logging abstractions that implementations can fulfill. Metrics count or measure; traces describe work across spans; logs retain individual events.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **11 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A metric name fails its actual guard before record is invoked. Compare that with the recording port throwing. Only the first proves recording was not attempted; a normal return still does not prove backend delivery.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** These abstractions and guards already existed. Predicate failures and helper boundaries were not uniformly available as machine-readable observations.

**After:** The existing primitives gain finite validation/boundary records and optional observers. Higher layers can tell rejected metric input from failed recording without parsing messages.

**Why this was needed:** Diagnostic work explains failure of monitoring itself. It must not recursively depend on the same failed logger or make successful business work fail.

This directory contains `documentation`, `definition`, `implementation`, `barrel-or-implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/monitoring/README.md -->

### README.md

[Open current source](../../../../../packages/core/src/monitoring/README.md) · **Snapshot:** modified existing file; 23 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for monitoring primitives and logging; read the sections `Core Monitoring Source Map`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Core Monitoring Source Map`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=8422442cdec6fd62bb571ef4d5c0e5e93e1a55d17a89dd174fa1328d6c4413f3 after=e1ec6a9f3b6672143fff52724108aa5f7a8e4f04e9eb1d0f1a2b685aec814d86 -->

<!-- course-file: packages/core/src/monitoring/boundary-diagnostics.ts -->

### boundary-diagnostics.ts

[Open current source](../../../../../packages/core/src/monitoring/boundary-diagnostics.ts) · **Snapshot:** added (absent from baseline); 45 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.monitoring.validation-rejected`, `core.monitoring.boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `coreMonitoringValidationDiagnostic`, `coreMonitoringBoundaryDiagnostic`, `coreMonitoringDiagnosticDefinitions`, `CoreMonitoringValidationDetail`, `CoreMonitoringBoundaryDetail`, `CoreMonitoringDiagnosticContext`, `CoreMonitoringDiagnosticOptions`, `required`, `coreMonitoringValidationDiagnosticRecord`, `coreMonitoringBoundaryDiagnosticRecord`.

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=8a73fc23cd35ac435e22707ac0f84554fb8b8338889077d9fa7648cff07343ef -->

<!-- course-file: packages/core/src/monitoring/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/monitoring/diagnostics.ts) · **Snapshot:** added (absent from baseline); 20 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines the selected capability records and helpers. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `MetricValidationField`, `metricValidationReasons`, `MetricValidationReason`, `MetricValidationObservation`, `MetricValidationObserver`, `metricValidationError`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=2c548e828d6f8b73b5fe479b8e74a5c08d4d7c06365bb55295438aa8b7cf9860 -->

<!-- course-file: packages/core/src/monitoring/health.ts -->

### health.ts

[Open current source](../../../../../packages/core/src/monitoring/health.ts) · **Snapshot:** modified existing file; 36 added / 26 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports monitoring primitives and logging at this layer.

**Before:** These abstractions and guards already existed. Predicate failures and helper boundaries were not uniformly available as machine-readable observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `monitoringMetadata`, `healthCheckResult`, `fixedHealthCheck`, `copyMonitoringMetadata` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core-owned closed logging/monitoring observations identify only actual guard and injected-call locations. Optional per-invocation delivery retains own location plus independently selected primary/eight; frozen/primitive throws and observer failures preserve original identity.

**Why:** Diagnostic work explains failure of monitoring itself. It must not recursively depend on the same failed logger or make successful business work fail.

Changed declaration anchors: `monitoringMetadata`, `healthCheckResult`, `fixedHealthCheck`, `copyMonitoringMetadata`.

Added import edges: `./boundary-diagnostics`, `./observations`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=d8b688effc9b751789b77cb23c34c36b295868ddf0fd9872692a2c84069767e8 after=ab4ce21db2b376b9201eb75f3924ce9fdcc81f69b1423de77e15f6a0b07c7ffe -->

<!-- course-file: packages/core/src/monitoring/identifiers.ts -->

### identifiers.ts

[Open current source](../../../../../packages/core/src/monitoring/identifiers.ts) · **Snapshot:** modified existing file; 48 added / 37 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports monitoring primitives and logging at this layer.

**Before:** These abstractions and guards already existed. Predicate failures and helper boundaries were not uniformly available as machine-readable observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `monitoringComponentName`, `monitoringComponent`, `healthCheckName`, `metricName`, `metricUnit`, `monitoringSignalName`, `traceSpanName` (4 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Existing metric name/unit/label predicates supply closed value-free observations through an optional current-invocation callback. Accepted values, TypeError class/messages, first-failure order and public module imports are retained; callback failure cannot replace validation and a prior error rethrown from input cannot establish current guard evidence.

**Why:** Diagnostic work explains failure of monitoring itself. It must not recursively depend on the same failed logger or make successful business work fail.

Changed declaration anchors: `monitoringComponentName`, `monitoringComponent`, `healthCheckName`, `metricName`, `metricUnit`, `monitoringSignalName`, `traceSpanName`, `traceId`, `spanId`, `observedName`, `observedTraceIdentifier`.

New declarations within this existing file: `observedName`, `observedTraceIdentifier`.

Added import edges: `./diagnostics`, `./boundary-diagnostics`, `./observations`.

Declarations removed or relocated: `assertTraceIdentifier`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `core-runtime`, `platform-observability-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=e5763d7351343390a231f9b4bfd776aa8a92809db3c9e7a68626acb131553f25 after=d5bf230b96215440266d2d496695199c6e055b3428581480911dea39fd8c8083 -->

<!-- course-file: packages/core/src/monitoring/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/monitoring/index.ts) · **Snapshot:** modified existing file; 5 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./diagnostics`, `./boundary-diagnostics`, `./observations`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./diagnostics`, `./boundary-diagnostics`, `./observations`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=13c1c0fe954a0a272f66e89ad14d3d93d1001bd159556687d66cdf605a287d30 after=ffe77bb7d4c6542453c9bc644c78eb6e70857e3b95997a0158f207c82e6f849d -->

<!-- course-file: packages/core/src/monitoring/metrics.ts -->

### metrics.ts

[Open current source](../../../../../packages/core/src/monitoring/metrics.ts) · **Snapshot:** modified existing file; 46 added / 28 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports monitoring primitives and logging at this layer.

**Before:** These abstractions and guards already existed. Predicate failures and helper boundaries were not uniformly available as machine-readable observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `metricLabels`, `metricPoint`, `assertMetricLabelName`, `copyMetricLabelValue` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Existing metric name/unit/label predicates supply closed value-free observations through an optional current-invocation callback. Accepted values, TypeError class/messages, first-failure order and public module imports are retained; callback failure cannot replace validation and a prior error rethrown from input cannot establish current guard evidence.

**Why:** Diagnostic work explains failure of monitoring itself. It must not recursively depend on the same failed logger or make successful business work fail.

Changed declaration anchors: `metricLabels`, `metricPoint`, `assertMetricLabelName`, `copyMetricLabelValue`.

Added import edges: `./diagnostics`, `./boundary-diagnostics`, `./observations`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=075004433c3266b1e06dfdc9b963e4e9958cfc218e3d5469956ac73863a95736 after=5a079e3e78cd86f35ae4696ba4b5069843e840188407583994aecd03d3ac7bd9 -->

<!-- course-file: packages/core/src/monitoring/observations.ts -->

### observations.ts

[Open current source](../../../../../packages/core/src/monitoring/observations.ts) · **Snapshot:** added (absent from baseline); 55 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Core-owned closed logging/monitoring observations identify only actual guard and injected-call locations. Optional per-invocation delivery retains own location plus independently selected primary/eight; frozen/primitive throws and observer failures preserve original identity. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `selectCoreMonitoringDiagnosticEvidence`, `nativeThen`, `isolate`, `observeCoreMonitoringDiagnostic`, `MonitoringObservation`.

Added import edges: `../diagnostic-catalog`, `../diagnostics/index`, `./boundary-diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=f309ddce1f047b9bb8d75ddd916ce09a42380c65b564ab9ab567ec524689d458 -->

<!-- course-file: packages/core/src/monitoring/signals.ts -->

### signals.ts

[Open current source](../../../../../packages/core/src/monitoring/signals.ts) · **Snapshot:** modified existing file; 33 added / 25 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports monitoring primitives and logging at this layer.

**Before:** These abstractions and guards already existed. Predicate failures and helper boundaries were not uniformly available as machine-readable observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `monitoringSignalDefinition` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core-owned closed logging/monitoring observations identify only actual guard and injected-call locations. Optional per-invocation delivery retains own location plus independently selected primary/eight; frozen/primitive throws and observer failures preserve original identity.

**Why:** Diagnostic work explains failure of monitoring itself. It must not recursively depend on the same failed logger or make successful business work fail.

Changed declaration anchors: `monitoringSignalDefinition`.

Added import edges: `./boundary-diagnostics`, `./observations`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=fdf193bf92e12cc056f6e05c80bc1737fc07c8e05539da7a926672944154f8b8 after=de10b47b88bb1cc387f3a8b817037fd36a0d01b23965c693214ed9d987c0abdb -->

<!-- course-file: packages/core/src/monitoring/tracing.ts -->

### tracing.ts

[Open current source](../../../../../packages/core/src/monitoring/tracing.ts) · **Snapshot:** modified existing file; 58 added / 34 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports monitoring primitives and logging at this layer.

**Before:** These abstractions and guards already existed. Predicate failures and helper boundaries were not uniformly available as machine-readable observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `traceContext`, `createInMemoryTracer`, `copyTraceSpanRecord`, `copyTraceContext`, `copyTraceAttributes` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core-owned closed logging/monitoring observations identify only actual guard and injected-call locations. Optional per-invocation delivery retains own location plus independently selected primary/eight; frozen/primitive throws and observer failures preserve original identity.

**Why:** Diagnostic work explains failure of monitoring itself. It must not recursively depend on the same failed logger or make successful business work fail.

Changed declaration anchors: `traceContext`, `createInMemoryTracer`, `copyTraceSpanRecord`, `copyTraceContext`, `copyTraceAttributes`.

Added import edges: `./boundary-diagnostics`, `./observations`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=c229af9ff0e7d74f2e3a34b62a3aa2f8db149d2faa50118040d342b973840095 after=2539cc0f49f8b0e8e159b3d8df1d132ad7a1373bc173a2084a5d1349a85817d7 -->

<!-- course-file: packages/core/src/monitoring/validation.ts -->

### validation.ts

[Open current source](../../../../../packages/core/src/monitoring/validation.ts) · **Snapshot:** modified existing file; 29 added / 15 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports monitoring primitives and logging at this layer.

**Before:** These abstractions and guards already existed. Predicate failures and helper boundaries were not uniformly available as machine-readable observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `MonitoringReject`, `assertDottedName`, `assertToken`, `assertNonEmpty`, `validationError`, `assertFiniteNumber`, `assertNonNegativeFiniteNumber` (1 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Existing metric name/unit/label predicates supply closed value-free observations through an optional current-invocation callback. Accepted values, TypeError class/messages, first-failure order and public module imports are retained; callback failure cannot replace validation and a prior error rethrown from input cannot establish current guard evidence.

**Why:** Diagnostic work explains failure of monitoring itself. It must not recursively depend on the same failed logger or make successful business work fail.

Changed declaration anchors: `MonitoringReject`, `assertDottedName`, `assertToken`, `assertNonEmpty`, `validationError`, `assertFiniteNumber`, `assertNonNegativeFiniteNumber`, `assertKnownValue`.

New declarations within this existing file: `MonitoringReject`, `validationError`.

Added import edges: `./diagnostics`, `./boundary-diagnostics`.

Owning registered proof: `core-runtime`, `platform-observability-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=8a2b18808ebbf9078650810a7a6fec6d150bf9fe6cf35a1dbef13730254db4e7 after=662f595a8fe4845a0afafc9095123ac0800c6b2a950abf91ccd080d05e263488 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What is the difference between a metric recording call returning and a backend retaining that metric?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Monitoring already existed before this project; this is not installation of a new observability stack. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/monitoring) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 11 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
