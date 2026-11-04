<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l033
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/runtime/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L033 — platform/runtime/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/runtime/tests -->

## What you will understand

Runtime mounts apps into a registry, builds request/job contexts and coordinates startup and shutdown.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **6 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

The second app fails during mount after the first registered successfully. Report the actual boundary using available selected catalogs; do not pretend that no registration happened or rerun the first app for diagnostics.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Mounting and lifecycle already existed. A thrown app callback, invalid registration and shutdown failure could become one generic failure without retaining the stage reached.

**After:** Optional observers identify registry/state/context/lifecycle boundaries, retain selected catalogs and preserve source evidence. Existing app order and original errors remain the compatibility boundary.

**Why this was needed:** An agent needs to know whether failure occurred while declaring a route, constructing a context, starting work or shutting down. These imply different affected components.

This directory contains `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/runtime/tests/context-diagnostics-runtime.test.ts -->

### context-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/runtime/tests/context-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 71 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for application mounting and lifecycle.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Code-owned Runtime state and boundary records observe original construction, phase-local iteration/selection/invocation/completion/event/projection and request/job-context boundaries without supplied IDs or error text. Raw throws, legacy Results/state, reverse cleanup, native getter/receiver/order and first-failure behavior remain.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `secret`, `cause`, `request`, `now`, `jobName`, `job`, `expected`, `reads`, `emitted`, `input`, `tenantReads`, `flagCalls` (6 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/shared`, `@kanbien/core/queues`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-runtime-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=fcedc48d6f535b8c22e414832dc364b5aed8bb5242354b19c6122567c1b547f2 -->

<!-- course-file: platform/runtime/tests/diagnostics-runtime.test.ts -->

### diagnostics-runtime.test.ts

[Open current source](../../../../../platform/runtime/tests/diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 68 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for application mounting and lifecycle.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. Production/testing share existing meanings and copied selected config evidence; no new policy is introduced.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `definition`, `catalog`, `registry`, `app`, `accessed`, `definitions`, `snapshot`, `classes`, `arrayGets`, `suppliedClasses`, `declarationReads`, `changingProfile`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `../src/index`, `@kanbien/platform-contracts`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=ddbf62eb3e52353561f65cb419af61a6fa534d3bbc10647ce07132ad00269887 -->

<!-- course-file: platform/runtime/tests/lifecycle-diagnostics-runtime.test.ts -->

### lifecycle-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/runtime/tests/lifecycle-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 164 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for application mounting and lifecycle.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Code-owned Runtime state and boundary records observe original construction, phase-local iteration/selection/invocation/completion/event/projection and request/job-context boundaries without supplied IDs or error text. Raw throws, legacy Results/state, reverse cleanup, native getter/receiver/order and first-failure behavior remain.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `secret`, `cause`, `id`, `appId`, `app`, `failed`, `detail`, `base`, `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/shared`, `@kanbien/platform-contracts`, `../src/index`.

Owning registered proof: `platform-runtime-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=ea2da30646fa9e913d66bf587416658b7e5c1578fd36fc63536c2af48f4f01fb -->

<!-- course-file: platform/runtime/tests/lifecycle-diagnostics-types.test.ts -->

### lifecycle-diagnostics-types.test.ts

[Open current source](../../../../../platform/runtime/tests/lifecycle-diagnostics-types.test.ts) · **Snapshot:** added (absent from baseline); 10 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for application mounting and lifecycle.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Code-owned Runtime state and boundary records observe original construction, phase-local iteration/selection/invocation/completion/event/projection and request/job-context boundaries without supplied IDs or error text. Raw throws, legacy Results/state, reverse cleanup, native getter/receiver/order and first-failure behavior remain.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `legacy`, `options`, `invalid`.

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/platform-contracts`, `../src/index`.

Owning registered proof: `platform-runtime-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=2eae7841fc080023750e8dd80706204a30734945eb27159691b7c2ea996ce15b -->

<!-- course-file: platform/runtime/tests/mount-boundary-diagnostics-runtime.test.ts -->

### mount-boundary-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/runtime/tests/mount-boundary-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 72 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for application mounting and lifecycle.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Code-owned Runtime state and boundary records observe original construction, phase-local iteration/selection/invocation/completion/event/projection and request/job-context boundaries without supplied IDs or error text. Raw throws, legacy Results/state, reverse cleanup, native getter/receiver/order and first-failure behavior remain.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `secret`, `cause`, `checkedId`, `id`, `detail`, `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`, `platform-server-runtime`, `platform-workers-runtime`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=1a3f827e694d9c9bcd67d9d06bb0e389cdfcc4f1191ba38f355547b2730a3ff0 -->

<!-- course-file: platform/runtime/tests/registration-diagnostics-runtime.test.ts -->

### registration-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/runtime/tests/registration-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 99 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for application mounting and lifecycle.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. Production/testing share existing meanings and copied selected config evidence; no new policy is introduced.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `requirement`, `baseRoute`, `baseJob`, `record`, `failure`, `resourceRoute`, `production`, `testing`, `proveMountPreservation`.

Added import edges: `node:assert/strict`, `../src/index`, `@kanbien/platform-testing`, `@kanbien/platform-contracts`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=31ccf7705ea29c279b1b98a3c2e356e32851286641001899a08238e37d5dc0d4 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What state is known when mount fails after an earlier app has registered routes?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** A reported shutdown deadline is an observation, not proof that work was cancelled or cleanup completed. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/runtime/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L030 platform/runtime](030-platform-runtime.md) · [L031 platform/runtime/contracts](031-platform-runtime-contracts.md) · [L032 platform/runtime/src](032-platform-runtime-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 6 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
