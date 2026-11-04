<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l142
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L142 — scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal -->

## What you will understand

Controllers orchestrate existing deployment and verification steps; readers interpret the receipts and task output on which later decisions rely.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A verifier task fails; its safe existing log record identifies the operation. The controller may retain that checked record, but a failed or partial log read cannot turn failure into success. A remote side effect remains uncertain unless separate evidence proves it.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Existing controllers and receipts could discard task detail, pass through uncontrolled text, or conflate observation failure with absence or successful progress.

**After:** Readers validate selected generated contracts and preserve primary failure plus bounded source observations. The failed-verifier path permits one bounded read of the failed task's existing stream after exact identity validation; successful verification remains unchanged.

**Why this was needed:** A precise producer record is useless if the controller drops it. An invalid or incomplete receipt must also not authorize acceptance or a repeated mutation.

This directory contains `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal/smoke-test.py -->

### smoke-test.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal/smoke-test.py) · **Snapshot:** modified existing file; 2 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for deployment controllers and evidence readers.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Current reading anchors (not all are new): `load`, `passed`, `cli`, `capture`, `custody`, `hashes`, `route_tests`, `check_mutation`, `text`, `missing_mode` (6 more in source).

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=7f84531ea475fa4c7787d8e730c805e0055821e0c71a2a09a1b6463263c6d1cf after=9bc7a4a679bb8f0415a8716b4c864d8c44ba11053ceb12e5e0a171d5a698364e -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must failure to read a failed task's log not replace the original verification failure?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local reader/controller fixtures do not prove live stream identity, rollout success or rollback compatibility; live checks belong to a separate chat. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L141 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence](141-targets-kanbien-core-platform-core-server-persistence.md) · [L143 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence](143-kanbien-core-platform-core-server-persistence-collect-acceptance-evidence.md) · [L144 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore](144-kanbien-core-platform-core-server-persistence-rehearse-isolated-database-restore.md) · [L145 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness](145-kanbien-core-platform-core-server-persistence-rehearse-observability-readiness.md) · [L146 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle](146-kanbien-core-platform-core-server-persistence-rehearse-runtime-credential-lifecycle.md) · [L147 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement](147-kanbien-core-platform-core-server-persistence-rehearse-server-replacement.md) · [L148 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration](148-kanbien-core-platform-core-server-persistence-run-administration.md) · [L149 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration](149-kanbien-core-platform-core-server-persistence-run-migration.md) · [L150 scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate](150-kanbien-core-platform-core-server-persistence-verify-candidate.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
