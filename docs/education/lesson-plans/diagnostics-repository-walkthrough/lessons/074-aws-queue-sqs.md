<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l074
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/queue/sqs.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L074 — platform/adapters/aws/queue/sqs

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/queue/sqs -->

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

This directory contains `documentation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/queue/sqs/README.md -->

### README.md

[Open current source](../../../../../platform/adapters/aws/queue/sqs/README.md) · **Snapshot:** modified existing file; 28 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for sqs transport evidence; read the sections `AWS SQS Queue Adapter`, `What happens when an outbox item is sent`, `Deliberate boundaries`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `AWS SQS Queue Adapter`; `What happens when an outbox item is sent`; `Deliberate boundaries`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=b66544d98cb842630662cbe850fdad99811ddb1466c0f109eaf5fa2dc12cc048 after=aabbbf2e17303d7703376e798f4061d63697128720b1c5b8b053960aa6518684 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must queue URL and message body stay out of a shared diagnostic even when they would help a human recognize the request?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Existing receive/delete/retry semantics and source queue identities remain private and unchanged. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/queue/sqs) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L075 platform/adapters/aws/queue/sqs/src](075-queue-sqs-src.md) · [L076 platform/adapters/aws/queue/sqs/tests](076-queue-sqs-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
