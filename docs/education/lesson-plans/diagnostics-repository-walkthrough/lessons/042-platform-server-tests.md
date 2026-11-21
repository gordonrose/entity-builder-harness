<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l042
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-09"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/server/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L042 — platform/server/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/server/tests -->

## What you will understand

The server resolves configuration, starts a listener, admits transport requests, creates context, authenticates/authorizes, invokes handlers and writes responses.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **17 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Send a body that fails the existing decode boundary, then contrast a valid body whose handler throws. Keep the established public response, but give the internal agent distinct evidence for each observed stage.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The HTTP path already existed. Several fallback choices, rejected inputs and thrown transport/request boundaries were observable only as broad failures.

**After:** Closed records identify listener/port/health choices, transport predicates, decode/context/handler boundaries, writer/drain/close failures and process stages. Selected upstream evidence travels internally without entering response metadata.

**Why this was needed:** A fallback port is not a listener failure; a handler exception is not invalid JSON; a response-write failure does not prove that the handler never ran.

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/server/tests/integration/builtin-evidence-runtime.test.ts -->

### builtin-evidence-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/builtin-evidence-runtime.test.ts) · **Snapshot:** added (absent from baseline); 81 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. Explicit target catalogs compose with built-ins/apps while retaining conflict validation and injected-reporter precedence.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `checkedId`, `id`, `records`, `source`, `own`, `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/core/config`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`, `../src/diagnostics`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=4eed68a6744f08efb9d5b33c0fefd7b472eb88f09c3737f0d99ca9ee4f44c97d -->

<!-- course-file: platform/server/tests/unit/configuration-omissions-runtime.test.ts -->

### configuration-omissions-runtime.test.ts

[Open current source](../../../../../platform/server/tests/unit/configuration-omissions-runtime.test.ts) · **Snapshot:** added (absent from baseline); 43 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): One shared resolver explains host/port and health exposure choices with closed bounded records; preserves original API, Number conversion, programmatic overrides including port zero, defaults and HTTP behavior. Exact reasons, independent choices and safe delivery are tested.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `coercions`, `object`, `thrown`, `attempts`.

Added import edges: `node:assert/strict`, `../src/index`, `@kanbien/core/diagnostics`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`, `core-dependency-boundary`, `persistence-composition`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=0a09f9c408a18a774f9e5f9540b6302248513263018c09a2e5de66bd0e38dcdf -->

<!-- course-file: platform/server/tests/integration/configuration-runtime.test.ts -->

### configuration-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/configuration-runtime.test.ts) · **Snapshot:** added (absent from baseline); 199 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): One shared resolver explains host/port and health exposure choices with closed bounded records; preserves original API, Number conversion, programmatic overrides including port zero, defaults and HTTP behavior. Exact reasons, independent choices and safe delivery are tested.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `details`, `legacy`, `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/platform-contracts`, `@kanbien/platform-observability`, `../src/index`, `../src/main`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`, `core-dependency-boundary`, `persistence-composition`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=4f3d5d5e169352cbe7b902a025b468b106dfd697a1197ed82d45d86e22a25951 -->

<!-- course-file: platform/server/tests/integration/diagnostics-runtime.test.ts -->

### diagnostics-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 68 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. Explicit target catalogs compose with built-ins/apps while retaining conflict validation and injected-reporter precedence.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/validation`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=16efca98a60025668a8f8d49543548ed7269f86e4e165c46a0481951b8c09a15 -->

<!-- course-file: platform/server/tests/integration/health-diagnostics-runtime.test.ts -->

### health-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/health-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 56 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Health-owned closed records distinguish returned degraded/unhealthy states, invocation throw, completion rejection, public projection failure and lifecycleReady=false without guessing a cause. Zero-based check indices avoid arbitrary names; actual upstream primary/related evidence is forwarded only for nonhealthy/projection-failure paths.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/logging`, `@kanbien/core/diagnostics`, `@kanbien/core/monitoring`, `@kanbien/core/shared`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=d1fa87cf878302daf54635f7a31f37f2f8ae0f654a87d910f2c5322cb699427b -->

<!-- course-file: platform/server/tests/integration/metric-diagnostics-runtime.test.ts -->

### metric-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/metric-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 40 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Four additive code-owned definitions distinguish current Core preparation predicates and precise raw-access locations, trusted same-port adapter rejections, creation not-attempted and invocation unknown effect. Independent bindings preserve helper void/API compatibility and bounded opt-out-aware reporting.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `node:assert/strict`, `@kanbien/platform-contracts`, `@kanbien/core/logging`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=6244f93d4087643fcb8a5e3bb968cad203cc3f4ff825350b9078f3277d51da26 -->

<!-- course-file: platform/server/tests/integration/platform-server-runtime.test.ts -->

### platform-server-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/platform-server-runtime.test.ts) · **Snapshot:** modified existing file; 14 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. Explicit target catalogs compose with built-ins/apps while retaining conflict validation and injected-reporter precedence.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=de02d2ea1a761e7438ed90c2f4ed821cc2fa2cc9cfd191ba9874ae0731bffb15 after=70f5a32ab3f2febd281993727765229130ac977a78f32fd9c1383d2cd4d9ebfb -->

<!-- course-file: platform/server/tests/type-level/platform-server-types.test.ts -->

### platform-server-types.test.ts

[Open current source](../../../../../platform/server/tests/type-level/platform-server-types.test.ts) · **Snapshot:** modified existing file; 10 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for http transport and request handling.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): One shared resolver explains host/port and health exposure choices with closed bounded records; preserves original API, Number conversion, programmatic overrides including port zero, defaults and HTTP behavior. Exact reasons, independent choices and safe delivery are tested.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `shell`, `configurationObservation`.

New declarations within this existing file: `configurationObservation`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`, `core-dependency-boundary`, `persistence-composition`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b2f1b07ab1b6dadd52eaee61e4d3791d0532351c8cdbb9b3ad02f1d3157a3b7b after=24026805419ed5764934702d142a3603263c4b116fcb45c075ed9bfe819d631a -->

<!-- course-file: platform/server/tests/integration/process-boundary-diagnostics-runtime.test.ts -->

### process-boundary-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/process-boundary-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 134 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): One shared resolver explains host/port and health exposure choices with closed bounded records; preserves original API, Number conversion, programmatic overrides including port zero, defaults and HTTP behavior. Exact reasons, independent choices and safe delivery are tested.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `observations`, `selectionAndRegistrationBoundaries`, `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/logging`, `@kanbien/platform-contracts`, `../src/main`, `node:http`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`, `core-dependency-boundary`, `persistence-composition`, `platform-shell-payload`, `platform-runtime-runtime`, `platform-workers-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=660ccd04430060f836228fb515f441240c07841e68b5b8aa5fa72e270e2218b5 -->

<!-- course-file: platform/server/tests/integration/request-boundary-diagnostics-runtime.test.ts -->

### request-boundary-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/request-boundary-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 233 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. Explicit target catalogs compose with built-ins/apps while retaining conflict validation and injected-reporter precedence.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `id`, `capability`, `profile`, `appId`, `capabilityName`, `profileName`, `permission`, `requestId`, `definition`, `evidence`, `evidenceLiterals` (12 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/core/shared`, `@kanbien/core/tenancy`, `@kanbien/core/validation`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=b106c0023662f3d1173525d96595c94440035894075f9678fbfe74829628fc67 -->

<!-- course-file: platform/server/tests/integration/request-observation-runtime.test.ts -->

### request-observation-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/request-observation-runtime.test.ts) · **Snapshot:** added (absent from baseline); 236 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Connection/IAM/administrator/source/certificate observations and bounded configuration aggregation retain existing defaults, SQL, validation order and outward codes. Actual target /readyz explicitly selects the persistence catalog; its typed health subtype retains primary/security evidence through one selected observation or one legacy readiness call, with the original receiver and cleanup.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `checkedId`, `checkedCapability`, `checkedProfile`, `checkedMetricProfile`, `appId`, `capability`, `profile`, `metricProfile`, `definition`, `literals`, `records` (8 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/monitoring`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/core/shared`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`, `../../observability/src/normalization`, `../../contracts/src/observability-profiles`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`, `persistence-composition`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=e62a8310278dc456760a1e9f6070e15509c9084b71f2755836697dce18fdea3f -->

<!-- course-file: platform/server/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../platform/server/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreModules`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=5391e040aa6e0a67c8625733b48cf318908cf249269d8b4186423d63d5760721 after=5f47db0d7359fe738a15268db10fdc1f2611a22a21696c3b6bdee6b2235de603 -->

<!-- course-file: platform/server/tests/integration/security-diagnostics-runtime.test.ts -->

### security-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/security-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 175 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Core owns additive principal and tenant-constructor boundary definitions. Optional observers independently deliver the exact observed projection/copy location and selected source primary plus up to eight related records, preserving raw primitive/frozen throw identity, eager claims enumeration, repeated getters, scope iteration and nullish tenant fallback.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `main`.

Added import edges: `node:assert/strict`, `@kanbien/core/authz`, `@kanbien/core/diagnostics`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `@kanbien/platform-security`, `../src/index`.

Owning registered proof: `core-runtime`, `platform-security-runtime`, `platform-server-runtime`, `diagnostic-catalog-readers`, `security-shared-rate-limit-diagnostics`, `shell-package-source`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=2ef392548ae38acb40aee771fdadfd057bf35fc9d26675b2f9b3198d88e72912 -->

<!-- course-file: platform/server/tests/integration/startup-configuration-diagnostics-runtime.test.ts -->

### startup-configuration-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/startup-configuration-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 211 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. Explicit target catalogs compose with built-ins/apps while retaining conflict validation and injected-reporter precedence.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `id`, `route`, `appId`, `routeName`, `definition`, `appRecords`, `appLiterals`, `coreLiteral`, `positionLiteral`, `parseLiteral`, `sourceLiteral` (8 more in source).

Added import edges: `node:assert/strict`, `node:timers/promises`, `@kanbien/core`, `@kanbien/core/config`, `@kanbien/core/diagnostics`, `@kanbien/core/logging`, `@kanbien/platform-contracts`, `@kanbien/platform-testing`, `../src/index`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=b4e91f9a2461af92e81f3f8ca390beb8c10eeea78b09083f29137f2addb44228 -->

<!-- course-file: platform/server/tests/unit/transport-configuration-diagnostics-runtime.test.ts -->

### transport-configuration-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/server/tests/unit/transport-configuration-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 42 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. Explicit target catalogs compose with built-ins/apps while retaining conflict validation and injected-reporter precedence.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `fields`, `baseline`, `relation`, `simultaneous`, `reads`, `withGetter`.

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `../src/transport`, `../src/diagnostics`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=718af6a2c060043658ad24322bc01eb6f0cac1a24aba051e8404f07443f6c9a2 -->

<!-- course-file: platform/server/tests/integration/transport-diagnostics-runtime.test.ts -->

### transport-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/server/tests/integration/transport-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 371 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. Explicit target catalogs compose with built-ins/apps while retaining conflict validation and injected-reporter precedence.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `requestId`, `tick`, `response`, `FakeResponse`, `RequestOptions`, `fakeRequest`, `fixture`, `rejectedRequests`, `callbackBoundaries`, `listenerFailures`, `deadlinesAndCapacity` (4 more in source).

Added import edges: `node:assert/strict`, `node:events`, `node:http`, `@kanbien/core/diagnostics`, `@kanbien/core/shared`, `../src/index`, `../src/diagnostics`, `../src/transport`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=960f1629e53d64598065637446c067da6b18da128caf34e32d26ba2002ce3188 -->

<!-- course-file: platform/server/tests/type-level/transport-diagnostics-types.test.ts -->

### transport-diagnostics-types.test.ts

[Open current source](../../../../../platform/server/tests/type-level/transport-diagnostics-types.test.ts) · **Snapshot:** added (absent from baseline); 29 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for http transport and request handling.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Catalogued server boundary errors preserve public responses and select configuration/shared-security/health definitions. Explicit target catalogs compose with built-ins/apps while retaining conflict validation and injected-reporter precedence.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `record`, `input`, `transportEvidence`, `invalidStatus`.

Added import edges: `@kanbien/core/diagnostics`, `../src/diagnostics`, `../src/transport`.

Owning registered proof: `platform-server-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=8a160652e83a0da18e57e1077b6bcd16e15a59418a3883bdc23774e8c00cc2b0 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: If response writing fails after a handler committed a change, why must diagnostic handling not replay the handler?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No new HTTP routes, authentication policy or public error-detail expansion is implied. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/server/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L037 platform/server](037-platform-server.md) · [L038 platform/server/contracts](038-platform-server-contracts.md) · [L039 platform/server/src](039-platform-server-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 17 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
