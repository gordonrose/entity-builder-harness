<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l026
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-09"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/contracts/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L026 — platform/contracts/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/contracts/tests -->

## What you will understand

Contracts define how apps declare routes, jobs, permissions, configuration, observability profiles and diagnostic catalogs without importing runtime implementations.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **4 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Register a route that references an undeclared observability profile. Observe the registration failure before listening. A structurally valid catalog with a conflicting definition must not silently replace the selected meaning.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail.

**After:** Catalog/reporter/context interfaces, registration observations and finite error-class declarations are explicit. Runtime and test consumers share those meanings, rather than inventing parallel declarations.

**Why this was needed:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/contracts/tests/contract/platform-contracts-runtime.test.ts -->

### platform-contracts-runtime.test.ts

[Open current source](../../../../../platform/contracts/tests/contract/platform-contracts-runtime.test.ts) · **Snapshot:** modified existing file; 158 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for platform registration contracts.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Readiness-event rejection identifies the exact first observed logical predicate and actual traversal ordinal without supplied fields/values. Separate unknown boundary observations distinguish structure, enumeration, traversal selection/invocation, field/result projection and time parsing.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `operationalContractsDiagnostics`.

New declarations within this existing file: `operationalContractsDiagnostics`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-contracts-runtime`, `platform-observability-runtime`, `platform-shell-payload`, `persistence-composition`, `diagnostic-catalog-readers`, `platform-runtime-runtime`, `platform-testing-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b1c1949fe36b08cce922d97ca78433c4f1ab1a17bbfc5d7f82acbd1b7b46ba4b after=62bdc70a38bf5107df78e3b49c223785515c563409a8125ff46027f69ffe3203 -->

<!-- course-file: platform/contracts/tests/type-level/platform-contracts-types.test.ts -->

### platform-contracts-types.test.ts

[Open current source](../../../../../platform/contracts/tests/type-level/platform-contracts-types.test.ts) · **Snapshot:** modified existing file; 38 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for platform registration contracts.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): The optional request-only typed diagnostic callback keeps existing request, runtime and job contexts compatible. Server supplies delivery only under matched-route operational-log permission; this contract adds no provider dependency, sink, response field or framework-wide global observer.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `runtimeDiagnosticContext`, `unknownDiagnosticStage`, `observabilityProfile`, `invalidClassDeclaration`, `operationalDiagnostics`, `observedFlags`, `observedEvent`, `rawOperationalObserver`, `observingRequestContext`.

New declarations within this existing file: `runtimeDiagnosticContext`, `unknownDiagnosticStage`, `invalidClassDeclaration`, `operationalDiagnostics`, `observedFlags`, `observedEvent`, `rawOperationalObserver`, `observingRequestContext`.

Owning registered proof: `platform-contracts-runtime`, `platform-observability-runtime`, `platform-shell-payload`, `persistence-composition`, `diagnostic-catalog-readers`, `platform-runtime-runtime`, `platform-testing-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=33cd48c21df06cdebf7976efe6bc90ffddf115f339cff5839675af3b9c644fc4 after=50604d633dc4b05fd3bd017e37539e7a21e3a3b88b730b6b29e7eb04e5d3595f -->

<!-- course-file: platform/contracts/tests/contract/registration-diagnostics-runtime.test.ts -->

### registration-diagnostics-runtime.test.ts

[Open current source](../../../../../platform/contracts/tests/contract/registration-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 255 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for platform registration contracts.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Contract-owned records observe actual registration/catalog/namespace/duplicate/deferred-reference predicates, preserving legacy codes, permissive admission and getter/first-failure order. Production/testing share existing meanings and copied selected config evidence; no new policy is introduced.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `requirement`, `baseRoute`, `baseJob`, `baseProfile`, `classGetters`, `accessorClasses`, `declarationCases`, `accessorDeclaration`, `accessorRejection`, `arrayGets`, `deceptiveClasses` (25 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/diagnostics`, `../src/index`, `../src/identifiers`.

Owning registered proof: `platform-contracts-runtime`, `platform-runtime-runtime`, `platform-testing-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=f7903da2c37d3335511b1b6315b001b7f3c8efc5c6bf9b4ba85c9d7d44ef3f10 -->

<!-- course-file: platform/contracts/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../platform/contracts/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 6 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreRoot`.

New declarations within this existing file: `coreRoot`.

Added import edges: `../../../packages/core/src/index.js`, `../../../../packages/core/src/diagnostics/index.js`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=b404ff35dcbc26e3f0a7658c5210d402b3f3240de7248d9c070c87fa28990e90 after=aa81015a3d23b9704275eec0dc4d16b642832af53a88dbbfa23ef28cb168e6b0 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why should a Contracts interface not import the concrete HTTP server or AWS adapter?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Registration consistency checks cannot certify architectural judgment or all future failure modes on their own. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/contracts/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L023 platform/contracts](023-platform-contracts.md) · [L024 platform/contracts/contracts](024-platform-contracts-contracts.md) · [L025 platform/contracts/src](025-platform-contracts-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 4 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
