<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l060
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/persistence/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L060 — platform/persistence/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/persistence/src -->

## What you will understand

Persistence covers records, transactions, outbox messages, processing claims and lineage. An outbox holds work alongside a business change so it can be delivered later.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **9 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A write throws and a reconciliation read follows under existing policy. Report each observed step separately. A failed reconciliation cannot establish that the write did not happen, and diagnostic reporting must not introduce another write.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions.

**After:** Core owns primitive/storage-independent meanings; Platform owns orchestration meanings. Adapters add actual provider evidence. Local rejection, boundary failure, conditional conflict, stored shape and reconciliation remain distinct.

**Why this was needed:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

This directory contains `definition`, `implementation`, `barrel-or-implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/persistence/src/diagnostics.ts -->

### diagnostics.ts

[Open current source](../../../../../platform/persistence/src/diagnostics.ts) · **Snapshot:** added (absent from baseline); 290 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns the capability's versioned diagnostic meanings and construction helpers.

**Before:** This dedicated definitions module was absent; the capability and some older error codes already existed.

**After:** Defines `persistence.configuration-invalid`, `persistence.local-rejected`, `persistence.stored-record-observed`, `persistence.boundary-observed`, `persistence.reconciliation-observed`, `persistence.command-condition-observed`, `persistence.stored-attribute-observed`, `persistence.relay-boundary-observed`. Detail must fit the declared finite schema; the changed symbols below are the entry points.

**Why:** Meaning belongs to the capability that understands the predicate, not to a downstream logger, AWS adapter or harness prose.

Changed declaration anchors: `persistenceDiagnosticCodes`, `persistenceObservedPhases`, `persistenceFailureClassifications`, `historicalPersistenceOperations`, `persistenceOperations`, `kinds`, `historicalDetail`, `persistenceDiagnosticDefinitions`, `persistenceCurrentDiagnosticDefinitions`, `persistenceConfigurationDiagnostic`, `persistenceConfigurationDiagnosticRecord`, `persistenceLocalRejectionDiagnostic` (40 more in source).

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`.

Owning registered proof: `persistence-composition`, `restore-connection-diagnostics`, `platform-shell-payload`, `deployment-operation-diagnostics-regression`, `diagnostic-catalog-readers`, `postgresql-connection-diagnostics`, `platform-observability-runtime`, `platform-persistence-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `platform-health-runtime`, `platform-smoke-runtime`, `shell-package-source`, `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=b92176a8437ec16ed0a3226b5ba0fb8dc065349524d194d9b9c6fffe45f290ad -->

<!-- course-file: platform/persistence/src/errors.ts -->

### errors.ts

[Open current source](../../../../../platform/persistence/src/errors.ts) · **Snapshot:** modified existing file; 19 added / 14 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `platformPersistenceErrorClasses`, `PlatformPersistenceErrorCode`, `platformPersistenceError` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `platformPersistenceErrorClasses`, `PlatformPersistenceErrorCode`, `platformPersistenceError`.

New declarations within this existing file: `platformPersistenceErrorClasses`.

Added import edges: `@kanbien/core/diagnostics`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=952b0f5be7c914cfe8ddccedb8eef67c36b1afcf2800e0c411da807b8e98893c after=32d26a7fbcb8d35792fd0f8c57da9ba515c5b6625fb7d74508a915d3aeaa4de3 -->

<!-- course-file: platform/persistence/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/persistence/src/index.ts) · **Snapshot:** modified existing file; 16 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./diagnostics`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=77052907ce39122466abcd7abffe7b7e4f89b7e8827765b6189522c146389fd3 after=b72f477f87376d92660e2ef55c9b90fa567f922df4fecd2b0ef1374d6899695c -->

<!-- course-file: platform/persistence/src/lineage.ts -->

### lineage.ts

[Open current source](../../../../../platform/persistence/src/lineage.ts) · **Snapshot:** modified existing file; 5 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `createInMemoryPlatformRecordChangeStore` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `createInMemoryPlatformRecordChangeStore`.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=00bbcb2404717b2c394a742f9e3026bb79f39def7049c0ce908cd269585c7377 after=4e1d8891257ebaecedbb91f446661baad93d291e48294a4c79458f218ffda2ee -->

<!-- course-file: platform/persistence/src/outbox.ts -->

### outbox.ts

[Open current source](../../../../../platform/persistence/src/outbox.ts) · **Snapshot:** modified existing file; 28 added / 10 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `createInMemoryPlatformOutboxStore`, `failure` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `createInMemoryPlatformOutboxStore`, `failure`.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ebe17d3a1f748a0e718ad7e28587ebf58fbee4337d4b5bff8d659ee2f86fcc1c after=299ccb0c19290c31981cfc44d82ab95246af6cc57503518ecbbf101586adbb6a -->

<!-- course-file: platform/persistence/src/processing.ts -->

### processing.ts

[Open current source](../../../../../platform/persistence/src/processing.ts) · **Snapshot:** modified existing file; 27 added / 9 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `createInMemoryPlatformProcessingStore`, `failure` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `createInMemoryPlatformProcessingStore`, `failure`.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=d95320dbfff57ca1d648a3d10ad832c2d0ab815d878c089eb2efa377dd4b53bb after=6abf139a42fd175d8309086eff118483a3c8adcce91b2bf1666a1bfd26c5ca95 -->

<!-- course-file: platform/persistence/src/relay.ts -->

### relay.ts

[Open current source](../../../../../platform/persistence/src/relay.ts) · **Snapshot:** modified existing file; 90 added / 12 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformOutboxRelayOptions`, `createPlatformOutboxRelay`, `recordRelayObservation`, `platformOutboxQueueMessage`, `relayBoundaryRecord`, `relayDiagnostics`, `invalidRelayState` (1 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `PlatformOutboxRelayOptions`, `createPlatformOutboxRelay`, `recordRelayObservation`, `platformOutboxQueueMessage`, `relayBoundaryRecord`, `relayDiagnostics`, `invalidRelayState`, `invalidQueueMapping`.

New declarations within this existing file: `relayBoundaryRecord`, `relayDiagnostics`.

Added import edges: `./diagnostics`, `@kanbien/core/diagnostics`, `@kanbien/core`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f21fcf9c5892807943610345583285e275507f9cb6e30a122d744dbf958ff120 after=111e69b8567e293dcdd26bb9beb447dab7bf01f24ed2a4cf9f7b102106feee5c -->

<!-- course-file: platform/persistence/src/transaction.ts -->

### transaction.ts

[Open current source](../../../../../platform/persistence/src/transaction.ts) · **Snapshot:** modified existing file; 20 added / 13 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PlatformPersistenceAtomicWriter`, `platformPersistenceMutation`, `invalidMutation` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `PlatformPersistenceAtomicWriter`, `platformPersistenceMutation`, `invalidMutation`.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=53b71a9bcce54d578c05e664d093b6ad7d159034fb1ec19af94f3920aa8d69ad after=3a263fce516f153a3dee81e8b5920f2f21c6f0c974911879bc06c2edc753c1cf -->

<!-- course-file: platform/persistence/src/types.ts -->

### types.ts

[Open current source](../../../../../platform/persistence/src/types.ts) · **Snapshot:** modified existing file; 12 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports persistence meaning and coordination at this layer.

**Before:** Those operations and their existing result/error contracts already existed. Several local rejections, callback failures and uncertain outcomes shared coarse descriptions. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `platformPersistenceLeaseOwner`, `platformPersistenceFence`, `platformPersistenceAttempt`, `platformPersistenceLease`, `nextPlatformPersistenceLease` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Versioned persistence attribution and bounded related-record retention preserve historical v1 definitions and existing transition logs/metric labels. Transition observers report primary and explicitly selected companion records, honor operational-log opt-outs and isolate sink failure from work outcomes.

**Why:** An agent must not retry an uncertain write as though it were known not to have happened. It also needs to distinguish local validation from provider denial or transaction conflict.

Changed declaration anchors: `platformPersistenceLeaseOwner`, `platformPersistenceFence`, `platformPersistenceAttempt`, `platformPersistenceLease`, `nextPlatformPersistenceLease`.

Added import edges: `./diagnostics`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=72ade7cb6560f3ff890650a1d7273b55fce39421a303983dba1ec2ef54e7062a after=41c9d5dfca2389160212473f20cf26d4905bd7af96aad56d379cba95dbbd6e72 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which evidence would establish write-not-reached, and which merely establishes that the invocation did not return?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No new transaction, SQL, privilege, retry or delivery guarantee is authorized by adding diagnostics. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/persistence/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L058 platform/persistence](058-platform-persistence.md) · [L059 platform/persistence/contracts](059-platform-persistence-contracts.md) · [L061 platform/persistence/src/observability](061-persistence-src-observability.md) · [L062 platform/persistence/tests](062-platform-persistence-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 9 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
