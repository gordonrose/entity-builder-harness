<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l077
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/observability.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L077 — platform/observability

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/observability -->

## What you will understand

Platform observability wraps logging, metrics, traces and readiness observation; it does not itself choose every provider or backend.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A metric recording throws and the optional diagnostic sink also rejects. Preserve the workload result and avoid recursive reporting. The bounded binding records attempts, not guaranteed delivery; suppression must not be called full coverage.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The observability slice already implemented telemetry. Several best-effort failures were swallowed or coarsely normalized, so lack of telemetry could be hard to explain.

**After:** Owned records distinguish configuration, preparation, validation, creation, recording, collection, export, flush/shutdown and wrapper failures. Bounded reporting stays independent of the failed telemetry operation.

**Why this was needed:** An agent must tell a rejected metric from a recording invocation, collection issue or exporter failure. None of those alone prove what the backend retained.

This directory contains `documentation`, `compiler` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/observability/README.md -->

### README.md

[Open current source](../../../../../platform/observability/README.md) · **Snapshot:** modified existing file; 116 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for diagnostics for telemetry itself; read the sections `Platform Observability`, `Boundary`, `Responsibility map`, `Configuration diagnostics`, `Readiness diagnostics`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform Observability`; `Boundary`; `Responsibility map`; `Configuration diagnostics`; `Readiness diagnostics`; `Metric lifecycle diagnostics`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=82b25b73df981d286074ad4e2dea6db51e84733372a6a7d819fafc0e63ed4870 after=ec5341c11675a68245c4871a49a940a52eac248fa278f44672dd9a878ac48cb4 -->

<!-- course-file: platform/observability/tsconfig.runtime-test.json -->

### tsconfig.runtime-test.json

[Open current source](../../../../../platform/observability/tsconfig.runtime-test.json) · **Snapshot:** modified existing file; 4 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Configures which sources/dependencies the test compiler can resolve.

**Before:** The existing compiler scope did not include all newly referenced diagnostic/security dependencies.

**After:** Extends the relevant compilation inputs or aliases for the tests; the JSON diff is the exact declaration change.

**Why:** Runtime tests must exercise the implementation that consumers actually import, rather than fail resolution or omit the new modules.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=def0379ff1aef1deabd60d06089db668e78c73ef657365354bf257b0dabd9a0b after=2a15208c65390ef08ef80b697ae88093703202dcb8a926ae26cd6afe80b6ce8d -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why would sending a logger-failed diagnostic through the same failed logger recursively be dangerous?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No SDK or metrics backend is introduced here. SDK-internal failures that never cross observable public boundaries cannot be invented as observed facts. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/observability) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L008 platform/config](008-platform-config.md) · [L023 platform/contracts](023-platform-contracts.md) · [L030 platform/runtime](030-platform-runtime.md) · [L034 platform/testing](034-platform-testing.md) · [L037 platform/server](037-platform-server.md) · [L043 platform/health](043-platform-health.md) · [L053 platform/security](053-platform-security.md) · [L058 platform/persistence](058-platform-persistence.md) · [L070 platform/workers](070-platform-workers.md) · [L078 platform/observability/contracts](078-platform-observability-contracts.md) · [L079 platform/observability/src](079-platform-observability-src.md) · [L080 platform/observability/tests](080-platform-observability-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
