<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l069
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/queues.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L069 — packages/core/src/queues

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/queues -->

## What you will understand

Workers receive jobs, validate payloads, coordinate durable claims, invoke handlers and settle delivery. Queue adapters implement transport operations.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A handler returns successfully, then acknowledgement throws. Describe the observed acknowledgement invocation with uncertain effect. Do not report handler rejection or replay it merely to obtain a diagnostic.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Worker processing and queues already existed. Invalid payload, lost claim, handler failure and acknowledgement uncertainty could lose their distinct locations and source facts.

**After:** Closed worker/queue records describe actual validation, coordination, handler and settlement boundaries. Optional reporting preserves attempt multiplicity, profile opt-outs and original business results.

**Why this was needed:** A failed acknowledgement may follow successful business work. Treating it as handler-not-run could duplicate effects on recovery.

This directory contains `documentation`, `definition`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/queues/README.md -->

### README.md

[Open current source](../../../../../packages/core/src/queues/README.md) · **Snapshot:** modified existing file; 16 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for worker processing and queue delivery; read the sections `Core Queue Source Map`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Core Queue Source Map`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=ea7ca48ff3feba1c6690e072c2766cd7dc985c8da3e40d60486a969f7a648187 after=e9bc7b4cb5933ec3e8e077dbb7bac4f254aca292dbad451daa8abeff2a484f4c -->

<!-- course-file: packages/core/src/queues/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/queues/diagnostics.ts) · **Snapshot:** added (absent from baseline); 59 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.queue.validation-rejected`, `core.queue.boundary-failed`, `core.queue.receive-reduced`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `coreQueueValidationDiagnostic`, `coreQueueBoundaryDiagnostic`, `coreQueueReceiveReductionDiagnostic`, `coreQueueDiagnosticDefinitions`, `CoreQueueValidationDetail`, `CoreQueueBoundaryDetail`, `CoreQueueReceiveReductionDetail`, `CoreQueueDiagnosticContext`, `CoreQueueDiagnosticOptions`, `requiredRecord`, `coreQueueValidationDiagnosticRecord`, `coreQueueBoundaryDiagnosticRecord` (1 more in source).

Added import edges: `../diagnostics/index`.

Owning registered proof: `shell-package-source`, `platform-shell-payload`, `core-runtime`, `diagnostic-catalog-readers`, `sqs-queue-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=4d844f751df34afb80284a69a42dc6900fbd918cb8ae21a65e0bbf5702319368 -->

<!-- course-file: packages/core/src/queues/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/queues/index.ts) · **Snapshot:** modified existing file; 56 added / 9 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports worker processing and queue delivery at this layer.

**Before:** Worker processing and queues already existed. Invalid payload, lost claim, handler failure and acknowledgement uncertainty could lose their distinct locations and source facts. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `queueMessageType`, `queueMessageVersion`, `queueDelaySeconds`, `queueAttempt`, `queueIdempotencyKey`, `queueMessageGroupKey`, `queueDeadLetterReason` (9 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Preserve supplied diagnosticRecord through existing error factories and add the optional validation projection; CoreError declares bounded related observations, with affected persistence factories validating them against explicitly supplied definitions. Shared date/JSON guards now retain value-free positional evidence; overridden map semantics and unavailable callback locations are tested without replacing existing errors.

**Why:** A failed acknowledgement may follow successful business work. Treating it as handler-not-run could duplicate effects on recovery.

Changed declaration anchors: `queueMessageType`, `queueMessageVersion`, `queueDelaySeconds`, `queueAttempt`, `queueIdempotencyKey`, `queueMessageGroupKey`, `queueDeadLetterReason`, `queueError`, `queueRetryMetadata`, `queueDelivery`, `requireNonEmpty`, `queueValidation` (4 more in source).

New declarations within this existing file: `queueValidation`, `selectCoreQueueDiagnosticEvidence`, `queuePromiseThen`, `ignoreQueueDiagnosticRejection`, `observeCoreQueueDiagnostic`.

Added import edges: `../diagnostic-catalog`, `./diagnostics`.

Owning registered proof: `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=4e1d1222c4a5ef6d59a0b9e0855c931b98d6beb506476d90085e67ffa9fa80e5 after=9516f274cee4d4f99e4ca9ffa0a44fb0240dc32767d31650882b5793919bead3 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What must an agent investigate before retrying a delivery whose settlement failed?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** This is not a new exactly-once policy, retry policy or queue backend. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/queues) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
