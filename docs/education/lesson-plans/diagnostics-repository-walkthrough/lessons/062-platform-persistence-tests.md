<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l062
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-09"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/persistence/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L062 — platform/persistence/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/persistence/tests -->

## What you will understand

Persistence covers records, transactions, outbox messages, processing claims and lineage. An outbox holds work alongside a business change so it can be delivered later.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **4 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A write throws and a reconciliation read follows under existing policy. Report each observed step separately. A failed reconciliation cannot establish that the write did not happen, and diagnostic reporting must not introduce another write.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions.

**After:** Core owns primitive/storage-independent meanings; Platform owns orchestration meanings. Adapters add actual provider evidence. Local rejection, boundary failure, conditional conflict, stored shape and reconciliation remain distinct.

**Why this was needed:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

This directory contains `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/persistence/tests/integration/platform-persistence-observability-runtime.test.ts -->

### platform-persistence-observability-runtime.test.ts

[Open current source](../../../../../platform/persistence/tests/integration/platform-persistence-observability-runtime.test.ts) · **Snapshot:** modified existing file; 258 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for persistence meaning and coordination.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Four additive code-owned definitions distinguish current Core preparation predicates and precise raw-access locations, trusted same-port adapter rejections, creation not-attempted and invocation unknown effect. Independent bindings preserve helper void/API compatibility and bounded opt-out-aware reporting.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `@kanbien/core/persistence`, `@kanbien/core/diagnostics`, `@kanbien/platform-observability`, `../../contracts/src/observability-profiles`.

Owning registered proof: `platform-observability-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-persistence-runtime`, `cloudwatch-observability-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=d1d7caa8d4d1905ab6e3cbf2b4fbce15c4cd590c4bae4c479efefda100270b6e after=deb7caaf508650b6d9b1100fb8271f68fd1260f97cffdf2cbd58e78e565b8420 -->

<!-- course-file: platform/persistence/tests/type-level/platform-persistence-observability-types.test.ts -->

### platform-persistence-observability-types.test.ts

[Open current source](../../../../../platform/persistence/tests/type-level/platform-persistence-observability-types.test.ts) · **Snapshot:** modified existing file; 6 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for persistence meaning and coordination.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=74e9697ea6ef75edee12ecb76f708af8d704f5a852ef0622dcc24483f1c0f1c7 after=9ac46a3652b928bc265878da47989350abff813cb4dc5a284ddde42a1f070727 -->

<!-- course-file: platform/persistence/tests/integration/platform-persistence-runtime.test.ts -->

### platform-persistence-runtime.test.ts

[Open current source](../../../../../platform/persistence/tests/integration/platform-persistence-runtime.test.ts) · **Snapshot:** modified existing file; 410 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for persistence meaning and coordination.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `relayDiagnosticProof`.

New declarations within this existing file: `relayDiagnosticProof`.

Added import edges: `@kanbien/core/tenancy`, `@kanbien/core/diagnostics`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=2e7352906e6374f56bc7cfd2dc16533e06b489133238866a168b0f4865e192c5 after=3659d39193577d62bcd7a46de45f77d992720e9af7a01ccf74d678e0bc3a0d93 -->

<!-- course-file: platform/persistence/tests/type-level/platform-persistence-types.test.ts -->

### platform-persistence-types.test.ts

[Open current source](../../../../../platform/persistence/tests/type-level/platform-persistence-types.test.ts) · **Snapshot:** modified existing file; 25 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Compile-time compatibility proof for persistence meaning and coordination.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `compatibleWriter`.

New declarations within this existing file: `compatibleWriter`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=5b02a1df9f0d79b8d78d7b5af6397eddee131c307490b64cec476e98239ead9b after=a51f9b28d725b1c848efeb6a90705b68988d6a34298da00d1428c8879eac080e -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which evidence would establish write-not-reached, and which merely establishes that the invocation did not return?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No new transaction, SQL, privilege, retry or delivery guarantee is authorized by adding diagnostics. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/persistence/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L058 platform/persistence](058-platform-persistence.md) · [L059 platform/persistence/contracts](059-platform-persistence-contracts.md) · [L060 platform/persistence/src](060-platform-persistence-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 4 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
