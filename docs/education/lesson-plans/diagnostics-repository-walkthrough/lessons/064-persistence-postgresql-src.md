<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l064
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-03"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/persistence/postgresql/src.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L064 — platform/adapters/aws/persistence/postgresql/src

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/persistence/postgresql/src -->

## What you will understand

The PostgreSQL adapter implements Platform persistence against a relational database and binds connection, credentials, queries and transactions.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **14 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare an authentication-related native code with prose that merely says authentication failed. The classifier must rely on its supported machine evidence or retain unknown. Compare a pool query failure with cleanup end failing afterward; preserve the original outcome.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence.

**After:** The adapter observes configuration, credential, connect/query/transaction/cleanup boundaries and uses declared machine signals where available. Shared Security owns certificate/TLS meanings; Persistence supplies operation context.

**Why this was needed:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

This directory contains `implementation`, `barrel-or-implementation`, `observer` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/config.ts -->

### config.ts

The filename and comparison below describe the original course snapshot.
DIAG-009/010 later retired the forwarding file; the current-source link now
opens the configuration folder's public index. The checker and contracts live
in that folder, not in a second sibling implementation.

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/configuration/index.ts) · **Snapshot:** modified existing file; 34 added / 9 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PostgreSqlPersistenceConfigurationError`, `postgreSqlPersistenceConfiguration`, `invalid`, `integerIssue`, `postgreSqlLoginNameRule`, `postgreSqlPersistenceConfigurationTextRules` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Add bounded configuration reasons and a provider-owned login-name rule shared by password credentials, IAM and target preflight, retaining leading-underscore acceptance and separate database/schema syntax without changing token signing or provider acceptance behavior.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `PostgreSqlPersistenceConfigurationError`, `postgreSqlPersistenceConfiguration`, `invalid`, `integerIssue`, `postgreSqlLoginNameRule`, `postgreSqlPersistenceConfigurationTextRules`.

New declarations within this existing file: `integerIssue`, `postgreSqlLoginNameRule`, `postgreSqlPersistenceConfigurationTextRules`.

Added import edges: `@kanbien/core/config`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=34706b351ec37128fbc7a8b3840807ca0ffe3af666dce9382882b535ba521e1f after=580b5dd0fd5d15c94585084004de9d9929afab010f8d0cba257271e8f6137830 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/connection.ts -->

### connection.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/connection.ts) · **Snapshot:** modified existing file; 18 added / 8 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `createNodePostgreSqlConnectionPool`, `createNodePostgreSqlTokenConnectionPool`, `nodePoolAdapter`, `nodeClientAdapter` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Adapter-owned observations locate actual pool/transaction/migration/atomic/store predicates and bounded decode reductions without changing SQL, retries, results, callback/traversal truthiness, raw throws, double rollback or release precedence. Unknown decoder/body throws do not prove invalid data; matched lease reconciliation does not prove expiry.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `createNodePostgreSqlConnectionPool`, `createNodePostgreSqlTokenConnectionPool`, `nodePoolAdapter`, `nodeClientAdapter`.

Added import edges: `@kanbien/platform-persistence`, `./observations`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=eab912af3d66810cfbadc61d13f8a9239689f049b99e306f80a5eb53f43629f0 after=d0f7999b100da1ff092cf39b5ae9c0db92cef78670fd9fc60f365f2db67290ad -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/credentials.ts -->

### credentials.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/credentials.ts) · **Snapshot:** added (absent from baseline); 27 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** This implementation/helper file was absent at the baseline; its surrounding capability may already have existed.

**After:** Updates `PostgreSqlPasswordCredentials`, `PostgreSqlCredentialIssue`, `postgreSqlPasswordCredentials` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Validate already-parsed credential fields with exact value-free reasons; preserve accepted bytes and distinguish structural validation from actual database authentication.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `PostgreSqlPasswordCredentials`, `PostgreSqlCredentialIssue`, `postgreSqlPasswordCredentials`.

Added import edges: `@kanbien/core/config`, `@kanbien/core/shared`, `./config`.

Owning registered proof: `postgresql-connection-diagnostics`, `persistence-composition`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=2efa25256b1a37d9596c72efd91cc5cb0f22764e3526bf281af84f4b14c97650 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/errors.ts -->

### errors.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/errors.ts) · **Snapshot:** modified existing file; 86 added / 11 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PostgreSqlPersistenceOperation`, `postgreSqlPersistenceOperationError`, `explicitDefinitions`, `postgreSqlFailureClassifications`, `PostgreSqlObservedPhase`, `postgreSqlFailureDiagnostic`, `observedCause` (1 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Translate bounded machine-code, causal and actual-invocation evidence; recover observed phases through private wrappers, retain the existing primary classification precedence and attach selected shared-security observations only to TLS-classified failures. No provider fault, safe replay or schema/capacity cause is inferred.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `PostgreSqlPersistenceOperation`, `postgreSqlPersistenceOperationError`, `explicitDefinitions`, `postgreSqlFailureClassifications`, `PostgreSqlObservedPhase`, `postgreSqlFailureDiagnostic`, `observedCause`, `postgreSqlSecurityDiagnosticRecords`.

New declarations within this existing file: `explicitDefinitions`, `observedCause`, `postgreSqlSecurityDiagnosticRecords`.

Added import edges: `@kanbien/core`, `@kanbien/platform-security`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6c99cf706073bd6a0d5fb5dcb87357a07b5e753e7db60216a93fab04c4a730f1 after=feb839681435a4b913c14a521427d7b26dc2ea1c30cf973effe46bc742637808 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/index.ts -->

### index.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/index.ts) · **Snapshot:** modified existing file; 6 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Public export barrel: a stable import surface, not a new operating component.

**Before:** The file already exposed its existing supported API.

**After:** Adds the public exports from `./credentials`. The implementation and diagnostic meaning remain in those owning modules.

**Why:** Callers and compiled consumers need access to the new APIs without reaching into private files; a barrel edit itself does not perform or report a provider operation.

Added import edges: `./credentials`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=94536fabd2f3f397c9f21485b5ecad1a9c75cc1e056a861946dca63cb50b6f66 after=660aaa404fd5c361384c16600663e94bf333fd091df8e33b1889766310739c2b -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/lineage.ts -->

### lineage.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/lineage.ts) · **Snapshot:** modified existing file; 20 added / 16 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PostgreSqlPlatformRecordChangeStoreOptions`, `createPostgreSqlPlatformRecordChangeStore`, `findChanges`, `duplicateChange` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Adapter-owned observations locate actual pool/transaction/migration/atomic/store predicates and bounded decode reductions without changing SQL, retries, results, callback/traversal truthiness, raw throws, double rollback or release precedence. Unknown decoder/body throws do not prove invalid data; matched lease reconciliation does not prove expiry.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `PostgreSqlPlatformRecordChangeStoreOptions`, `createPostgreSqlPlatformRecordChangeStore`, `findChanges`, `duplicateChange`.

Added import edges: `./observations`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=19a795f9e02c868f9bf50d848d84a0ca437f6b25a78d93ac879e618a9a59aa6c after=fa993e15771534eb47b6021fedd7ee6571a398baf9e82a78678fb29863b589cf -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/migrations.ts -->

### migrations.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/migrations.ts) · **Snapshot:** modified existing file; 47 added / 25 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `createPostgreSqlMigrationRunner`, `applyManifest`, `manifestRejection`, `invalidMigration`, `checksumMismatch` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Adapter-owned observations locate actual pool/transaction/migration/atomic/store predicates and bounded decode reductions without changing SQL, retries, results, callback/traversal truthiness, raw throws, double rollback or release precedence. Unknown decoder/body throws do not prove invalid data; matched lease reconciliation does not prove expiry.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `createPostgreSqlMigrationRunner`, `applyManifest`, `manifestRejection`, `invalidMigration`, `checksumMismatch`.

New declarations within this existing file: `manifestRejection`.

Added import edges: `./observations`.

Declarations removed or relocated: `validManifest`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=acc80dd1c4b78ba75f092de77dd6bce2b782b7ec709b783ee96c77cde96f29e4 after=7fb3f48ed9d4a0f45028a59430233a01082558d54f5d34f3f1670d4aa1637789 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/observations.ts -->

### observations.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/observations.ts) · **Snapshot:** added (absent from baseline); 80 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Observes local progress and safely hands off selected diagnostic evidence.

**Before:** This dedicated observation helper was absent.

**After:** Adapter-owned observations locate actual pool/transaction/migration/atomic/store predicates and bounded decode reductions without changing SQL, retries, results, callback/traversal truthiness, raw throws, double rollback or release precedence. Unknown decoder/body throws do not prove invalid data; matched lease reconciliation does not prove expiry. Read the changed functions below to locate observation versus business work.

**Why:** Knowing where execution reached is different from guessing a cause. Optional reporting must preserve original outcomes and must not replay business work.

Changed declaration anchors: `observeBoundary`, `localRejection`, `Issue`, `storedObservation`, `StoredObservation`.

Added import edges: `@kanbien/platform-persistence`, `@kanbien/core/diagnostics`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=aab3848e93e3da57ebc09d10d743b4ba2e0a31e3fbb4ec5184379544f7eb54e7 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/outbox.ts -->

### outbox.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/outbox.ts) · **Snapshot:** modified existing file; 61 added / 42 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PostgreSqlPlatformOutboxStoreOptions`, `createPostgreSqlPlatformOutboxStore`, `findOutbox`, `duplicateOutbox`, `missingOutbox`, `invalidLimit`, `invalidLease` (5 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Adapter-owned observations locate actual pool/transaction/migration/atomic/store predicates and bounded decode reductions without changing SQL, retries, results, callback/traversal truthiness, raw throws, double rollback or release precedence. Unknown decoder/body throws do not prove invalid data; matched lease reconciliation does not prove expiry.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `PostgreSqlPlatformOutboxStoreOptions`, `createPostgreSqlPlatformOutboxStore`, `findOutbox`, `duplicateOutbox`, `missingOutbox`, `invalidLimit`, `invalidLease`, `invalidStoredOutbox`, `notLeased`, `staleFence`, `leaseExpired`, `failure`.

Added import edges: `./observations`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b93daa5a708888f5843c40e6bfc5dae7bc1e0acdede636cfe710dc720ab1fe06 after=6086246d76671ba3800606c4e5acd1d32dcf641ac0a5e3bb4e93f94fe5868b57 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/processing.ts -->

### processing.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/processing.ts) · **Snapshot:** modified existing file; 56 added / 32 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PostgreSqlPlatformProcessingStoreOptions`, `createPostgreSqlPlatformProcessingStore`, `findProcessing`, `invalidLease`, `invalidStoredProcessing`, `notClaimed`, `staleFence` (2 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Adapter-owned observations locate actual pool/transaction/migration/atomic/store predicates and bounded decode reductions without changing SQL, retries, results, callback/traversal truthiness, raw throws, double rollback or release precedence. Unknown decoder/body throws do not prove invalid data; matched lease reconciliation does not prove expiry.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `PostgreSqlPlatformProcessingStoreOptions`, `createPostgreSqlPlatformProcessingStore`, `findProcessing`, `invalidLease`, `invalidStoredProcessing`, `notClaimed`, `staleFence`, `leaseExpired`, `failure`.

Added import edges: `./observations`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=79f4066771dc2ea791559d0b216d83938187b0c67a874b8da774d61b9476b58a after=f771105cfaf50e84c924b83bda2123431ccc02e4c0bd893caf6b006a139b3dd0 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/rds-iam-authentication.ts -->

### rds-iam-authentication.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/rds-iam-authentication.ts) · **Snapshot:** modified existing file; 8 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `rdsIamAuthenticationTextRules` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Add bounded configuration reasons and a provider-owned login-name rule shared by password credentials, IAM and target preflight, retaining leading-underscore acceptance and separate database/schema syntax without changing token signing or provider acceptance behavior.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `rdsIamAuthenticationTextRules`.

New declarations within this existing file: `rdsIamAuthenticationTextRules`.

Added import edges: `@kanbien/core/config`, `./config`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ead3700f877cc7f075ee1b9e778a7b05cf6afaf8f97b0b7fd1455bc730348fb2 after=771067c81692e1c37e40822ba3479c44bb69e476f1e3b65095906ae7cecc2745 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/records.ts -->

### records.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/records.ts) · **Snapshot:** modified existing file; 61 added / 19 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `outboxRecordFromRow`, `processingRecordFromRow`, `recordChangeFromRow`, `relation`, `leaseFromRow`, `rejectionCondition` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Adapter-owned observations locate actual pool/transaction/migration/atomic/store predicates and bounded decode reductions without changing SQL, retries, results, callback/traversal truthiness, raw throws, double rollback or release precedence. Unknown decoder/body throws do not prove invalid data; matched lease reconciliation does not prove expiry.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `outboxRecordFromRow`, `processingRecordFromRow`, `recordChangeFromRow`, `relation`, `leaseFromRow`, `rejectionCondition`.

New declarations within this existing file: `rejectionCondition`.

Added import edges: `./observations`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=09df11ef256b3d90dd6520620196c1ef9a424449bd36dd7214c40ab500c38f67 after=75a00e9c37e26363f3d1e871b2b09a7f4cd0684e72049fe64ad76516e036c4ec -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/telemetry.ts -->

### telemetry.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/telemetry.ts) · **Snapshot:** modified existing file; 60 added / 11 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `recordPostgreSqlPersistenceTelemetry`, `postgreSqlPlatformPersistenceObserver`, `intrinsicPromiseThen`, `consumeRejection`, `observeTelemetryFailure` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): The optional existing persistence diagnostic port observes local telemetry encoding versus sink callback failure, consumes returned rejection without awaiting/replay, and independently retains selected selected source primary plus eight related records. A failed operation getter does not invent an owning operation.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `recordPostgreSqlPersistenceTelemetry`, `postgreSqlPlatformPersistenceObserver`, `intrinsicPromiseThen`, `consumeRejection`, `observeTelemetryFailure`.

New declarations within this existing file: `intrinsicPromiseThen`, `consumeRejection`, `observeTelemetryFailure`.

Owning registered proof: `postgresql-connection-diagnostics`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ec215519b819008be18e1240fdc020ed1ab4fa062ea6510b1f5e7c856bd9f255 after=8becfb13770a45d0fd26203972fe73f995b7e63b6e18efc85d2c6d520857e1de -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/src/transactions.ts -->

### transactions.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/src/transactions.ts) · **Snapshot:** modified existing file; 64 added / 28 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements or exports postgresql: provider evidence at this layer.

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `PostgreSqlTransactionOptions`, `PostgreSqlAtomicTransactionBuffer`, `createPostgreSqlPlatformPersistenceFactWriter`, `createPostgreSqlPlatformPersistenceAtomicWriter`, `stagePostgreSqlTransactionStatement`, `withPostgreSqlTransaction`, `writePlatformFacts` (3 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Adapter-owned observations locate actual pool/transaction/migration/atomic/store predicates and bounded decode reductions without changing SQL, retries, results, callback/traversal truthiness, raw throws, double rollback or release precedence. Unknown decoder/body throws do not prove invalid data; matched lease reconciliation does not prove expiry.

**Why:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

Changed declaration anchors: `PostgreSqlTransactionOptions`, `PostgreSqlAtomicTransactionBuffer`, `createPostgreSqlPlatformPersistenceFactWriter`, `createPostgreSqlPlatformPersistenceAtomicWriter`, `stagePostgreSqlTransactionStatement`, `withPostgreSqlTransaction`, `writePlatformFacts`, `invalidAtomicTransaction`, `rejectedDmlStatement`, `failureData`.

New declarations within this existing file: `rejectedDmlStatement`, `failureData`.

Added import edges: `./observations`.

Declarations removed or relocated: `isReviewedDmlStatement`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=cccbc723c73d796e413c708beebd7f4ddb4a70878c71252137e556873778d869 after=5e4e37140b4894cc6b64724bfbbcf1f73e79b0dbe216da35c7f1848186984886 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why is matching an English error sentence less reliable than an explicitly supported native code?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Certificate parsing proves syntax, not peer identity, trust-chain validity or a successful live RDS connection. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/persistence/postgresql/src) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L063 platform/adapters/aws/persistence/postgresql](063-aws-persistence-postgresql.md) · [L065 platform/adapters/aws/persistence/postgresql/tests](065-persistence-postgresql-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 14 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
