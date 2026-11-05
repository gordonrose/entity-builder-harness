<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l016
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/audit.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L016 — packages/core/src/audit

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/audit -->

## What you will understand

Audit code builds records of actions and offers recorder ports. A port is an interface into which another implementation can be supplied.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A metadata copy throws before append. Compare that with append throwing after it was invoked. The first says append was not reached; the second leaves the append effect uncertain. Neither should print metadata values.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Audit constructors, in-memory recording and no-op recording already existed. Failures in actor/target/metadata projection or append were difficult to distinguish safely.

**After:** Closed validation and boundary records identify projection phases, callback ordinals and append uncertainty. Observation is optional and isolated from the recorder result.

**Why this was needed:** An append invocation that did not return is not evidence that an audit record was durably stored, and repeating it for better logging could duplicate the event.

This directory contains `definition`, `barrel-or-implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/audit/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/audit/diagnostics.ts) · **Snapshot:** added (absent from baseline); 46 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.audit.validation-rejected`, `core.audit.boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `coreAuditValidationDiagnostic`, `coreAuditBoundaryDiagnostic`, `coreAuditDiagnosticDefinitions`, `CoreAuditValidationDetail`, `CoreAuditBoundaryDetail`, `CoreAuditDiagnosticContext`, `CoreAuditDiagnosticOptions`, `CoreAuditErrorEvidence`, `coreAuditValidationDiagnosticRecord`, `coreAuditBoundaryDiagnosticRecord`, `required`.

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=0a0269cf6bf5fe8753ff42512151964ef74abfb6e1c83cb56a0d6aff917ad40d -->

<!-- course-file: packages/core/src/audit/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/audit/index.ts) · **Snapshot:** modified existing file; 95 added / 51 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports audit records and projection at this layer.

**Before:** Audit constructors, in-memory recording and no-op recording already existed. Failures in actor/target/metadata projection or append were difficult to distinguish safely. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `auditEventType`, `auditEventVersion`, `auditActor`, `auditTarget`, `auditEvent`, `projectAuditEvent`, `auditRecordError` (5 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Existing Audit type/version/target predicates retain exact first-failure alternatives and original repeated reads. Closed raw records identify actor/target/metadata projection, eager entries-before-nested-copy, record append uncertainty and snapshot callback ordinals.

**Why:** An append invocation that did not return is not evidence that an audit record was durably stored, and repeating it for better logging could duplicate the event.

Changed declaration anchors: `auditEventType`, `auditEventVersion`, `auditActor`, `auditTarget`, `auditEvent`, `projectAuditEvent`, `auditRecordError`, `inMemoryAuditRecorder`, `copyAuditActor`, `copyAuditTarget`, `copyAuditMetadata`, `auditRelatedEvidence`.

New declarations within this existing file: `projectAuditEvent`, `auditRelatedEvidence`.

Added import edges: `./observations`, `./diagnostics`.

Declarations removed or relocated: `copyAuditEvent`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=40125a44cdc80aa450097459f5187451f87326b2290ad3ad1ca1021804ae9cc2 after=94d7ab158c3f49f74bffda6ff5874eaf21fbe65f699c5f33d5f4249ae79c1608 -->

<!-- course-file: packages/core/src/audit/observations.ts -->

### observations.ts

[Open current source](../../../../../packages/core/src/audit/observations.ts) · **Snapshot:** added (absent from baseline); 67 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Existing Audit type/version/target predicates retain exact first-failure alternatives and original repeated reads. Closed raw records identify actor/target/metadata projection, eager entries-before-nested-copy, record append uncertainty and snapshot callback ordinals. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `nativeThen`, `observe`, `AuditObservation`.

Added import edges: `../diagnostic-catalog`, `../diagnostics/index`, `../shared/diagnostics`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=ef646b217050f4f7987369196effb82c4c91daf44354426975c4343cf348a858 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must a diagnostic reporter failure never cause the audit append to run again?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** In-memory append is not durable commitment; the course will not pretend an audit storage service was added. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/audit) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
