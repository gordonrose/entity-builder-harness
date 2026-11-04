<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l045
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/health/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L045 — platform/health/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/health/src -->

## What you will understand

Health checks tell the workload and its callers whether dependencies and lifecycle state are ready. Public detail is a separate disclosure contract.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A check returns unhealthy with a message containing a private connection string. The public response retains status and a fixed summary, not that string; internal selected facts identify the check boundary without copying it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Health checks already ran, but public messages and metadata could contain arbitrary strings; internal failures could lose exact safe source evidence.

**After:** Internal records separate returned not-ready results, throws, rejections, projection problems and lifecycle state. Public messages use fixed summaries and explicitly allowed metadata values.

**Why this was needed:** Redacting keys is insufficient if an otherwise harmless message string contains a secret. A safe internal diagnostic should be detailed while the public endpoint stays deliberately limited.

This directory contains `definition`, `barrel-or-implementation`, `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/health/src/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../platform/health/src/diagnostics.ts) · **Snapshot:** added (absent from baseline); 30 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `health.check-not-ready`, `health.check-threw`, `health.check-rejected`, `health.check-projection-failed`, `health.lifecycle-not-ready`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `classification`, `index`, `healthNotReadyDiagnostic`, `healthInvocationDiagnostic`, `healthRejectionDiagnostic`, `healthProjectionDiagnostic`, `healthLifecycleDiagnostic`, `platformHealthDiagnosticCatalog`, `healthDiagnosticRecord`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=9d52c0d1e6440a3d53317d97ec5eb9fd6176862289ca09d3f290d448196a2702 -->

<!-- course-file: platform/health/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/health/src/index.ts) · **Snapshot:** modified existing file; 52 added / 25 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports health: public status and private evidence at this layer.

**Before:** Health checks already ran, but public messages and metadata could contain arbitrary strings; internal failures could lose exact safe source evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `intrinsicPromiseThen`, `PlatformSafeHealthCheckResult`, `PlatformReadinessInput`, `platformReadiness`, `runSafeHealthCheck`, `safeHealthCheckResult` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Health-owned closed records distinguish returned degraded/unhealthy states, invocation throw, completion rejection, public projection failure and lifecycleReady=false without guessing a cause. Zero-based check indices avoid arbitrary names; actual upstream primary/related evidence is forwarded only for nonhealthy/projection-failure paths.

**Why:** Redacting keys is insufficient if an otherwise harmless message string contains a secret. A safe internal diagnostic should be detailed while the public endpoint stays deliberately limited.

Changed declaration anchors: `intrinsicPromiseThen`, `PlatformSafeHealthCheckResult`, `PlatformReadinessInput`, `platformReadiness`, `runSafeHealthCheck`, `safeHealthCheckResult`.

New declarations within this existing file: `intrinsicPromiseThen`.

Added import edges: `./diagnostics`, `./public-details`.

Declarations removed or relocated: `safeMetadata`, `isJsonObject`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=461f6cd998495654aaaadf268f05c9758d68c487eaf82236aa592d6e620bb097 after=956ec4768a29b30900372da74b938a5083e474566edf57aa8aa55a2799774263 -->

<!-- course-file: platform/health/src/public-details.ts -->

### public-details.ts

[Open current source](../../../../../platform/health/src/public-details.ts) · **Snapshot:** added (absent from baseline); 39 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the public health disclosure allowlist.

**Before:** Public health detail could preserve arbitrary message and metadata strings.

**After:** Returns fixed summaries and only explicitly permitted dependency/config values, inspecting optional metadata through own data descriptors.

**Why:** Sensitive content can be inside a harmless-looking message string; key-name redaction cannot remove that risk.

Changed declaration anchors: `summaries`, `metadataValues`, `PlatformPublicHealthMessage`, `PlatformPublicHealthMetadata`, `publicHealthMessage`, `publicHealthMetadata`, `approvedMetadataValue`.

Added import edges: `@kanbien/core/monitoring`.

Connected review context (`platform-health-diagnostics`; this review may span several files): Health-owned closed records distinguish returned degraded/unhealthy states, invocation throw, completion rejection, public projection failure and lifecycleReady=false without guessing a cause. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=67a39a20b7c1c89e264e64c52f918c9855fc557b09c9b51eaf7323e0c139ba96 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why is replacing arbitrary public prose an intentional compatibility decision, rather than a transparent refactor?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Healthy local checks do not establish live deployment acceptance or prove remote log delivery. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/health/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L043 platform/health](043-platform-health.md) · [L044 platform/health/contracts](044-platform-health-contracts.md) · [L046 platform/health/tests](046-platform-health-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
