<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l013
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/authn.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L013 — packages/core/src/authn

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/authn -->

## What you will understand

Authentication asks who a caller is; authorization asks what they may do; tenancy identifies the operating context. These modules construct those representations.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Let claims enumeration throw while building a principal. The observation can say projection failed; it cannot claim the token signature failed. The original thrown value must still leave the constructor unchanged.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Constructors and permission checks already existed. Projection, claim copying or scope iteration could fail without identifying the observed constructor boundary.

**After:** Optional observations identify actual principal/tenant/permission boundaries and selected source evidence while retaining thrown identity, getter order and existing nullish fallbacks.

**Why this was needed:** A failed principal projection is not automatically an invalid token, denied permission or cross-tenant attack. The diagnostic must name the boundary actually reached.

This directory contains `definition`, `barrel-or-implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/authn/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/authn/diagnostics.ts) · **Snapshot:** added (absent from baseline); 26 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.authn.boundary-failed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `coreAuthnBoundaryDiagnostic`, `coreAuthnDiagnosticDefinitions`, `CoreAuthnBoundaryDetail`, `CoreAuthnDiagnosticContext`, `CoreAuthnDiagnosticOptions`, `coreAuthnBoundaryDiagnosticRecord`.

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `platform-security-runtime`, `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=b9303495cc2d33450f2f4fa2dacc5ccdbb3f753c610d4345a90efb01fa46636e -->

<!-- course-file: packages/core/src/authn/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/authn/index.ts) · **Snapshot:** modified existing file; 20 added / 13 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports identity and tenant construction at this layer.

**Before:** Constructors and permission checks already existed. Projection, claim copying or scope iteration could fail without identifying the observed constructor boundary. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `principal`, `copyPrincipalClaims` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core owns additive principal and tenant-constructor boundary definitions. Optional observers independently deliver the exact observed projection/copy location and selected source primary plus up to eight related records, preserving raw primitive/frozen throw identity, eager claims enumeration, repeated getters, scope iteration and nullish tenant fallback.

**Why:** A failed principal projection is not automatically an invalid token, denied permission or cross-tenant attack. The diagnostic must name the boundary actually reached.

Changed declaration anchors: `principal`, `copyPrincipalClaims`.

Added import edges: `./observations`, `./diagnostics`.

Owning registered proof: `core-runtime`, `platform-security-runtime`, `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b2facf296fa6224267f8ff6d84b090fc78c86d683a3e7024d0ea6055a15939c4 after=a105338985fa5dadb0042b146fd723d7920f5b16d77f8a070d63f680eeef2923 -->

<!-- course-file: packages/core/src/authn/observations.ts -->

### observations.ts

[Open current source](../../../../../packages/core/src/authn/observations.ts) · **Snapshot:** added (absent from baseline); 43 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Core owns additive principal and tenant-constructor boundary definitions. Optional observers independently deliver the exact observed projection/copy location and selected source primary plus up to eight related records, preserving raw primitive/frozen throw identity, eager claims enumeration, repeated getters, scope iteration and nullish tenant fallback. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `nativeThen`, `isolate`, `observeCoreAuthnDiagnostic`, `PrincipalObservation`.

Added import edges: `../diagnostic-catalog`, `../diagnostics/index`, `./diagnostics`.

Owning registered proof: `core-runtime`, `platform-security-runtime`, `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=b51e96a464066476d3ff17bdf1eb61f30fe221e19b38280b84147faf59e218c9 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What extra evidence would you need before turning a tenant-construction failure into an isolation violation?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** This work did not implement a new session, cookie, CSRF or tenant-isolation policy. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/authn) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L014 packages/core/src/authz](014-core-src-authz.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
