<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l073
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/workers/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L073 — platform/workers/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/workers/tests -->

## What you will understand

Workers receive jobs, validate payloads, coordinate durable claims, invoke handlers and settle delivery. Queue adapters implement transport operations.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **11 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A handler returns successfully, then acknowledgement throws. Describe the observed acknowledgement invocation with uncertain effect. Do not report handler rejection or replay it merely to obtain a diagnostic.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Worker processing and queues already existed. Invalid payload, lost claim, handler failure and acknowledgement uncertainty could lose their distinct locations and source facts.

**After:** Closed worker/queue records describe actual validation, coordination, handler and settlement boundaries. Optional reporting preserves attempt multiplicity, profile opt-outs and original business results.

**Why this was needed:** A failed acknowledgement may follow successful business work. Treating it as handler-not-run could duplicate effects on recovery.

This directory contains `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/workers/tests/builtin-evidence-runtime.test.ts -->

### builtin-evidence-runtime.test.ts

[Open current source](../../../../../platform/workers/tests/builtin-evidence-runtime.test.ts) · **Snapshot:** added (absent from baseline); 71 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for worker processing and queue delivery.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `checkedId`, `id`, `records`, `source`, `own`, `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`, `../src/diagnostics`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=a21b87d15d9b3b6af502351e96cca3342af22eea9598eb6ffe5f9b072338afc1 -->

<!-- course-file: platform/workers/tests/context-boundary-diagnostics-runtime.test.ts -->

### context-boundary-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/workers/tests/context-boundary-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 135 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for worker processing and queue delivery.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `secret`, `checkedId`, `checkedJob`, `checkedProfile`, `checkedCapability`, `id`, `name`, `profile`, `capability`, `definition`, `records`, `location` (1 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/core/queues`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`, `../src/errors`, `@kanbien/platform-persistence`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=44ae2c092287d33023f1281688e391f227660ce40f187a4e0ec7898ddf6b8782 -->

<!-- course-file: platform/workers/tests/delivery-boundary-diagnostics-runtime.test.ts -->

### delivery-boundary-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/workers/tests/delivery-boundary-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 243 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for worker processing and queue delivery.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `required`, `id`, `name`, `profileName`, `capability`, `type`, `definition`, `records`, `source`, `failed`, `own` (6 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/monitoring`, `@kanbien/core/queues`, `@kanbien/core/shared`, `@kanbien/platform-contracts`, `@kanbien/platform-persistence`, `@kanbien/platform-testing`, `../src/index`, `../src/errors` (more in source).

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=59f52fe031279ac6a71379c2d28c566b8bbd08ad88004b6d8506f16b6c447527 -->

<!-- course-file: platform/workers/tests/health-diagnostics-runtime.test.ts -->

### health-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/workers/tests/health-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 46 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for worker processing and queue delivery.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Health-owned closed records distinguish returned degraded/unhealthy states, invocation throw, completion rejection, public projection failure and lifecycleReady=false without guessing a cause. Zero-based check indices avoid arbitrary names; actual upstream primary/related evidence is forwarded only for nonhealthy/projection-failure paths.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/logging`, `@kanbien/core/diagnostics`, `@kanbien/core/monitoring`, `@kanbien/core/shared`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=2b05ab6dcdc7f48598a312a1babef00f0217974364710e23d4773657161c1773 -->

<!-- course-file: platform/workers/tests/lifecycle-boundary-diagnostics-runtime.test.ts -->

### lifecycle-boundary-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/workers/tests/lifecycle-boundary-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 108 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for worker processing and queue delivery.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Code-owned Runtime state and boundary records observe original construction, phase-local iteration/selection/invocation/completion/event/projection and request/job-context boundaries without supplied IDs or error text. Raw throws, legacy Results/state, reverse cleanup, native getter/receiver/order and first-failure behavior remain.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `secret`, `checkedId`, `id`, `definition`, `records`, `source`, `literals`, `runtime`, `Mode`, `sink`, `app`, `expectSeen` (1 more in source).

Added import edges: `node:assert/strict`, `node:timers/promises`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`, `platform-runtime-runtime`, `platform-server-runtime`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=03d16e67deac57d0f45cc1920aeeafecad1c80a7d1b6359849c307352ad97a53 -->

<!-- course-file: platform/workers/tests/lifecycle-boundary-diagnostics-types.test.ts -->

### lifecycle-boundary-diagnostics-types.test.ts

[Open current source](../../../../../platform/workers/tests/lifecycle-boundary-diagnostics-types.test.ts) · **Snapshot:** added (absent from baseline); 11 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for worker processing and queue delivery.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `catalogs`, `processOptions`, `shellOptions`, `legacy`, `invalid`.

Added import edges: `@kanbien/platform-contracts`, `../src/index`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=dce641501bd0d146e4dba67d2b9621e0bc2467e4d42de625d148f4e9bde3e46b -->

<!-- course-file: platform/workers/tests/metric-diagnostics-runtime.test.ts -->

### metric-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/workers/tests/metric-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 43 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for worker processing and queue delivery.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Four additive code-owned definitions distinguish current Core preparation predicates and precise raw-access locations, trusted same-port adapter rejections, creation not-attempted and invocation unknown effect. Independent bindings preserve helper void/API compatibility and bounded opt-out-aware reporting.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `node:assert/strict`, `@kanbien/platform-contracts`, `@kanbien/core/logging`, `@kanbien/core/queues`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=7f2b5da4392b2c869e5c398575a7ed49bdced2d16b10d2e9ca2b3c04e31a5f48 -->

<!-- course-file: platform/workers/tests/platform-workers-runtime.test.ts -->

### platform-workers-runtime.test.ts

[Open current source](../../../../../platform/workers/tests/platform-workers-runtime.test.ts) · **Snapshot:** modified existing file; 19 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for worker processing and queue delivery.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=be99b44ad628314b6cb6cd5d4ff8f0bacb382ff0fc2c8a187a5fe357516d0a3c after=7871efd0b3c3ec65beddccdf36a41b70241493916085c3db516a43cbe773c879 -->

<!-- course-file: platform/workers/tests/platform-workers-types.test.ts -->

### platform-workers-types.test.ts

[Open current source](../../../../../platform/workers/tests/platform-workers-types.test.ts) · **Snapshot:** modified existing file; 2 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for worker processing and queue delivery.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `observedQueue`.

New declarations within this existing file: `observedQueue`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f875680f735a3a0d8bb409fbb45d99456e88a3d2b3e7427235e20e4c45de5a46 after=6945a1c3c289ae46f90f9ec3ba033e63b1ac6eb4bac301ed20c2a34272477b7d -->

<!-- course-file: platform/workers/tests/process-boundary-diagnostics-runtime.test.ts -->

### process-boundary-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/workers/tests/process-boundary-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 101 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for worker processing and queue delivery.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `secret`, `checkedId`, `id`, `definition`, `records`, `source`, `app`, `worker`, `runtime`, `sink`, `main`.

Added import edges: `node:assert/strict`, `node:timers/promises`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/platform-contracts`, `../src/index`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=30cb89e4456d01b28b2c5fd488b9f56a6904b4c284949524cbd8b75b8041e88c -->

<!-- course-file: platform/workers/tests/startup-configuration-diagnostics-runtime.test.ts -->

### startup-configuration-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/workers/tests/startup-configuration-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 206 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for worker processing and queue delivery.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued worker boundary errors and explicitly selected configuration/app definitions preserve validated upstream observations through worker failures and delivery reporting. Generic health() selects health-owned definitions and forwards the reporter without inheriting job policy.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `id`, `route`, `appId`, `routeName`, `definition`, `appRecords`, `appLiterals`, `coreLiteral`, `positionLiteral`, `parseLiteral`, `sourceLiteral` (8 more in source).

Added import edges: `node:assert/strict`, `node:timers/promises`, `@kanbien/core`, `@kanbien/core/config`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-workers-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=c3d75f03ff262004d97f005f87a14074052508478d638882f45b966992a37a80 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What must an agent investigate before retrying a delivery whose settlement failed?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** This is not a new exactly-once policy, retry policy or queue backend. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/workers/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L070 platform/workers](070-platform-workers.md) · [L071 platform/workers/contracts](071-platform-workers-contracts.md) · [L072 platform/workers/src](072-platform-workers-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 11 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
