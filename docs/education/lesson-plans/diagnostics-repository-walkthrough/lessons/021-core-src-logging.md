<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l021
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/logging.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L021 — packages/core/src/logging

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/logging -->

## What you will understand

Core exposes health, metrics, tracing and logging abstractions that implementations can fulfill. Metrics count or measure; traces describe work across spans; logs retain individual events.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A metric name fails its actual guard before record is invoked. Compare that with the recording port throwing. Only the first proves recording was not attempted; a normal return still does not prove backend delivery.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** These abstractions and guards already existed. Predicate failures and helper boundaries were not uniformly available as machine-readable observations.

**After:** The existing primitives gain finite validation/boundary records and optional observers. Higher layers can tell rejected metric input from failed recording without parsing messages.

**Why this was needed:** Diagnostic work explains failure of monitoring itself. It must not recursively depend on the same failed logger or make successful business work fail.

This directory contains `definition`, `barrel-or-implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/logging/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/logging/diagnostics.ts) · **Snapshot:** added (absent from baseline); 28 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.logging.boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `coreLoggingBoundaryDiagnostic`, `coreLoggingDiagnosticDefinitions`, `CoreLoggingBoundaryDetail`, `CoreLoggingDiagnosticContext`, `CoreLoggingDiagnosticOptions`, `coreLoggingBoundaryDiagnosticRecord`.

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=4eb5712864c08e6336e4329e19f33556bb5ddfb4fa88b835010fa0ba7bcbe912 -->

<!-- course-file: packages/core/src/logging/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/logging/index.ts) · **Snapshot:** modified existing file; 68 added / 29 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports monitoring primitives and logging at this layer.

**Before:** These abstractions and guards already existed. Predicate failures and helper boundaries were not uniformly available as machine-readable observations. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `logRecord`, `redactLogFields`, `createLogRedactor`, `redactFields`, `redactRecord`, `keyRedactor`, `redactingLogger` (1 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core-owned closed logging/monitoring observations identify only actual guard and injected-call locations. Optional per-invocation delivery retains own location plus independently selected primary/eight; frozen/primitive throws and observer failures preserve original identity.

**Why:** Diagnostic work explains failure of monitoring itself. It must not recursively depend on the same failed logger or make successful business work fail.

Changed declaration anchors: `logRecord`, `redactLogFields`, `createLogRedactor`, `redactFields`, `redactRecord`, `keyRedactor`, `redactingLogger`, `redactNestedValue`.

New declarations within this existing file: `redactFields`.

Added import edges: `./diagnostics`, `./observations`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=353fcb48f035a7b2aba869fea618f607ea04fa46eef7840132814e5665263be0 after=96b7706a82904fb3e4f28af6a89198a8e96dd3747f525028af50ab4298edf033 -->

<!-- course-file: packages/core/src/logging/observations.ts -->

### observations.ts

[Open current source](../../../../../packages/core/src/logging/observations.ts) · **Snapshot:** added (absent from baseline); 45 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Core-owned closed logging/monitoring observations identify only actual guard and injected-call locations. Optional per-invocation delivery retains own location plus independently selected primary/eight; frozen/primitive throws and observer failures preserve original identity. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `selectCoreLoggingDiagnosticEvidence`, `nativeThen`, `isolate`, `observeCoreLoggingDiagnostic`, `LoggingObservation`.

Added import edges: `../diagnostic-catalog`, `../diagnostics/index`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=62e0d6cf3ebea38f986197e6266c01e6295e59dcc670690fab2ed67134d88886 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What is the difference between a metric recording call returning and a backend retaining that metric?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Monitoring already existed before this project; this is not installation of a new observability stack. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/logging) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
