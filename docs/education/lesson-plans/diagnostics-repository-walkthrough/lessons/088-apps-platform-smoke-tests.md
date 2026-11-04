<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l088
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder apps/platform-smoke/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L088 — apps/platform-smoke/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: apps/platform-smoke/tests -->

## What you will understand

Platform-smoke is a real example app that mounts routes/jobs and exercises persistence-backed work-item acceptance.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **5 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A work-item acceptance input fails an existing feature predicate. Preserve the business result; attach the app-owned safe reason. If the writer itself throws, retain selected source evidence separately rather than replacing it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The feature and its endpoints already existed. App-specific configuration and accepted-payload failures could be hidden behind generic platform errors.

**After:** The app declares its own diagnostic catalog and payload/configuration/acceptance observations; Platform and targets select and deliver them. Existing supported acceptance behavior remains.

**Why this was needed:** Only the feature can say what an invalid accepted work item means. Generic HTTP or database code should not own the app vocabulary.

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: apps/platform-smoke/tests/configuration-validation-diagnostics-runtime.test.ts -->

### configuration-validation-diagnostics-runtime.test.ts

[Open current source](../../../../../apps/platform-smoke/tests/configuration-validation-diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 74 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for the sample app owns its feature meaning.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): App owns app-name configuration and accepted-work-item payload predicate meanings, preserving Core reader companions. Actual server config and worker dead-letter delivery are tested default/injected/unavailable.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `reads`, `accessor`, `inaccessible`, `record`, `deep`, `delivery`.

Added import edges: `node:assert/strict`, `@kanbien/core/logging`, `@kanbien/core/diagnostics`, `@kanbien/platform-workers`, `@kanbien/platform-server`, `@kanbien/platform-testing`, `../src/index`, `../src/app.mount`.

Owning registered proof: `platform-smoke-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=6685b96d9c2ea2cb2ec6b86ac0baa085b3342ffa652f28aa859004bad51dc22c -->

<!-- course-file: apps/platform-smoke/tests/diagnostics-runtime.test.ts -->

### diagnostics-runtime.test.ts

[Open current source](../../../../../apps/platform-smoke/tests/diagnostics-runtime.test.ts) · **Snapshot:** added (absent from baseline); 14 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for the sample app owns its feature meaning.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): App owns app-name configuration and accepted-work-item payload predicate meanings, preserving Core reader companions. Actual server config and worker dead-letter delivery are tested default/injected/unavailable.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `unknown`.

Added import edges: `node:assert/strict`, `../src/diagnostics`, `../src/app.mount`.

Owning registered proof: `platform-smoke-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=64160e122b942530af4441d1ffa93524a8a06667f12441a9e410b811b2234cc2 -->

<!-- course-file: apps/platform-smoke/tests/platform-smoke-runtime.test.ts -->

### platform-smoke-runtime.test.ts

[Open current source](../../../../../apps/platform-smoke/tests/platform-smoke-runtime.test.ts) · **Snapshot:** modified existing file; 218 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for the sample app owns its feature meaning.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): App owns app-name configuration and accepted-work-item payload predicate meanings, preserving Core reader companions. Actual server config and worker dead-letter delivery are tested default/injected/unavailable.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `acceptanceDiagnosticCoverage`.

New declarations within this existing file: `acceptanceDiagnosticCoverage`.

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/platform-runtime`, `@kanbien/platform-contracts`.

Owning registered proof: `platform-smoke-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=fa99972bb2d226bcbfd723a15c5e984feca46ba7be3b8a8e79a20681863b79f4 after=f1fa2682b5dd6d09ab27321676318b59c028b1766a1b0d90bb7622f21e214cd7 -->

<!-- course-file: apps/platform-smoke/tests/platform-smoke-types.test.ts -->

### platform-smoke-types.test.ts

[Open current source](../../../../../apps/platform-smoke/tests/platform-smoke-types.test.ts) · **Snapshot:** modified existing file; 18 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for the sample app owns its feature meaning.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): App owns app-name configuration and accepted-work-item payload predicate meanings, preserving Core reader companions. Actual server config and worker dead-letter delivery are tested default/injected/unavailable.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `legacyAcceptance`, `invocation`, `observedAcceptance`, `explicitlySelectedApp`.

New declarations within this existing file: `legacyAcceptance`, `invocation`, `observedAcceptance`, `explicitlySelectedApp`.

Added import edges: `@kanbien/platform-persistence`.

Owning registered proof: `platform-smoke-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=dc2f08594d7c5e2b7ab5914780c6b54e09ea023f46c79392d529a28a8583840f after=c6c130d7c85e5fd20d9c6602717922f874e27a2e03b8cc3b78344cd881162e79 -->

<!-- course-file: apps/platform-smoke/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../apps/platform-smoke/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreModules`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=22340e26fc3cf0d036cf2bfedbbac1c0cdd0f52022c3fcd69e87c1bef04ef324 after=201e6fbe3cc98c69518c0abbda26308cde62943b3c913b1b6041df39402f7d66 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which part of this explanation belongs to the app, and which belongs to Persistence?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** An acceptance diagnostic does not independently prove that a database commit happened. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../apps/platform-smoke/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L084 apps/platform-smoke](084-apps-platform-smoke.md) · [L085 apps/platform-smoke/contracts](085-apps-platform-smoke-contracts.md) · [L086 apps/platform-smoke/src](086-apps-platform-smoke-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 5 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
