<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l059
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/persistence/contracts.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L059 — platform/persistence/contracts

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/persistence/contracts -->

## What you will understand

Persistence covers records, transactions, outbox messages, processing claims and lineage. An outbox holds work alongside a business change so it can be delivered later.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A write throws and a reconciliation read follows under existing policy. Report each observed step separately. A failed reconciliation cannot establish that the write did not happen, and diagnostic reporting must not introduce another write.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions.

**After:** Core owns primitive/storage-independent meanings; Platform owns orchestration meanings. Adapters add actual provider evidence. Local rejection, boundary failure, conditional conflict, stored shape and reconciliation remain distinct.

**Why this was needed:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

This directory contains `catalog` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/persistence/contracts/diagnostics.v1.json -->

### diagnostics.v1.json

[Open current source](../../../../../platform/persistence/contracts/diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 3943 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected persistence meaning and coordination contract for non-TypeScript readers, including 41 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `persistence.transport-unavailable` v1, `persistence.trust-validation-failed` v1, `persistence.credential-rejected` v1, `persistence.runtime-permission-denied` v1, `persistence.capacity-exhausted` v1; 36 more definitions are in the export.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=97e421823361e7bbb1ae355e2c402f2044980d446e9e215e578ff29612a97db4 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which evidence would establish write-not-reached, and which merely establishes that the invocation did not return?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No new transaction, SQL, privilege, retry or delivery guarantee is authorized by adding diagnostics. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/persistence/contracts) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L058 platform/persistence](058-platform-persistence.md) · [L060 platform/persistence/src](060-platform-persistence-src.md) · [L062 platform/persistence/tests](062-platform-persistence-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
