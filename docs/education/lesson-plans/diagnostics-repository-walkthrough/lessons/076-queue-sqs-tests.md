<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l076
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-09"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/queue/sqs/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L076 — platform/adapters/aws/queue/sqs/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/queue/sqs/tests -->

## What you will understand

The SQS adapter binds generic queue messages and workers to AWS receive, send, delete and related command behavior.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a local message shape rejection before send with send being invoked and throwing. The latter is not proof of no delivery, and raw AWS prose is not the diagnostic payload.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The queue backend already worked. Message projection, configuration, command rejection and callback failures were not uniformly exposed as finite safe facts.

**After:** Observers identify existing SQS/queue locations and supported native categories, preserving message handling order and original source evidence without exporting payloads or queue addresses.

**Why this was needed:** The agent needs to know whether a local message envelope was invalid or an actual transport command failed. Those are different owners and recovery paths.

This directory contains `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/queue/sqs/tests/contract/sqs-adapter-runtime.test.ts -->

### sqs-adapter-runtime.test.ts

[Open current source](../../../../../platform/adapters/aws/queue/sqs/tests/contract/sqs-adapter-runtime.test.ts) · **Snapshot:** modified existing file; 201 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for sqs transport evidence.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): SQS reports actual client selection/construction, command encoding/invocation, response projection, decode predicates and receive reductions with unchanged SDK command/receiver/getter counts and legacy error/result identities. Own location and selected selected source primary plus eight related records are independent.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `../src/messages`, `../src/observations`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`, `sqs-queue-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=563c7eb1e4b9716838c6efa446fa3ab4e3e04f907b48b812ab3f127612af9acc after=1637677e74f4cb8f35f35e686c1fa49833e041628c8c1538ef13c3ff15b88698 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must queue URL and message body stay out of a shared diagnostic even when they would help a human recognize the request?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Existing receive/delete/retry semantics and source queue identities remain private and unchanged. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/queue/sqs/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L074 platform/adapters/aws/queue/sqs](074-aws-queue-sqs.md) · [L075 platform/adapters/aws/queue/sqs/src](075-queue-sqs-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
