<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l067
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-03"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/persistence/dynamodb/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L067 — platform/adapters/aws/persistence/dynamodb/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/persistence/dynamodb/src -->

## What you will understand

This adapter stores Platform records, outbox entries, claims and lineage using DynamoDB commands and existing transaction semantics.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **8 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a supported conditional rejection with a generic thrown object bearing a plausible message. The former may support the declared condition classification; the latter must not be promoted into that conclusion.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The adapter already performed these commands, but local configuration, stored attributes, condition failures and invocation failures could collapse into broad persistence errors.

**After:** Bounded observations identify the existing command or stored-field location and distinguish supported condition evidence from unknown invocation failures. Source companions survive selected wrappers.

**Why this was needed:** A condition rejection is not the same thing as inability to read the response. Incorrectly claiming absence or conflict can cause an agent to choose an unsafe recovery.

This directory contains `implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/persistence/dynamodb/src/client.ts -->

### client.ts

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/src/client.ts) · **Snapshot:** modified existing file; 4 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports dynamodb persistence at this layer.

**Before:** The adapter already performed these commands, but local configuration, stored attributes, condition failures and invocation failures could collapse into broad persistence errors. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `createAwsSdkDynamoDbPersistenceCommandClient` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Finite current command/selection/encoding/callback/response/decode and durable-state observations preserve legacy getter reads, codes/params, SDK receiver and selection-before-encoding, raw throws, write ordering/counts and race validation-without-write policy. Neutral conditions are not automatic errors; transaction cancellation alone does not establish cause.

**Why:** A condition rejection is not the same thing as inability to read the response. Incorrectly claiming absence or conflict can cause an agent to choose an unsafe recovery.

Changed declaration anchors: `createAwsSdkDynamoDbPersistenceCommandClient`.

Added import edges: `@kanbien/platform-persistence`, `./observations`.

Owning registered proof: `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=20064bb8a1e55354a83257bc6d6abd0638970a5dd2028f257271efffb9241de5 after=13257ad08f9b2d25c9573e79617727faf354c41889dbbd70d0de62b8c7777206 -->

<!-- course-file: platform/adapters/aws/persistence/dynamodb/src/configuration.ts -->

### configuration.ts

The filename and comparison below describe the original course snapshot.
DIAG-009/010 later retired the forwarding file; the current-source link now
opens the configuration folder's public index. The checker and contracts live
in that folder, not in a second sibling implementation.

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/src/configuration/index.ts) · **Snapshot:** modified existing file; 14 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports dynamodb persistence at this layer.

**Before:** The adapter already performed these commands, but local configuration, stored attributes, condition failures and invocation failures could collapse into broad persistence errors. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `DynamoDbPersistenceConfigurationError`, `dynamoDbPersistenceConfiguration`, `configurationField` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Actual blank/oversized table/index predicates bind persistence-owned closed fields. entries/getter order, first failure, historical tableName detail for oversized indices and missing-to-empty target reduction remain, without inventing absent-value evidence.

**Why:** A condition rejection is not the same thing as inability to read the response. Incorrectly claiming absence or conflict can cause an agent to choose an unsafe recovery.

Changed declaration anchors: `DynamoDbPersistenceConfigurationError`, `dynamoDbPersistenceConfiguration`, `configurationField`.

New declarations within this existing file: `configurationField`.

Added import edges: `@kanbien/platform-persistence`, `@kanbien/core/diagnostics`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`, `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=2bfdc125745daf94e5945ca6305d69e5a6c5db81ac64555ade6a176566480de9 after=5d018bc2b32139cf870fe2b03297750aecb28091002f953f07899e5449f13bee -->

<!-- course-file: platform/adapters/aws/persistence/dynamodb/src/lineage-store.ts -->

### lineage-store.ts

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/src/lineage-store.ts) · **Snapshot:** modified existing file; 24 added / 24 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports dynamodb persistence at this layer.

**Before:** The adapter already performed these commands, but local configuration, stored attributes, condition failures and invocation failures could collapse into broad persistence errors. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `DynamoDbPlatformRecordChangeStoreOptions`, `createDynamoDbPlatformRecordChangeStore`, `failure` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Finite current command/selection/encoding/callback/response/decode and durable-state observations preserve legacy getter reads, codes/params, SDK receiver and selection-before-encoding, raw throws, write ordering/counts and race validation-without-write policy. Neutral conditions are not automatic errors; transaction cancellation alone does not establish cause.

**Why:** A condition rejection is not the same thing as inability to read the response. Incorrectly claiming absence or conflict can cause an agent to choose an unsafe recovery.

Changed declaration anchors: `DynamoDbPlatformRecordChangeStoreOptions`, `createDynamoDbPlatformRecordChangeStore`, `failure`.

Added import edges: `./observations`.

Declarations removed or relocated: `responseItems`, `isItem`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=d7007e7b02a9d7695fe64debf64c7225b3e9c532de01c8f780b2e6c3d047cce2 after=65c77c9ff10c394fd53320b6b252b5a3ad91ba5dd2f378ff613e1c60429b5e91 -->

<!-- course-file: platform/adapters/aws/persistence/dynamodb/src/observations.ts -->

### observations.ts

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/src/observations.ts) · **Snapshot:** added (absent from baseline); 189 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Finite current command/selection/encoding/callback/response/decode and durable-state observations preserve legacy getter reads, codes/params, SDK receiver and selection-before-encoding, raw throws, write ordering/counts and race validation-without-write policy. Neutral conditions are not automatic errors; transaction cancellation alone does not establish cause. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `Command`, `Issue`, `nativeNames`, `own`, `nativeCondition`, `cancellation`, `dynamoDbObservation`, `DynamoDbObservation`, `attributeObservation`, `AttributeObservation`, `responseItem`, `responseItems` (1 more in source).

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/platform-persistence`, `./client`, `./errors`, `./records`.

Owning registered proof: `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=760f13874d946e5d5c743f59c65d391ef58da95bd153d3adb68419c83f03277d -->

<!-- course-file: platform/adapters/aws/persistence/dynamodb/src/outbox-store.ts -->

### outbox-store.ts

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/src/outbox-store.ts) · **Snapshot:** modified existing file; 85 added / 71 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports dynamodb persistence at this layer.

**Before:** The adapter already performed these commands, but local configuration, stored attributes, condition failures and invocation failures could collapse into broad persistence errors. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `DynamoDbPlatformOutboxStoreOptions`, `createDynamoDbPlatformOutboxStore`, `readOutbox`, `resolveOutboxClaimRace`, `resolvePublishRace`, `validatePublish`, `outboxNotFound` (1 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Finite current command/selection/encoding/callback/response/decode and durable-state observations preserve legacy getter reads, codes/params, SDK receiver and selection-before-encoding, raw throws, write ordering/counts and race validation-without-write policy. Neutral conditions are not automatic errors; transaction cancellation alone does not establish cause.

**Why:** A condition rejection is not the same thing as inability to read the response. Incorrectly claiming absence or conflict can cause an agent to choose an unsafe recovery.

Changed declaration anchors: `DynamoDbPlatformOutboxStoreOptions`, `createDynamoDbPlatformOutboxStore`, `readOutbox`, `resolveOutboxClaimRace`, `resolvePublishRace`, `validatePublish`, `outboxNotFound`, `failure`.

Added import edges: `./observations`.

Declarations removed or relocated: `responseItem`, `responseItems`, `isItem`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=7e2dc0eff61afe3809147f529311a10748f272c6e00ad544f31b2dcd8ddcb4ab after=2f7bc314e8bb0f6e416fb9e2885a517e43f5d9a7a2065ea3a02e34e099d91fb7 -->

<!-- course-file: platform/adapters/aws/persistence/dynamodb/src/processing-store.ts -->

### processing-store.ts

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/src/processing-store.ts) · **Snapshot:** modified existing file; 99 added / 74 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports dynamodb persistence at this layer.

**Before:** The adapter already performed these commands, but local configuration, stored attributes, condition failures and invocation failures could collapse into broad persistence errors. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `DynamoDbPlatformProcessingStoreOptions`, `createDynamoDbPlatformProcessingStore`, `readProcessing`, `resolveProcessingClaimRace`, `resolveCompletionRace`, `resolveReleaseRace`, `validateCompletion` (5 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Finite current command/selection/encoding/callback/response/decode and durable-state observations preserve legacy getter reads, codes/params, SDK receiver and selection-before-encoding, raw throws, write ordering/counts and race validation-without-write policy. Neutral conditions are not automatic errors; transaction cancellation alone does not establish cause.

**Why:** A condition rejection is not the same thing as inability to read the response. Incorrectly claiming absence or conflict can cause an agent to choose an unsafe recovery.

Changed declaration anchors: `DynamoDbPlatformProcessingStoreOptions`, `createDynamoDbPlatformProcessingStore`, `readProcessing`, `resolveProcessingClaimRace`, `resolveCompletionRace`, `resolveReleaseRace`, `validateCompletion`, `validateRelease`, `processingNotClaimedCompletion`, `staleFenceCompletion`, `leaseExpiredCompletion`, `failure`.

Added import edges: `./observations`.

Declarations removed or relocated: `responseItem`, `isItem`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b35e250246b36c10a32fa0bf4d838ee9bfe28efdf575ebdd3d27e7400e242303 after=c7a5b40b6614338ac3017201b35aa04b51a07abbf9ef262f891138809252480f -->

<!-- course-file: platform/adapters/aws/persistence/dynamodb/src/records.ts -->

### records.ts

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/src/records.ts) · **Snapshot:** modified existing file; 59 added / 30 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports dynamodb persistence at this layer.

**Before:** The adapter already performed these commands, but local configuration, stored attributes, condition failures and invocation failures could collapse into broad persistence errors. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `itemToOutboxRecord`, `itemToProcessingRecord`, `itemToRecordChange`, `rowDecoder`, `ownValue` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Finite current command/selection/encoding/callback/response/decode and durable-state observations preserve legacy getter reads, codes/params, SDK receiver and selection-before-encoding, raw throws, write ordering/counts and race validation-without-write policy. Neutral conditions are not automatic errors; transaction cancellation alone does not establish cause.

**Why:** A condition rejection is not the same thing as inability to read the response. Incorrectly claiming absence or conflict can cause an agent to choose an unsafe recovery.

Changed declaration anchors: `itemToOutboxRecord`, `itemToProcessingRecord`, `itemToRecordChange`, `rowDecoder`, `ownValue`.

New declarations within this existing file: `rowDecoder`, `ownValue`.

Added import edges: `./observations`.

Declarations removed or relocated: `itemToLease`, `itemToChangedFields`, `requiredString`, `optionalString`, `requiredAttributeString`, `requiredNumber`, `requiredIso`, `requiredOutboxState`, `requiredProcessingState`, `requiredProcessingOutcome` (2 more in source). Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ee1d6a8f60f2732dd3b6e62031ce9d79a88674b18e0cbcabfc9ca08c4cf3d136 after=12d5e70dd5ff334b9613a44c9713bfbbb09adbd720c8982b7bdccb5425a6cc72 -->

<!-- course-file: platform/adapters/aws/persistence/dynamodb/src/transactions.ts -->

### transactions.ts

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/src/transactions.ts) · **Snapshot:** modified existing file; 45 added / 20 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports dynamodb persistence at this layer.

**Before:** The adapter already performed these commands, but local configuration, stored attributes, condition failures and invocation failures could collapse into broad persistence errors. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `DynamoDbPlatformPersistenceFactWriterOptions`, `DynamoDbPlatformPersistenceAtomicWriterOptions`, `DynamoDbAtomicTransactionBuffer`, `createDynamoDbPlatformPersistenceFactWriter`, `createDynamoDbPlatformPersistenceAtomicWriter`, `stageDynamoDbTransactionWrite`, `invalidAtomicTransaction` (1 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Finite current command/selection/encoding/callback/response/decode and durable-state observations preserve legacy getter reads, codes/params, SDK receiver and selection-before-encoding, raw throws, write ordering/counts and race validation-without-write policy. Neutral conditions are not automatic errors; transaction cancellation alone does not establish cause.

**Why:** A condition rejection is not the same thing as inability to read the response. Incorrectly claiming absence or conflict can cause an agent to choose an unsafe recovery.

Changed declaration anchors: `DynamoDbPlatformPersistenceFactWriterOptions`, `DynamoDbPlatformPersistenceAtomicWriterOptions`, `DynamoDbAtomicTransactionBuffer`, `createDynamoDbPlatformPersistenceFactWriter`, `createDynamoDbPlatformPersistenceAtomicWriter`, `stageDynamoDbTransactionWrite`, `invalidAtomicTransaction`, `dynamoDbTransactionWriteCount`.

New declarations within this existing file: `dynamoDbTransactionWriteCount`.

Added import edges: `./observations`.

Declarations removed or relocated: `isOneDynamoDbTransactionWrite`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=4683cb7441b6d857feb676cc54d6bc62af5d1b9c6936bce280347fc128f06503 after=f92d9e948a1ddc705a7d31f7908f934bba18eaddabc779812b417ebc0b61dc5d -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Can a malformed stored record be diagnosed without copying its attribute values into logs?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Existing key layouts, transaction behavior and command order are not redesigned by this work. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/persistence/dynamodb/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L066 platform/adapters/aws/persistence/dynamodb](066-aws-persistence-dynamodb.md) · [L068 platform/adapters/aws/persistence/dynamodb/tests](068-persistence-dynamodb-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 8 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
