<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l061
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/persistence/src/observability.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L061 — platform/persistence/src/observability

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/persistence/src/observability -->

## What you will understand

Persistence covers records, transactions, outbox messages, processing claims and lineage. An outbox holds work alongside a business change so it can be delivered later.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **3 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A write throws and a reconciliation read follows under existing policy. Report each observed step separately. A failed reconciliation cannot establish that the write did not happen, and diagnostic reporting must not introduce another write.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions.

**After:** Core owns primitive/storage-independent meanings; Platform owns orchestration meanings. Adapters add actual provider evidence. Local rejection, boundary failure, conditional conflict, stored shape and reconciliation remain distinct.

**Why this was needed:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

This directory contains `documentation`, `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/persistence/src/observability/README.md -->

### README.md

[Open current source](../../../../../platform/persistence/src/observability/README.md) · **Snapshot:** modified existing file; 18 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for persistence meaning and coordination; read the sections `Persistence Observability Source Map`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Persistence Observability Source Map`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=a8e71a6944f0f57f641617f5d5d35f0969502cbbe2560f5e6cb2b09d02e41854 after=4300399901d6c27989c8c9d057d03299eb139aa0a7977a6bc30a3f39b79b5f34 -->

<!-- course-file: platform/persistence/src/observability/integration.ts -->

### integration.ts

[Open current source](../../../../../platform/persistence/src/observability/integration.ts) · **Snapshot:** modified existing file; 102 added / 6 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformPersistenceTransitionObserverOptions`, `platformPersistenceTransitionProfile`, `createPlatformPersistenceTransitionObserver`, `canonicalCatalog`, `persistenceNomenclature` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `PlatformPersistenceTransitionObserverOptions`, `platformPersistenceTransitionProfile`, `createPlatformPersistenceTransitionObserver`, `canonicalCatalog`, `persistenceNomenclature`.

New declarations within this existing file: `canonicalCatalog`.

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `../diagnostics`, `../errors`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=edb05fa3604eb92bff857383a3903237a2a14f465daec2eb6cc7b19242e8d47c after=99ccab8803e0737eddbd0012b741e2861c9bfce8bb8c99a1dcc76527f86b74bb -->

<!-- course-file: platform/persistence/src/observability/port.ts -->

### port.ts

[Open current source](../../../../../platform/persistence/src/observability/port.ts) · **Snapshot:** modified existing file; 12 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformPersistenceObservation`, `PlatformPersistenceObserver`, `recordPlatformPersistenceObservation`, `intrinsicPromiseThen` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `PlatformPersistenceObservation`, `PlatformPersistenceObserver`, `recordPlatformPersistenceObservation`, `intrinsicPromiseThen`.

New declarations within this existing file: `intrinsicPromiseThen`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=9c34bb5a93dec3930163647a28aca640d2a2c66d2fa9f3dd9ed899926ebdf7e3 after=0acdc8983d0988c0509395a6836e86094928a73f6f6252e24e2159c8b7c40e63 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which evidence would establish write-not-reached, and which merely establishes that the invocation did not return?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No new transaction, SQL, privilege, retry or delivery guarantee is authorized by adding diagnostics. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/persistence/src/observability) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L060 platform/persistence/src](060-platform-persistence-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 3 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
