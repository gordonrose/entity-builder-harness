<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l075
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/queue/sqs/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L075 — platform/adapters/aws/queue/sqs/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/queue/sqs/src -->

## What you will understand

The SQS adapter binds generic queue messages and workers to AWS receive, send, delete and related command behavior.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **5 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a local message shape rejection before send with send being invoked and throwing. The latter is not proof of no delivery, and raw AWS prose is not the diagnostic payload.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The queue backend already worked. Message projection, configuration, command rejection and callback failures were not uniformly exposed as finite safe facts.

**After:** Observers identify existing SQS/queue locations and supported native categories, preserving message handling order and original source evidence without exporting payloads or queue addresses.

**Why this was needed:** The agent needs to know whether a local message envelope was invalid or an actual transport command failed. Those are different owners and recovery paths.

This directory contains `implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/queue/sqs/src/errors.ts -->

### errors.ts

[Open current source](../../../../../platform/adapters/aws/queue/sqs/src/errors.ts) · **Snapshot:** modified existing file; 30 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports sqs transport evidence at this layer.

**Before:** The queue backend already worked. Message projection, configuration, command rejection and callback failures were not uniformly exposed as finite safe facts. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformSqsConfigurationIssue`, `assertSqsConfigurationText`, `PlatformSqsWorkerQueueError`, `invalidConfig`, `invalidMessage`, `operationError` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core-only SQS adapter configuration guards attach fixed typed facts without upward Platform dependencies. Environment and direct producer/worker constructors preserve Number coercion, predicate counts, original text quirks, RangeError/native TypeError and first failure.

**Why:** The agent needs to know whether a local message envelope was invalid or an actual transport command failed. Those are different owners and recovery paths.

Changed declaration anchors: `PlatformSqsConfigurationIssue`, `assertSqsConfigurationText`, `PlatformSqsWorkerQueueError`, `invalidConfig`, `invalidMessage`, `operationError`.

New declarations within this existing file: `PlatformSqsConfigurationIssue`, `assertSqsConfigurationText`.

Added import edges: `@kanbien/core`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`, `sqs-queue-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=45f617446c2f1a90dba9c383150e260a4cdba12a6d04ce4f269c70f8e649530a after=3a3fbc0c1ec1464eb29812be67041a5d5c8e4533dbc7340e36d83d3be2409e0d -->

<!-- course-file: platform/adapters/aws/queue/sqs/src/messages.ts -->

### messages.ts

[Open current source](../../../../../platform/adapters/aws/queue/sqs/src/messages.ts) · **Snapshot:** modified existing file; 55 added / 18 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports sqs transport evidence at this layer.

**Before:** The queue backend already worked. Message projection, configuration, command rejection and callback failures were not uniformly exposed as finite safe facts. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `decodePlatformQueueMessage`, `parseTraceParent` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): SQS reports actual client selection/construction, command encoding/invocation, response projection, decode predicates and receive reductions with unchanged SDK command/receiver/getter counts and legacy error/result identities. Own location and selected selected source primary plus eight related records are independent.

**Why:** The agent needs to know whether a local message envelope was invalid or an actual transport command failed. Those are different owners and recovery paths.

Changed declaration anchors: `decodePlatformQueueMessage`, `parseTraceParent`.

Added import edges: `./observations`.

Owning registered proof: `sqs-queue-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=8645347637b95930e858fea1fa4afb0543f63055002c49b85791a90b11e8f3c5 after=faf54888473ed3a21306849973b147cb060c366ce5e7de093ef57e6e8d140d90 -->

<!-- course-file: platform/adapters/aws/queue/sqs/src/observations.ts -->

### observations.ts

[Open current source](../../../../../platform/adapters/aws/queue/sqs/src/observations.ts) · **Snapshot:** added (absent from baseline); 103 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** SQS reports actual client selection/construction, command encoding/invocation, response projection, decode predicates and receive reductions with unchanged SDK command/receiver/getter counts and legacy error/result identities. Own location and selected selected source primary plus eight related records are independent. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `Native`, `allSdkOperations`, `keyOperations`, `modeledNativeNames`, `nativeObservation`, `sqsObservation`, `SqsObservation`, `receiveReductions`, `ReceiveReductions`.

Added import edges: `@kanbien/core`, `./worker`.

Owning registered proof: `sqs-queue-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=ac3e768f3c69c227039b91de9f5818436754c868c628e5f581cd054e5df48b82 -->

<!-- course-file: platform/adapters/aws/queue/sqs/src/queue.ts -->

### queue.ts

[Open current source](../../../../../platform/adapters/aws/queue/sqs/src/queue.ts) · **Snapshot:** modified existing file; 22 added / 14 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports sqs transport evidence at this layer.

**Before:** The queue backend already worked. Message projection, configuration, command rejection and callback failures were not uniformly exposed as finite safe facts. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformSqsQueueOptions`, `AwsSdkPlatformSqsQueueOptions`, `createPlatformSqsQueue`, `createAwsSdkPlatformSqsQueue`, `validDelay` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core-only SQS adapter configuration guards attach fixed typed facts without upward Platform dependencies. Environment and direct producer/worker constructors preserve Number coercion, predicate counts, original text quirks, RangeError/native TypeError and first failure.

**Why:** The agent needs to know whether a local message envelope was invalid or an actual transport command failed. Those are different owners and recovery paths.

Changed declaration anchors: `PlatformSqsQueueOptions`, `AwsSdkPlatformSqsQueueOptions`, `createPlatformSqsQueue`, `createAwsSdkPlatformSqsQueue`, `validDelay`.

Added import edges: `./errors`, `./observations`.

Declarations removed or relocated: `assertNonEmpty`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`, `sqs-queue-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=2a05d514ada2181e199d1fba87f3c921b4cf336d3baad8642c8d1a5ed062dada after=c263565d507330a11f0aeb2e4395bd3e51867bfa48ae7dfb5d27d93246c06002 -->

<!-- course-file: platform/adapters/aws/queue/sqs/src/worker.ts -->

### worker.ts

[Open current source](../../../../../platform/adapters/aws/queue/sqs/src/worker.ts) · **Snapshot:** modified existing file; 79 added / 46 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports sqs transport evidence at this layer.

**Before:** The queue backend already worked. Message projection, configuration, command rejection and callback failures were not uniformly exposed as finite safe facts. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformSqsWorkerQueueOptions`, `AwsSdkPlatformSqsWorkerQueueOptions`, `createPlatformSqsWorkerQueue`, `createAwsSdkPlatformSqsWorkerQueue`, `createAwsSdkPlatformSqsWorkerQueueFromEnv`, `firstSqsMessage`, `requiredString` (5 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Core-only SQS adapter configuration guards attach fixed typed facts without upward Platform dependencies. Environment and direct producer/worker constructors preserve Number coercion, predicate counts, original text quirks, RangeError/native TypeError and first failure.

**Why:** The agent needs to know whether a local message envelope was invalid or an actual transport command failed. Those are different owners and recovery paths.

Changed declaration anchors: `PlatformSqsWorkerQueueOptions`, `AwsSdkPlatformSqsWorkerQueueOptions`, `createPlatformSqsWorkerQueue`, `createAwsSdkPlatformSqsWorkerQueue`, `createAwsSdkPlatformSqsWorkerQueueFromEnv`, `firstSqsMessage`, `requiredString`, `boundedInteger`, `parseReceiveCount`, `projectedString`, `assertNonEmpty`, `assertWholeNumberInRange`.

New declarations within this existing file: `projectedString`.

Added import edges: `./observations`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`, `sqs-queue-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=7d8cd194a5d88c44ac7239275fb95e176d47f5379036f309f117ca420503e48b after=5161a9a496c31b51bf438b51424dd3939d1b0e3cbe54d0705081d2e7ee4a6744 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why must queue URL and message body stay out of a shared diagnostic even when they would help a human recognize the request?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Existing receive/delete/retry semantics and source queue identities remain private and unchanged. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/queue/sqs/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L074 platform/adapters/aws/queue/sqs](074-aws-queue-sqs.md) · [L076 platform/adapters/aws/queue/sqs/tests](076-queue-sqs-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 5 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
