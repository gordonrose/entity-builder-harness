<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l046
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/health/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L046 — platform/health/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/health/tests -->

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

This directory contains `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/health/tests/diagnostics-runtime.test.ts -->

### diagnostics-runtime.test.ts

[Open current source](../../../../../platform/health/tests/diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 127 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for health: public status and private evidence.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Health-owned closed records distinguish returned degraded/unhealthy states, invocation throw, completion rejection, public projection failure and lifecycleReady=false without guessing a cause. Zero-based check indices avoid arbitrary names; actual upstream primary/related evidence is forwarded only for nonhealthy/projection-failure paths.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/core/monitoring`, `@kanbien/core/shared`, `@kanbien/platform-contracts`, `@kanbien/platform-observability`, `../src/index`.

Owning registered proof: `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=9e4477bd88d578402639ee4f235335ab84ed297ce49f852cec3a1fbaaf2db210 -->

<!-- course-file: platform/health/tests/platform-health-runtime.test.ts -->

### platform-health-runtime.test.ts

[Open current source](../../../../../platform/health/tests/platform-health-runtime.test.ts) · **Snapshot:** modified existing file; 2 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for health: public status and private evidence.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Health-owned closed records distinguish returned degraded/unhealthy states, invocation throw, completion rejection, public projection failure and lifecycleReady=false without guessing a cause. Zero-based check indices avoid arbitrary names; actual upstream primary/related evidence is forwarded only for nonhealthy/projection-failure paths.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Owning registered proof: `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `persistence-composition`, `diagnostic-catalog-readers`, `platform-observability-runtime`, `platform-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=320592b3a152e3f085b85129578abdd6d36ce560f33d1a123273b946932be64f after=975f98bbb518c8cd75d35cd598ab1da7fbd1a7e0c12814110763dffbff0058d0 -->

<!-- course-file: platform/health/tests/platform-health-types.test.ts -->

### platform-health-types.test.ts

[Open current source](../../../../../platform/health/tests/platform-health-types.test.ts) · **Snapshot:** modified existing file; 13 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for health: public status and private evidence.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Health-owned closed records distinguish returned degraded/unhealthy states, invocation throw, completion rejection, public projection failure and lifecycleReady=false without guessing a cause. Zero-based check indices avoid arbitrary names; actual upstream primary/related evidence is forwarded only for nonhealthy/projection-failure paths.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `publicMessage`, `publicMetadata`, `privateDependency`, `privateField`, `privateMessage`.

New declarations within this existing file: `publicMessage`, `publicMetadata`, `privateDependency`, `privateField`, `privateMessage`.

Owning registered proof: `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6409f41f9464aa6b70c237b26b307b7c3d9108271920e1897e4ca91e5736a18a after=fd8d80cb011f6ea58fbbeff4232208becfed03fbb16518c793402377ffe3b2b3 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why is replacing arbitrary public prose an intentional compatibility decision, rather than a transparent refactor?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Healthy local checks do not establish live deployment acceptance or prove remote log delivery. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/health/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L043 platform/health](043-platform-health.md) · [L044 platform/health/contracts](044-platform-health-contracts.md) · [L045 platform/health/src](045-platform-health-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
