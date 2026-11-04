<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l017
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/events.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L017 — packages/core/src/events

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/events -->

## What you will understand

Event helpers create event representations and invoke existing event-related callbacks. Their responsibility is distinct from transport delivery.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

An event passes its envelope checks but an injected callback throws. Report the observed callback boundary, not that no consumer received the event. Keep event payload and identifiers out of detail.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Existing event validation and callbacks could fail with the same broad exception shape despite different progress through the operation.

**After:** Versioned observations identify existing validation, projection and callback boundaries, retaining source records independently and preserving original results.

**Why this was needed:** An agent should distinguish rejected event input from a publication invocation whose outcome is unknown before considering recovery.

This directory contains `definition`, `barrel-or-implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/events/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/events/diagnostics.ts) · **Snapshot:** added (absent from baseline); 48 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.events.validation-rejected`, `core.events.boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `coreEventValidationDiagnostic`, `coreEventBoundaryDiagnostic`, `coreEventDiagnosticDefinitions`, `CoreEventValidationDetail`, `CoreEventBoundaryDetail`, `CoreEventDiagnosticContext`, `CoreEventDiagnosticOptions`, `CoreEventErrorEvidence`, `coreEventValidationDiagnosticRecord`, `coreEventBoundaryDiagnosticRecord`, `required`.

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=b895e61b119ed89d63a100f6fe0f2264adf142356938aec28cadcef0adfbc868 -->

<!-- course-file: packages/core/src/events/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/events/index.ts) · **Snapshot:** modified existing file; 91 added / 29 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports events, handlers and publication at this layer.

**Before:** Existing event validation and callbacks could fail with the same broad exception shape despite different progress through the operation. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `eventType`, `eventVersion`, `eventPublishError`, `eventEnvelope`, `projectEventEnvelope`, `inMemoryEventBus`, `eventRelatedEvidence` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Existing Event type/version predicates retain exact regex/integer/positive alternatives. Closed records distinguish declaration, batch/argument projection, actual event/handler traversal, getter selection, invocation, completion, published append and snapshots.

**Why:** An agent should distinguish rejected event input from a publication invocation whose outcome is unknown before considering recovery.

Changed declaration anchors: `eventType`, `eventVersion`, `eventPublishError`, `eventEnvelope`, `projectEventEnvelope`, `inMemoryEventBus`, `eventRelatedEvidence`.

New declarations within this existing file: `projectEventEnvelope`, `eventRelatedEvidence`.

Added import edges: `./observations`, `./diagnostics`.

Declarations removed or relocated: `copyEventEnvelope`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=0484ad2c9c88d2157c4ea766f7e56374122db5907c365277bf106337cbbea606 after=0262d3c361c53f8eff2ee8124d11eb3ec50b80737c1162ff6373cf201c3fad89 -->

<!-- course-file: packages/core/src/events/observations.ts -->

### observations.ts

[Open current source](../../../../../packages/core/src/events/observations.ts) · **Snapshot:** added (absent from baseline); 70 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Existing Event type/version predicates retain exact regex/integer/positive alternatives. Closed records distinguish declaration, batch/argument projection, actual event/handler traversal, getter selection, invocation, completion, published append and snapshots. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `nativeThen`, `selectCoreEventDiagnosticDefinitions`, `observe`, `EventObservation`.

Added import edges: `../diagnostic-catalog`, `../diagnostics/index`, `../shared/diagnostics`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=12f87119e13c89ca8e9e12388e52483b4bed8a933371a61f8fd07cd0e938b63d -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Does a normally returning callback prove delivery to every subscriber?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Diagnostic adoption adds neither a new event bus nor an exactly-once guarantee. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/events) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
