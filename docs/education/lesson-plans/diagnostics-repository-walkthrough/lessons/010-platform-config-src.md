<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l010
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/config/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L010 — platform/config/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/config/src -->

## What you will understand

Configuration code turns supplied settings into values the workload can use. A setting is a logical requirement; its environment-variable name belongs to the caller that binds it.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Start with the original combined host/database/schema/reference/port guard. If port is absent and host is present, the useful observation is the port requirement being missing—not a guessed connection failure. If reading the source throws before a value is obtained, wrong-type would be an unsupported claim.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Existing readers rejected missing or malformed values, but several callers collapsed alternatives into undefined or one broad configuration error.

**After:** Reusable readers retain safe setting references, exact observed reasons, source-read failures, indexed issues and explicitly declared relationships. Target bindings supply exact source names privately, without placing submitted values in diagnostic detail.

**Why this was needed:** An agent needs to know which requirement failed and whether to fix a declaration, provide a setting, or investigate an unreadable source. One broad rejection cannot support that decision.

This directory contains `definition`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/config/src/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../platform/config/src/diagnostics.ts) · **Snapshot:** added (absent from baseline); 140 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `platform-config.schema-rejected`, `platform-config.schema-boundary-threw`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `defineConfigurationDiagnostic`, `configurationDiagnostic`, `defineConfigurationRelationshipDiagnostics`, `configurationRelationshipDiagnostic`, `relationshipEvidenceObject`, `relationshipEvidenceArray`, `platformConfigDiagnostic`, `platformConfigWideDiagnostic`, `platformConfigThrownDiagnostic`, `defineConfigurationSourceReadDiagnostic`, `configurationSourceReadDiagnosticRecord`, `platformConfigDiagnosticCatalog`.

Added import edges: `@kanbien/core/config`, `@kanbien/core/diagnostics`.

Owning registered proof: `platform-config-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`, `platform-workers-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=9c8be0da060b2a248ea40dfedd80ec4296f3a35b32b7226230b3b4aec5740f28 -->

<!-- course-file: platform/config/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/config/src/index.ts) · **Snapshot:** modified existing file; 61 added / 9 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports configuration: tell absence from invalidity at this layer.

**Before:** Existing readers rejected missing or malformed values, but several callers collapsed alternatives into undefined or one broad configuration error. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformConfigError`, `PlatformConfigValidationInput`, `intrinsicPromiseThen`, `validatePlatformConfigSchemas`, `rejectionRecord`, `platformConfigError`, `selectedEvidence` (1 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Schema rejection reports its position independently from explicitly selected Core/app primary and eight companions. Parse/projection throws report the actual boundary then rethrow the same value; optional callback throws/rejections cannot alter outcomes.

**Why:** An agent needs to know which requirement failed and whether to fix a declaration, provide a setting, or investigate an unreadable source. One broad rejection cannot support that decision.

Changed declaration anchors: `PlatformConfigError`, `PlatformConfigValidationInput`, `intrinsicPromiseThen`, `validatePlatformConfigSchemas`, `rejectionRecord`, `platformConfigError`, `selectedEvidence`, `observe`.

New declarations within this existing file: `intrinsicPromiseThen`, `rejectionRecord`, `selectedEvidence`, `observe`.

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `./diagnostics`.

Owning registered proof: `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=9cc880eddf5e2807448b754651fe9cb731268b0553b6ce36e2e8245ade446e54 after=82ae867017a42852f3740d381b13ced39fde49303c3a6713d16795083476fd1d -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which fact distinguishes a missing setting from a getter that threw before the setting could be read?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Do not expose hostnames, usernames, passwords, source contents or rejected values. The issue collector has a bound; overflow must not be called complete. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/config/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L008 platform/config](008-platform-config.md) · [L009 platform/config/contracts](009-platform-config-contracts.md) · [L011 platform/config/tests](011-platform-config-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
