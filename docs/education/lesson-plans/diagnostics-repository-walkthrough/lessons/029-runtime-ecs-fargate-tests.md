<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l029
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/runtime/ecs-fargate/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L029 — platform/adapters/aws/runtime/ecs-fargate/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/runtime/ecs-fargate/tests -->

## What you will understand

Runtime mounts apps into a registry, builds request/job contexts and coordinates startup and shutdown.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **4 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

The second app fails during mount after the first registered successfully. Report the actual boundary using available selected catalogs; do not pretend that no registration happened or rerun the first app for diagnostics.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Mounting and lifecycle already existed. A thrown app callback, invalid registration and shutdown failure could become one generic failure without retaining the stage reached.

**After:** Optional observers identify registry/state/context/lifecycle boundaries, retain selected catalogs and preserve source evidence. Existing app order and original errors remain the compatibility boundary.

**Why this was needed:** An agent needs to know whether failure occurred while declaring a route, constructing a context, starting work or shutting down. These imply different affected components.

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-boundaries.test.mjs -->

### ecs-fargate-adapter-boundaries.test.mjs

[Open current source](../../../../../platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-boundaries.test.mjs) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for application mounting and lifecycle.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Server owns trust rejection/fallback meanings; ECS translates only the actual configured-mode predicate and final-forwarded-address/fallback selection. Original RangeError text/class, result, header/peer/trim/isIP read order and fallback behavior remain.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Owning registered proof: `ecs-fargate-runtime`, `platform-server-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=5cb2f87a073f99569e79c3d5827450ec603dc01aa0a7339ebee3e4b72a5534bf after=dcff0570d957f594ca82cb289390df7204b6d136f9d453d460e01bb1f5c2ef75 -->

<!-- course-file: platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-runtime.test.ts -->

### ecs-fargate-adapter-runtime.test.ts

[Open current source](../../../../../platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-runtime.test.ts) · **Snapshot:** modified existing file; 63 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for application mounting and lifecycle.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Server owns trust rejection/fallback meanings; ECS translates only the actual configured-mode predicate and final-forwarded-address/fallback selection. Original RangeError text/class, result, header/peer/trim/isIP read order and fallback behavior remain.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `diagnosticsProof`.

New declarations within this existing file: `diagnosticsProof`.

Added import edges: `node:module`.

Owning registered proof: `ecs-fargate-runtime`, `platform-server-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=12cc1cd72778d9d136e94ae45bdcb5857c7e29e2e89f690f4000b3c45164054b after=b9eb0962f8c6c2add7e64abf56a4365c4f9fe736f996ce9526fe2b4c4e0fc5fa -->

<!-- course-file: platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-types.test.ts -->

### ecs-fargate-adapter-types.test.ts

[Open current source](../../../../../platform/adapters/aws/runtime/ecs-fargate/tests/ecs-fargate-adapter-types.test.ts) · **Snapshot:** added (absent from baseline); 13 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for application mounting and lifecycle.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Server owns trust rejection/fallback meanings; ECS translates only the actual configured-mode predicate and final-forwarded-address/fallback selection. Original RangeError text/class, result, header/peer/trim/isIP read order and fallback behavior remain.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `resolver`, `observed`, `invalid`.

Added import edges: `../src/index`, `@kanbien/platform-server`.

Owning registered proof: `ecs-fargate-runtime`, `platform-server-runtime`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=6640dfb8e4053831c4eaaaa2fdce9d9fd676bc56c87fe19df2f4050d440bf8e5 -->

<!-- course-file: platform/adapters/aws/runtime/ecs-fargate/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../platform/adapters/aws/runtime/ecs-fargate/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 22 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `runtimeRoot`, `coreModules`, `packages`, `result`.

New declarations within this existing file: `runtimeRoot`, `coreModules`, `packages`.

Added import edges: `node:fs`, `node:path`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=1e2bc3a149a3682374dd623c46826462a0926fdefd44729525c84546f5559e96 after=c326b9923157d6958237e9381042fe1833c93b9633656f758e008978a49924da -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What state is known when mount fails after an earlier app has registered routes?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** A reported shutdown deadline is an observation, not proof that work was cancelled or cleanup completed. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/runtime/ecs-fargate/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L027 platform/adapters/aws/runtime/ecs-fargate](027-aws-runtime-ecs-fargate.md) · [L028 platform/adapters/aws/runtime/ecs-fargate/src](028-runtime-ecs-fargate-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 4 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
