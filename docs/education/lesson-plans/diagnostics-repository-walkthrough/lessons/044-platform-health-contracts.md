<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l044
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/health/contracts.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L044 — platform/health/contracts

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/health/contracts -->

## What you will understand

Health checks tell the workload and its callers whether dependencies and lifecycle state are ready. Public detail is a separate disclosure contract.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A check returns unhealthy with a message containing a private connection string. The public response retains status and a fixed summary, not that string; internal selected facts identify the check boundary without copying it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Health checks already ran, but public messages and metadata could contain arbitrary strings; internal failures could lose exact safe source evidence.

**After:** Internal records separate returned not-ready results, throws, rejections, projection problems and lifecycle state. Public messages use fixed summaries and explicitly allowed metadata values.

**Why this was needed:** Redacting keys is insufficient if an otherwise harmless message string contains a secret. A safe internal diagnostic should be detailed while the public endpoint stays deliberately limited.

This directory contains `catalog` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/health/contracts/diagnostics.v1.json -->

### diagnostics.v1.json

[Open current source](../../../../../platform/health/contracts/diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 184 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected health: public status and private evidence contract for non-TypeScript readers, including 5 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `health.check-not-ready` v1, `health.check-threw` v1, `health.check-rejected` v1, `health.check-projection-failed` v1, `health.lifecycle-not-ready` v1.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=6e742fd0106595ee85fd8fd3a2bd6ae6f52c6c5641d38b192f9a83331329550e -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why is replacing arbitrary public prose an intentional compatibility decision, rather than a transparent refactor?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Healthy local checks do not establish live deployment acceptance or prove remote log delivery. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/health/contracts) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L043 platform/health](043-platform-health.md) · [L045 platform/health/src](045-platform-health-src.md) · [L046 platform/health/tests](046-platform-health-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
