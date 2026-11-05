<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l086
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder apps/platform-smoke/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L086 — apps/platform-smoke/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: apps/platform-smoke/src -->

## What you will understand

Platform-smoke is a real example app that mounts routes/jobs and exercises persistence-backed work-item acceptance.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A work-item acceptance input fails an existing feature predicate. Preserve the business result; attach the app-owned safe reason. If the writer itself throws, retain selected source evidence separately rather than replacing it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The feature and its endpoints already existed. App-specific configuration and accepted-payload failures could be hidden behind generic platform errors.

**After:** The app declares its own diagnostic catalog and payload/configuration/acceptance observations; Platform and targets select and deliver them. Existing supported acceptance behavior remains.

**Why this was needed:** Only the feature can say what an invalid accepted work item means. Generic HTTP or database code should not own the app vocabulary.

This directory contains `implementation`, `definition` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: apps/platform-smoke/src/app.mount.ts -->

### app.mount.ts

[Open current source](../../../../../apps/platform-smoke/src/app.mount.ts) · **Snapshot:** modified existing file; 70 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports the sample app owns its feature meaning at this layer.

**Before:** The feature and its endpoints already existed. App-specific configuration and accepted-payload failures could be hidden behind generic platform errors. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformSmokeAppOptions`, `platformSmokeWorkItemDeliveryObservabilityProfile`, `platformSmokeWorkItemAcceptanceObservabilityProfile`, `platformSmokeConfigSchema`, `platformSmokeRebuildValidator`, `platformSmokeWorkItemAcceptedValidator`, `platformSmokeWorkItemAcceptanceValidator` (4 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): App owns app-name configuration and accepted-work-item payload predicate meanings, preserving Core reader companions. Actual server config and worker dead-letter delivery are tested default/injected/unavailable.

**Why:** Only the feature can say what an invalid accepted work item means. Generic HTTP or database code should not own the app vocabulary.

Changed declaration anchors: `PlatformSmokeAppOptions`, `platformSmokeWorkItemDeliveryObservabilityProfile`, `platformSmokeWorkItemAcceptanceObservabilityProfile`, `platformSmokeConfigSchema`, `platformSmokeRebuildValidator`, `platformSmokeWorkItemAcceptedValidator`, `platformSmokeWorkItemAcceptanceValidator`, `createPlatformSmokeApp`, `registerPlatformSmokeWorkItemAcceptance`, `intrinsicPromiseThen`, `workItemInvocationDiagnostics`.

New declarations within this existing file: `intrinsicPromiseThen`, `workItemInvocationDiagnostics`.

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `@kanbien/platform-persistence`, `@kanbien/core/persistence`, `./diagnostics`.

Owning registered proof: `platform-smoke-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f220b1bf2a94fa2790bc96231264d267b8b4a5e19039f289b7c155e9ca551a6e after=973f430f09e101f937c182d3a6d811ff3ad73c5e76e8469d41db323686009a55 -->

<!-- course-file: apps/platform-smoke/src/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../apps/platform-smoke/src/diagnostics.ts) · **Snapshot:** added (absent from baseline); 86 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `platform-smoke.work-item-not-accepted`, `platform-smoke.attribute-invalid`, `platform-smoke.configuration-invalid`, `platform-smoke.accepted-payload-invalid`, `platform-smoke.accepted-payload-not-observed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `platformSmokeAcceptanceDiagnostic`, `platformSmokeAttributeDiagnostic`, `platformSmokeConfigDiagnostic`, `platformSmokeAcceptedPayloadDiagnostic`, `platformSmokeAcceptedProjectionDiagnostic`, `platformSmokeDiagnosticCatalog`, `platformSmokeConfigurationFailure`, `platformSmokeAcceptedPayloadFailure`, `platformSmokeAttributeFailure`, `platformSmokeAcceptanceFailure`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-smoke-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=136f899a4c8e35702a91537a64ef68c9ba8b00c451a0c5c61d14c44856b1e12e -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which part of this explanation belongs to the app, and which belongs to Persistence?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** An acceptance diagnostic does not independently prove that a database commit happened. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../apps/platform-smoke/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L084 apps/platform-smoke](084-apps-platform-smoke.md) · [L085 apps/platform-smoke/contracts](085-apps-platform-smoke-contracts.md) · [L087 apps/platform-smoke/src/persistence](087-platform-smoke-src-persistence.md) · [L088 apps/platform-smoke/tests](088-apps-platform-smoke-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
