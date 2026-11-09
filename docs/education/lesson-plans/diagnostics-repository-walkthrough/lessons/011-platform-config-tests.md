<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l011
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-09"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/config/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L011 — platform/config/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/config/tests -->

## What you will understand

Configuration code turns supplied settings into values the workload can use. A setting is a logical requirement; its environment-variable name belongs to the caller that binds it.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **4 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Start with the original combined host/database/schema/reference/port guard. If port is absent and host is present, the useful observation is the port requirement being missing—not a guessed connection failure. If reading the source throws before a value is obtained, wrong-type would be an unsupported claim.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Existing readers rejected missing or malformed values, but several callers collapsed alternatives into undefined or one broad configuration error.

**After:** Reusable readers retain safe setting references, exact observed reasons, source-read failures, indexed issues and explicitly declared relationships. Target bindings supply exact source names privately, without placing submitted values in diagnostic detail.

**Why this was needed:** An agent needs to know which requirement failed and whether to fix a declaration, provide a setting, or investigate an unreadable source. One broad rejection cannot support that decision.

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/config/tests/integration/evidence-runtime.test.ts -->

### evidence-runtime.test.ts

[Open current source](../../../../../platform/config/tests/integration/evidence-runtime.test.ts) · **Snapshot:** added (absent from baseline); 68 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for configuration: tell absence from invalidity.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Schema rejection reports its position independently from explicitly selected Core/app primary and eight companions. Parse/projection throws report the actual boundary then rethrow the same value; optional callback throws/rejections cannot alter outcomes.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `selected`, `checked`, `record`, `issue`, `failure`, `calls`, `schema`, `observed`, `input`, `result`, `unselected`, `reads` (5 more in source).

Added import edges: `node:assert/strict`, `@kanbien/core/config`, `@kanbien/core/diagnostics`, `@kanbien/core/validation`, `../src/index`.

Owning registered proof: `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=3e64d578f816fe60799805237a3cae0dc935d81d51e1687e055c191d6c0c4ad6 -->

<!-- course-file: platform/config/tests/integration/platform-config-runtime.test.ts -->

### platform-config-runtime.test.ts

[Open current source](../../../../../platform/config/tests/integration/platform-config-runtime.test.ts) · **Snapshot:** modified existing file; 99 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for configuration: tell absence from invalidity.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Schema rejection reports its position independently from explicitly selected Core/app primary and eight companions. Parse/projection throws report the actual boundary then rethrow the same value; optional callback throws/rejections cannot alter outcomes.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `sourceDiagnostic`, `relation`, `relationshipDefinitions`, `fieldIssues`, `evidenceAccessorReads`, `sensitiveGetter`, `validEvidence`, `rejectEvidence`.

New declarations within this existing file: `sourceDiagnostic`, `relation`, `relationshipDefinitions`, `fieldIssues`, `evidenceAccessorReads`, `sensitiveGetter`, `validEvidence`, `rejectEvidence`.

Added import edges: `../src/diagnostics`, `@kanbien/core/diagnostics`.

Owning registered proof: `core-runtime`, `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=c0324fed695223bd1028f7d1e5fefc317a666c66063e516d6131024d05ced0ab after=d35cf87fcf1310e9703f507646530c5f5fb78bb6d62a14f4874666ad52e2d229 -->

<!-- course-file: platform/config/tests/type-level/platform-config-types.test.ts -->

### platform-config-types.test.ts

[Open current source](../../../../../platform/config/tests/type-level/platform-config-types.test.ts) · **Snapshot:** modified existing file; 17 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for configuration: tell absence from invalidity.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Schema rejection reports its position independently from explicitly selected Core/app primary and eight companions. Parse/projection throws report the actual boundary then rethrow the same value; optional callback throws/rejections cannot alter outcomes.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `relation`, `definitions`, `record`.

New declarations within this existing file: `relation`, `definitions`, `record`.

Owning registered proof: `platform-config-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=1075680e1c6e121b8edee27c8cd40e9e4e289513cf8c26bc56e84a379ff12cbf after=bb262c896491db6dc3fb554287fab2a4ec1e1d0a8e7523f7edb79139a3dff343 -->

<!-- course-file: platform/config/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../platform/config/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreModules`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=3d3b9312a274665aeacecea27c916d9b30ef8ba6f479270a8942c0b8af5b6675 after=6a6c3dfd7478af494f652336c2e9e6225fe8371b7419a0b800a9fb7d955fb16f -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which fact distinguishes a missing setting from a getter that threw before the setting could be read?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Do not expose hostnames, usernames, passwords, source contents or rejected values. The issue collector has a bound; overflow must not be called complete. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/config/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L008 platform/config](008-platform-config.md) · [L009 platform/config/contracts](009-platform-config-contracts.md) · [L010 platform/config/src](010-platform-config-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 4 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
