<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l078
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/observability/contracts.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L078 — platform/observability/contracts

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/observability/contracts -->

## What you will understand

Platform observability wraps logging, metrics, traces and readiness observation; it does not itself choose every provider or backend.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A metric recording throws and the optional diagnostic sink also rejects. Preserve the workload result and avoid recursive reporting. The bounded binding records attempts, not guaranteed delivery; suppression must not be called full coverage.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The observability slice already implemented telemetry. Several best-effort failures were swallowed or coarsely normalized, so lack of telemetry could be hard to explain.

**After:** Owned records distinguish configuration, preparation, validation, creation, recording, collection, export, flush/shutdown and wrapper failures. Bounded reporting stays independent of the failed telemetry operation.

**Why this was needed:** An agent must tell a rejected metric from a recording invocation, collection issue or exporter failure. None of those alone prove what the backend retained.

This directory contains `catalog` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/observability/contracts/diagnostics.v1.json -->

### diagnostics.v1.json

[Open current source](../../../../../platform/observability/contracts/diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 927 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected diagnostics for telemetry itself contract for non-TypeScript readers, including 18 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `observability.configuration-invalid` v1, `observability.runtime-construction-failed` v1, `observability.metric-preparation-failed` v1, `observability.metric-rejected` v1, `observability.metric-instrument-creation-failed` v1; 13 more definitions are in the export.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=481a99d57cfd1721155439fed7a56256ee3cf2e904f9b2e02acabbea2237d994 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why would sending a logger-failed diagnostic through the same failed logger recursively be dangerous?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No SDK or metrics backend is introduced here. SDK-internal failures that never cross observable public boundaries cannot be invented as observed facts. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/observability/contracts) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L077 platform/observability](077-platform-observability.md) · [L079 platform/observability/src](079-platform-observability-src.md) · [L080 platform/observability/tests](080-platform-observability-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
