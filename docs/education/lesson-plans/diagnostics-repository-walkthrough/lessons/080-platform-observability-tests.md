<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l080
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-09"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/observability/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L080 — platform/observability/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/observability/tests -->

## What you will understand

Platform observability wraps logging, metrics, traces and readiness observation; it does not itself choose every provider or backend.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **10 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A metric recording throws and the optional diagnostic sink also rejects. Preserve the workload result and avoid recursive reporting. The bounded binding records attempts, not guaranteed delivery; suppression must not be called full coverage.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The observability slice already implemented telemetry. Several best-effort failures were swallowed or coarsely normalized, so lack of telemetry could be hard to explain.

**After:** Owned records distinguish configuration, preparation, validation, creation, recording, collection, export, flush/shutdown and wrapper failures. Bounded reporting stays independent of the failed telemetry operation.

**Why this was needed:** An agent must tell a rejected metric from a recording invocation, collection issue or exporter failure. None of those alone prove what the backend retained.

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/observability/tests/integration/configuration-runtime.test.ts -->

### configuration-runtime.test.ts

[Open current source](../../../../../platform/observability/tests/integration/configuration-runtime.test.ts) · **Snapshot:** added (absent from baseline); 99 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for diagnostics for telemetry itself.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Pure shared metric-series/readiness configuration predicates produce closed logical reasons and zero-based positions, independent comparisons, bounded explicit overflow and no supplied values. Construction uncertainty has a separate unknown definition; no remote delivery or runtime metric-point claim is made.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `row`, `issues`, `distribution`, `getterReads`, `getter`, `overflow`, `schedule`, `independent`, `accessorSchedule`, `diagnostic`, `construction`, `logs` (2 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `../src/index`.

Owning registered proof: `platform-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=5233a37fe377a67532f346b0f474dadfb7b70afbd3a78b2b9cb2bd47df1d6ed7 -->

<!-- course-file: platform/observability/tests/type-level/configuration-types.test.ts -->

### configuration-types.test.ts

[Open current source](../../../../../platform/observability/tests/type-level/configuration-types.test.ts) · **Snapshot:** added (absent from baseline); 17 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for diagnostics for telemetry itself.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Pure shared metric-series/readiness configuration predicates produce closed logical reasons and zero-based positions, independent comparisons, bounded explicit overflow and no supplied values. Construction uncertainty has a separate unknown definition; no remote delivery or runtime metric-point claim is made.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `checked`, `unknownReason`, `readiness`.

Added import edges: `@kanbien/core/config`, `../src/index`.

Owning registered proof: `platform-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=299f6e0564af171a87697c19158957ef0239978658a45f1999c97577d68ae8b9 -->

<!-- course-file: platform/observability/tests/integration/diagnostics-runtime.test.ts -->

### diagnostics-runtime.test.ts

[Open current source](../../../../../platform/observability/tests/integration/diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 95 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for diagnostics for telemetry itself.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Five closed definitions across collection, export, flush and shutdown families distinguish returned errors/count from failed collection, callback failure from thrown export, and exact lifecycle boundary/rejection/SDK timeout with unknown effect. Separate recording and lifecycle bindings share finite reporting mechanics without widening same-error/same-port provenance.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `definition`, `records`, `reporter`, `record`, `checkedRecord`, `context`, `unavailable`, `wrappedUnavailable`, `accessed`, `accessorRecord`, `nested`, `manyIssues` (6 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `../src/index`.

Owning registered proof: `platform-contracts-runtime`, `platform-observability-runtime`, `diagnostic-catalog-readers`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=b88fe2c2531237a0c47ea3cee1289e60c15e4abdbde14fa8f9beae8ceaa1b0a8 -->

<!-- course-file: platform/observability/tests/integration/metric-diagnostics-runtime.test.ts -->

### metric-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/observability/tests/integration/metric-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 248 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for diagnostics for telemetry itself.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Two pure additive closed definitions describe unknown observation boundary failures and truthful lifetime attempt suppression. They carry finite logical locations/effects only; no raw supplied values, exception text or automatic recovery grant.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `clock`, `valid`, `capture`, `detail`, `main`, `bindingSinkCoverage`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/monitoring`, `@kanbien/core/logging`, `@kanbien/platform-contracts`, `../src/index`.

Owning registered proof: `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`, `platform-health-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=06dbbff10e937acd232a92d697cb0be5cff24ebe8532007c0c2fe96af8aa5003 -->

<!-- course-file: platform/observability/tests/integration/metric-lifecycle-diagnostics-runtime.test.ts -->

### metric-lifecycle-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/observability/tests/integration/metric-lifecycle-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 62 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for diagnostics for telemetry itself.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Five closed definitions across collection, export, flush and shutdown families distinguish returned errors/count from failed collection, callback failure from thrown export, and exact lifecycle boundary/rejection/SDK timeout with unknown effect. Separate recording and lifecycle bindings share finite reporting mechanics without widening same-error/same-port provenance.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `logs`, `reporter`, `binding`, `expected`, `actual`, `getterReads`, `getterRecord`, `recording`, `attempts`, `unavailable`, `recursiveAttempts`, `recursive` (1 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `../src/index`.

Owning registered proof: `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`, `platform-contracts-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=e4592b27efccea828d433af45fb043d6e4c42cc8b3e1e92a9f89180a64c49985 -->

<!-- course-file: platform/observability/tests/integration/platform-observability-runtime.test.ts -->

### platform-observability-runtime.test.ts

[Open current source](../../../../../platform/observability/tests/integration/platform-observability-runtime.test.ts) · **Snapshot:** modified existing file; 172 added / 7 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for diagnostics for telemetry itself.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Two pure additive closed definitions describe unknown observation boundary failures and truthful lifetime attempt suppression. They carry finite logical locations/effects only; no raw supplied values, exception text or automatic recovery grant.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `boundaryCoverage`, `classificationProof`.

New declarations within this existing file: `boundaryCoverage`, `classificationProof`.

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/core/persistence`.

Owning registered proof: `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`, `platform-health-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=209783bb27e17409ff12b3a8021af3dc6d76558e9eada1b22b2312d07cb0defd after=c17b96c5dcddea126ea1fc9452ca76dedf181532430b5d8fc833c9160059ffd1 -->

<!-- course-file: platform/observability/tests/type-level/platform-observability-types.test.ts -->

### platform-observability-types.test.ts

[Open current source](../../../../../platform/observability/tests/type-level/platform-observability-types.test.ts) · **Snapshot:** modified existing file; 23 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for diagnostics for telemetry itself.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): The explicitly approved finite classification policy preserves normalized error field structure while admitting only actual native runtime-type groups and exact owner/app-declared members. Present undeclared/accessor codes become unknown; names/messages/causes are not guessed or executed.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `observations`, `classBinding`, `metricBinding`.

New declarations within this existing file: `observations`, `classBinding`, `metricBinding`.

Owning registered proof: `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`, `platform-health-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=4c1b14ccf3d96518eb6836a89d5045c74d82617067e96e8eaa0dd099c9355478 after=96c744e6c4b38495ea67d8c8db44089c1d85fb850cf4b19787103d480d18c9b7 -->

<!-- course-file: platform/observability/tests/integration/readiness-diagnostics-runtime.test.ts -->

### readiness-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/observability/tests/integration/readiness-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 189 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for diagnostics for telemetry itself.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Readiness-event rejection identifies the exact first observed logical predicate and actual traversal ordinal without supplied fields/values. Separate unknown boundary observations distinguish structure, enumeration, traversal selection/invocation, field/result projection and time parsing.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `clock`, `expected`, `main`, `laterBoundaryEvidence`, `operationalEventEvidence`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/platform-contracts`, `@kanbien/core`, `../../persistence/src/diagnostics`, `@kanbien/platform-security`, `../src/index`, `@kanbien/core/persistence`.

Owning registered proof: `platform-contracts-runtime`, `platform-observability-runtime`, `platform-shell-payload`, `persistence-composition`, `diagnostic-catalog-readers`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=276ec367602b01528a43148be0cd06cb22d3c424d89220e85ff11d1da2014479 -->

<!-- course-file: platform/observability/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../platform/observability/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 7 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreModules`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=914ab43e05ccf5777ce49822b6e6cd4490e93fd0765a3bf39b91dc33f4a902f9 after=6a894883e3054df6e6430680caf5ff4b636abfcdeb068e984935e6c78d0f9545 -->

<!-- course-file: platform/observability/tests/integration/security-diagnostics-runtime.test.ts -->

### security-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/observability/tests/integration/security-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 49 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for diagnostics for telemetry itself.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Parse complete certificate blocks with exact one-based malformed-block records, plus explicit strict marker validation; preserve production complete-block acceptance and comments without retaining content/native errors or claiming CA role, lifetime or peer trust.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `records`, `reporter`, `result`, `context`, `unavailable`, `primary`, `related`, `attempts`, `onlyPersistence`, `readinessRecords`, `logger`, `clock` (1 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `../../persistence/src/diagnostics`, `@kanbien/core/logging`, `@kanbien/platform-security`, `../src/index`.

Owning registered proof: `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `diagnostic-catalog-readers`, `platform-security-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=715859cbcebc00497267554f50f9212f2e0b2c8f9bd59d42032d5464879fe036 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why would sending a logger-failed diagnostic through the same failed logger recursively be dangerous?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No SDK or metrics backend is introduced here. SDK-internal failures that never cross observable public boundaries cannot be invented as observed facts. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/observability/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L077 platform/observability](077-platform-observability.md) · [L078 platform/observability/contracts](078-platform-observability-contracts.md) · [L079 platform/observability/src](079-platform-observability-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 10 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
