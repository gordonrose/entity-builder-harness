<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l014
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder packages/core/src/authz.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L014 — packages/core/src/authz

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: packages/core/src/authz -->

## What you will understand

Authentication asks who a caller is; authorization asks what they may do; tenancy identifies the operating context. These modules construct those representations.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Let claims enumeration throw while building a principal. The observation can say projection failed; it cannot claim the token signature failed. The original thrown value must still leave the constructor unchanged.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Constructors and permission checks already existed. Projection, claim copying or scope iteration could fail without identifying the observed constructor boundary.

**After:** Optional observations identify actual principal/tenant/permission boundaries and selected source evidence while retaining thrown identity, getter order and existing nullish fallbacks.

**Why this was needed:** A failed principal projection is not automatically an invalid token, denied permission or cross-tenant attack. The diagnostic must name the boundary actually reached.

This directory contains `definition`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: packages/core/src/authz/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../packages/core/src/authz/diagnostics.ts) · **Snapshot:** added (absent from baseline); 16 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `core.authz.permission-invalid`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `corePermissionDiagnostic`, `coreAuthzDiagnosticDefinitions`, `corePermissionRecord`.

Added import edges: `../diagnostics/index`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=6c09c6bd19986f37a936bae72c3fce3fec34d7deccad6b4430daecc17d0aed12 -->

<!-- course-file: packages/core/src/authz/index.ts -->

### index.ts

[Open current source](../../../../../packages/core/src/authz/index.ts) · **Snapshot:** modified existing file; 10 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports identity and tenant construction at this layer.

**Before:** Constructors and permission checks already existed. Projection, claim copying or scope iteration could fail without identifying the observed constructor boundary. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `assertPermissionPart` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Natural Core config/shared/security/authz modules own closed actual guard meanings and a package-root explicit catalog. Exact primitive grammar, first failure, source/getter reads, same thrown identity, custom map/some semantics and unavailable location/classification are independently tested.

**Why:** A failed principal projection is not automatically an invalid token, denied permission or cross-tenant attack. The diagnostic must name the boundary actually reached.

Changed declaration anchors: `assertPermissionPart`.

Added import edges: `../shared/diagnostics`, `./diagnostics`.

Owning registered proof: `core-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=d2510247978d2e79b7469f2ffa946989e2e074231ebf7716887339c6e00f3122 after=3a7c6eff4461d4019c57cf2868ff4ad994bdaa90cf985807f2683130db925a1b -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What extra evidence would you need before turning a tenant-construction failure into an isolation violation?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** This work did not implement a new session, cookie, CSRF or tenant-isolation policy. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../packages/core/src/authz) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L003 packages/core/src](003-packages-core-src.md) · [L004 packages/core/src/diagnostics](004-core-src-diagnostics.md) · [L005 packages/core/src/validation](005-core-src-validation.md) · [L007 packages/core/src/config](007-core-src-config.md) · [L012 packages/core/src/shared](012-core-src-shared.md) · [L013 packages/core/src/authn](013-core-src-authn.md) · [L015 packages/core/src/tenancy](015-core-src-tenancy.md) · [L016 packages/core/src/audit](016-core-src-audit.md) · [L017 packages/core/src/events](017-core-src-events.md) · [L018 packages/core/src/files](018-core-src-files.md) · [L019 packages/core/src/i18n](019-core-src-i18n.md) · [L020 packages/core/src/localization](020-core-src-localization.md) · [L021 packages/core/src/logging](021-core-src-logging.md) · [L022 packages/core/src/monitoring](022-core-src-monitoring.md) · [L047 packages/core/src/security](047-core-src-security.md) · [L057 packages/core/src/persistence](057-core-src-persistence.md) · [L069 packages/core/src/queues](069-core-src-queues.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
