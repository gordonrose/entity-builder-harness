<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l043
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/health.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L043 — platform/health

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/health -->

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

This directory contains `documentation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/health/README.md -->

### README.md

[Open current source](../../../../../platform/health/README.md) · **Snapshot:** added (absent from baseline); 42 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** This dedicated document was absent at the baseline.

**After:** Explains the diagnostic responsibilities and compatibility limits for health: public status and private evidence; read the sections `Platform Health`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform Health`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=absent after=f073c8520b20bda9b3f5b606c1b9508af72830ea42a90d3a4c0c1ef9680bb2a2 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why is replacing arbitrary public prose an intentional compatibility decision, rather than a transparent refactor?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Healthy local checks do not establish live deployment acceptance or prove remote log delivery. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/health) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L008 platform/config](008-platform-config.md) · [L023 platform/contracts](023-platform-contracts.md) · [L030 platform/runtime](030-platform-runtime.md) · [L034 platform/testing](034-platform-testing.md) · [L037 platform/server](037-platform-server.md) · [L044 platform/health/contracts](044-platform-health-contracts.md) · [L045 platform/health/src](045-platform-health-src.md) · [L046 platform/health/tests](046-platform-health-tests.md) · [L053 platform/security](053-platform-security.md) · [L058 platform/persistence](058-platform-persistence.md) · [L070 platform/workers](070-platform-workers.md) · [L077 platform/observability](077-platform-observability.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
