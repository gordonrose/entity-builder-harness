<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l072
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/workers/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L072 — platform/workers/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/workers/src -->

## What you will understand

Workers receive jobs, validate payloads, coordinate durable claims, invoke handlers and settle delivery. Queue adapters implement transport operations.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **9 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A handler returns successfully, then acknowledgement throws. Describe the observed acknowledgement invocation with uncertain effect. Do not report handler rejection or replay it merely to obtain a diagnostic.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Worker processing and queues already existed. Invalid payload, lost claim, handler failure and acknowledgement uncertainty could lose their distinct locations and source facts.

**After:** Closed worker/queue records describe actual validation, coordination, handler and settlement boundaries. Optional reporting preserves attempt multiplicity, profile opt-outs and original business results.

**Why this was needed:** A failed acknowledgement may follow successful business work. Treating it as handler-not-run could duplicate effects on recovery.

This directory contains `documentation`, `definition`, `implementation`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/workers/src/README.md -->

### README.md

[Open current source](../../../../../platform/workers/src/README.md) · **Snapshot:** modified existing file; 34 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for worker processing and queue delivery; read the sections `Platform Worker Source Map`, `Job lineage and traces`, `Durable outbox mode`, `Boundary evidence, not delivery-policy changes`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform Worker Source Map`; `Job lineage and traces`; `Durable outbox mode`; `Boundary evidence, not delivery-policy changes`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=bd0d6c8afc50b462b87d56c1aab74da73d6febd02a98be5012bce724ad33e733 after=775798b0a861a3196f3bce9a4347f38ee480141f4996ce7226338816235fb419 -->

<!-- course-file: platform/workers/src/configuration-diagnostics.ts -->

### configuration-diagnostics.ts

[Open current source](../../../../../platform/workers/src/configuration-diagnostics.ts) · **Snapshot:** added (absent from baseline); 13 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines the selected capability records and helpers. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `workerConfigurationFields`, `workerConfigurationReasons`, `platformWorkerConfigurationDiagnostic`, `workerConfigurationDiagnosticRecord`.

Added import edges: `@kanbien/platform-config`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`, `platform-shell-payload`, `sqs-queue-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=75d9d8e25e2ce919bb455cb0adac11c67b0a8eddb0926db8e21bcb2bceff4f8d -->

<!-- course-file: platform/workers/src/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../platform/workers/src/diagnostics.ts) · **Snapshot:** added (absent from baseline); 129 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `platform-worker.delivery-failed`, `platform-worker.boundary-failed`, `platform-worker.delivery-rejected`, `platform-worker.coordination-observed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `workerDiagnosticErrorCodes`, `platformWorkerDiagnostic`, `platformWorkerBoundaryDiagnostic`, `platformWorkerDeliveryRejectedDiagnostic`, `platformWorkerCoordinationDiagnostic`, `platformWorkerDeliveryBoundaryDiagnostic`, `WorkerDeliveryBoundaryDetail`, `workerDeliveryRejectedRecord`, `workerCoordinationRecord`, `workerDeliveryBoundaryRecord`, `requiredRecord`, `platformWorkerDiagnosticCatalog` (6 more in source).

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `@kanbien/platform-contracts`, `@kanbien/platform-observability`, `./configuration-diagnostics`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`, `shell-package-source`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=1da8ce51783ee0b83bd3aa894f84e4c4b6acb3bbc577e18979fb4b08a8117946 -->

<!-- course-file: platform/workers/src/errors.ts -->

### errors.ts

[Open current source](../../../../../platform/workers/src/errors.ts) · **Snapshot:** modified existing file; 13 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports worker processing and queue delivery at this layer.

**Before:** Worker processing and queues already existed. Invalid payload, lost claim, handler failure and acknowledgement uncertainty could lose their distinct locations and source facts. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformWorkerError`, `workerFailure`, `workerError` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** A failed acknowledgement may follow successful business work. Treating it as handler-not-run could duplicate effects on recovery.

Changed declaration anchors: `PlatformWorkerError`, `workerFailure`, `workerError`.

Added import edges: `@kanbien/core/diagnostics`, `./diagnostics`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=5ebc819906c47dd5791dab5847e0cd32dedc84c31133dc3639da69b038fa94b0 after=65f4633cd489330a567413eb6d9a5052ab8edfbe5fd5197f40ea6ef08220b47e -->

<!-- course-file: platform/workers/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/workers/src/index.ts) · **Snapshot:** modified existing file; 6 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./diagnostics`, `./configuration-diagnostics`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./diagnostics`, `./configuration-diagnostics`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=028a734dd30a9b2bd715e689f627c1dbb7d2ab9b560faa806954ade7ba8a62fc after=d1c69543f320f8e407c9dd5239a701d751d92089f2d6fd5df9d7b5ba1e5f93be -->

<!-- course-file: platform/workers/src/main.ts -->

### main.ts

[Open current source](../../../../../platform/workers/src/main.ts) · **Snapshot:** modified existing file; 44 added / 8 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports worker processing and queue delivery at this layer.

**Before:** Worker processing and queues already existed. Invalid payload, lost claim, handler failure and acknowledgement uncertainty could lose their distinct locations and source facts. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformWorkerProcessOptions`, `startPlatformWorkerProcess`, `installShutdownHandlers` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** A failed acknowledgement may follow successful business work. Treating it as handler-not-run could duplicate effects on recovery.

Changed declaration anchors: `PlatformWorkerProcessOptions`, `startPlatformWorkerProcess`, `installShutdownHandlers`.

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/platform-observability`, `./diagnostics`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=018100c2d9242570603b1f4d3f2f8a50eed13a306e597fcc97b298cb23e6cc42 after=8936ae0081522576aadc565f66a9bce5060cad23415fb2f6ee635609e5fe387c -->

<!-- course-file: platform/workers/src/queue.ts -->

### queue.ts

[Open current source](../../../../../platform/workers/src/queue.ts) · **Snapshot:** modified existing file; 22 added / 10 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports worker processing and queue delivery at this layer.

**Before:** Worker processing and queues already existed. Invalid payload, lost claim, handler failure and acknowledgement uncertainty could lose their distinct locations and source facts. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `createInMemoryPlatformWorkerQueue` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** A failed acknowledgement may follow successful business work. Treating it as handler-not-run could duplicate effects on recovery.

Changed declaration anchors: `createInMemoryPlatformWorkerQueue`.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=80ec9e3e885d9666f5a0bc15486ea332661c702066ad05c34061fb8febadcbd9 after=05f8e2903f405ffa51d53afd03ea64748af3f3fca972dae93697874c5d3808cf -->

<!-- course-file: platform/workers/src/types.ts -->

### types.ts

[Open current source](../../../../../platform/workers/src/types.ts) · **Snapshot:** modified existing file; 2 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports worker processing and queue delivery at this layer.

**Before:** Worker processing and queues already existed. Invalid payload, lost claim, handler failure and acknowledgement uncertainty could lose their distinct locations and source facts. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformWorkerShellOptions` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** A failed acknowledgement may follow successful business work. Treating it as handler-not-run could duplicate effects on recovery.

Changed declaration anchors: `PlatformWorkerShellOptions`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=92393387b714a0c23e9d25a22d02358b1fdb1d8825b4a7ab070e092b0d996f75 after=d4ab39fe5779cc0c3f740c678ca3acafacaa6573386342034f49da6d331930e2 -->

<!-- course-file: platform/workers/src/worker.ts -->

### worker.ts

[Open current source](../../../../../platform/workers/src/worker.ts) · **Snapshot:** modified existing file; 315 added / 59 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports worker processing and queue delivery at this layer.

**Before:** Worker processing and queues already existed. Invalid payload, lost claim, handler failure and acknowledgement uncertainty could lose their distinct locations and source facts. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `workerBuiltinDiagnosticCatalogs`, `createPlatformWorkerShell`, `validateJobPayload`, `WorkerBoundaryObserver`, `claimDurableOutboxProcessing`, `durableOutboxEntryId`, `durableOutboxEnvelopeFailure` (8 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** A failed acknowledgement may follow successful business work. Treating it as handler-not-run could duplicate effects on recovery.

Changed declaration anchors: `workerBuiltinDiagnosticCatalogs`, `createPlatformWorkerShell`, `validateJobPayload`, `WorkerBoundaryObserver`, `claimDurableOutboxProcessing`, `durableOutboxEntryId`, `durableOutboxEnvelopeFailure`, `settleFailedDurableOutboxProcessing`, `durableProcessingFailure`, `workerProfileForJob`, `recordWorkerObservationUnchecked`, `endWorkerTraceUnchecked` (3 more in source).

New declarations within this existing file: `workerBuiltinDiagnosticCatalogs`, `WorkerBoundaryObserver`, `recordWorkerObservationUnchecked`, `endWorkerTraceUnchecked`.

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `@kanbien/core/validation`, `./diagnostics`, `./configuration-diagnostics`.

Declarations removed or relocated: `recordWorkerObservation`, `endWorkerTrace`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b58c672467032334d356e40ceb8f17207606064c513c35d32db0f4439fbd0556 after=22c76da0ff5136dda5db3e08a218d5a2ff9ff8bfc5a5a260bc2966d12db18c73 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What must an agent investigate before retrying a delivery whose settlement failed?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** This is not a new exactly-once policy, retry policy or queue backend. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/workers/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L070 platform/workers](070-platform-workers.md) · [L071 platform/workers/contracts](071-platform-workers-contracts.md) · [L073 platform/workers/tests](073-platform-workers-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 9 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
