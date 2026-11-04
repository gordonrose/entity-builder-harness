<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l089
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder infra/04.deploy/03.product/entrypoints.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L089 — infra/04.deploy/03.product/entrypoints

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: infra/04.deploy/03.product/entrypoints -->

## What you will understand

Entrypoints assemble concrete settings, catalogs, adapters, reporters and programs. A one-shot program performs a task such as migration or verification and exits.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **30 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Follow a missing IAM username from its target binding through Core validation, the structured failure, selected catalog and safe task output to the Python reader. At no step is the username value required. Contrast source-read failure and permission proof rejection.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text.

**After:** Target bindings connect reusable definitions to actual settings and call boundaries. Administration/verifier observations preserve primary failure, bounded source companions, operation progress and existing SQL/privilege/cleanup behavior.

**Why this was needed:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

This directory contains `implementation`, `definition` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts -->

### kanbien-core-server-persistence-administration.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.ts) · **Snapshot:** modified existing file; 237 added / 90 removed lines. These are textual counts, not a count of new features.

**What it does:** Executes the existing bounded administration operations.

**Before:** Administration already created/checked roles, grants, schema ownership and privilege proofs, with coarse rejected-task output.

**After:** Observes actual input/row-count/role/privilege predicates and SQL invocation boundaries through target-owned records, preserving original task rejection first and bounded additional observations.

**Why:** A failed privilege proof must be distinguishable from an unreturned query without exposing SQL, role names or credential values; existing privileges and action order stay unchanged.

Changed declaration anchors: `runKanbienCoreServerPersistenceAdministration`, `bootstrapIdentities`, `bootstrapMigrationOwnedSchema`, `transferRelationOwnership`, `grantRuntimeApplicationAccess`, `observeMigrationState`, `proveRuntimePrivilege`, `expectPermissionDenied`, `configurationFromEnvironment`, `quotedIdentifier`, `observeAdministrationRollback`, `accepted` (1 more in source).

New declarations within this existing file: `observeAdministrationRollback`.

Added import edges: `@kanbien/core/diagnostics`, `./kanbien-core-server-persistence-operation-diagnostics`.

Declarations removed or relocated: `Credentials`, `AdministrationOperation`, `administrationOperation`, `credentialObject`, `identity`. Read the current exports/consumer tests before assuming the public API was removed.

Connected review context (`core-server-persistence-target`; this review may span several files): Connection/IAM/administrator/source/certificate observations and bounded configuration aggregation retain existing defaults, SQL, validation order and outward codes. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=02d60dadac7792c442ba93c4fb9909160086bb9006bd4faef0aa058c6d8c111f after=b3719acab8199921714c4ac3f596044f30bdedb21201e87ff60a6b0177a823a6 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts -->

### kanbien-core-server-persistence-configuration.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.ts) · **Snapshot:** modified existing file; 165 added / 33 removed lines. These are textual counts, not a count of new features.

**What it does:** Binds this target's settings, task evidence and catalogs.

**Before:** Combined target guards and serializers lost detail or had persistence-local versions of cross-cutting concerns.

**After:** Names logical settings, IAM/admin credentials and certificate source/read observations, selects shared definitions and preserves bounded safe task fields.

**Why:** Only composition knows the exact deployed setting sources; Security and Persistence still own reusable meaning.

Changed declaration anchors: `persistenceConfigurationBindings`, `persistenceConfigurationDiagnostic`, `persistenceIamConfigurationDiagnostic`, `persistenceAdministratorCredentialBindings`, `persistenceAdministratorCredentialDiagnostic`, `persistenceAdministrationBindings`, `persistenceAdministrationOperations`, `PersistenceAdministrationOperation`, `persistenceAdministrationRelationships`, `persistenceAdministrationDiagnostics`, `persistenceCertificateSourceDiagnostic`, `persistenceCertificateReadDiagnostic` (12 more in source).

New declarations within this existing file: `persistenceConfigurationBindings`, `persistenceConfigurationDiagnostic`, `persistenceIamConfigurationDiagnostic`, `persistenceAdministratorCredentialBindings`, `persistenceAdministratorCredentialDiagnostic`, `persistenceAdministrationBindings`, `persistenceAdministrationOperations`, `PersistenceAdministrationOperation` (13 more in source).

Added import edges: `@kanbien/core/config`, `@kanbien/platform-config`, `@kanbien/core/diagnostics`, `@kanbien/platform-security`, `@kanbien/platform-persistence`, `@kanbien/platform-observability`, `@kanbien/core`.

Connected review context (`postgresql-password-credential-validation`; this review may span several files): Validate already-parsed credential fields with exact value-free reasons; preserve accepted bytes and distinguish structural validation from actual database authentication. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`, `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=25c7e1b5f339786accb86bd424a924684d7305fdfda2a19bc6f18e857c85a3e2 after=140ae1093ae2626b2fcfde3b4374814bdd5fae984fdedb12318fe9f9df27d830 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-diagnostics.ts -->

### kanbien-core-server-persistence-diagnostics.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-diagnostics.ts) · **Snapshot:** added (absent from baseline); 46 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Defines this target's acceptance-request failure.

**Before:** The endpoint existed without this target-owned request diagnostic module.

**After:** Owns the acceptance request-invalid definition/catalog and safe constructor.

**Why:** Target endpoint predicates belong to the endpoint owner, not to generic HTTP or PostgreSQL code.

Changed declaration anchors: `kanbienCoreAcceptanceRequestDiagnostic`, `kanbienCoreAcceptanceDiagnosticCatalog`, `kanbienCoreAcceptanceRequestFailure`.

Added import edges: `@kanbien/core/diagnostics`.

Connected review context (`core-server-persistence-target`; this review may span several files): Connection/IAM/administrator/source/certificate observations and bounded configuration aggregation retain existing defaults, SQL, validation order and outward codes. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=51c84fde6ae3473413371f492b0b68f4d661cd2baa3726a576c8b7b14b71015f -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-iam-authentication.ts -->

### kanbien-core-server-persistence-iam-authentication.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-iam-authentication.ts) · **Snapshot:** modified existing file; 25 added / 11 removed lines. These are textual counts, not a count of new features.

**What it does:** Binds target IAM username/region to the existing PostgreSQL token provider.

**Before:** The compatibility reader returned a value or undefined, losing which requirement was rejected.

**After:** Adds the structured result reader using shared text rules and target diagnostic bindings, retaining the old value-or-undefined reader for compatibility.

**Why:** Production callers can retain exact value-safe configuration evidence without breaking older callers or retrieving a database password.

Changed declaration anchors: `PersistenceIamAuthentication`, `persistenceIamAuthenticationResult`, `persistenceIamAuthentication`.

New declarations within this existing file: `PersistenceIamAuthentication`, `persistenceIamAuthenticationResult`.

Added import edges: `@kanbien/core/config`, `./kanbien-core-server-persistence-configuration`.

Connected review context (`core-server-persistence-iam-configuration`; this review may span several files): Aggregate exact username and region predicates using core validation and provider-owned lexical rules; retain value-free detail through every production IAM caller and keep token consumption lazy. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=e87bad76b7a3eeb0856f5b7adedccc6b59fcaff0bbba13bd8f2be0f5c2fb75c2 after=66dfd907087498ad33c769b366e2d834615227388db176d7a44e040d6f727862 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts -->

### kanbien-core-server-persistence-migration.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.ts) · **Snapshot:** modified existing file; 28 added / 11 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs the target's one-shot PostgreSQL migration program.

**Before:** Migration configuration, execution, task serialization and pool cleanup already existed.

**After:** Retains structured configuration/source diagnostics and observes migration-body and cleanup boundaries through selected internal reporting, preserving historical task output and original throw/exit behavior.

**Why:** The migration caller must not discard upstream observations or silently recast cleanup failure as successful completion. Internal process logs do not automatically expand the historical task-reader envelope.

Changed declaration anchors: `runKanbienCoreServerPersistenceMigration`, `rejected`.

Added import edges: `@kanbien/core/diagnostics`, `./kanbien-core-server-persistence-operation-diagnostics`.

Connected review context (`core-server-persistence-target`; this review may span several files): Connection/IAM/administrator/source/certificate observations and bounded configuration aggregation retain existing defaults, SQL, validation order and outward codes. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=527617057385bf4f23919b732620aa4f08578cb229e4420acbb5410930d469e9 after=d68ea7cc3dbae3377c9f63d2d077ec8d407905a8e7282fdc5cbb2b6490938c7f -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-operation-diagnostics.ts -->

### kanbien-core-server-persistence-operation-diagnostics.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-operation-diagnostics.ts) · **Snapshot:** added (absent from baseline); 213 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Defines target-specific administration and verification observations.

**Before:** There was no dedicated catalog for these concrete target operation predicates and boundaries.

**After:** Declares finite administration/verifier operation, field, phase, reason and progress detail, plus constructors/observation helpers used by task producers.

**Why:** A rejected privilege proof or malformed verification result must identify the actual target responsibility, not expose SQL or pretend a generic library knows the deployment.

Changed declaration anchors: `predicateClassification`, `boundaryClassification`, `ordinal`, `adminOperations`, `adminFields`, `persistenceAdministrationPredicateDiagnostic`, `persistenceAdministrationBoundaryDiagnostic`, `verifierFields`, `persistenceVerificationPredicateDiagnostic`, `persistenceVerificationBoundaryDiagnostic`, `persistenceTaskOperationDiagnosticCatalog`, `AdministrationPredicateDetail` (21 more in source).

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `@kanbien/platform-persistence`, `@kanbien/platform-security`, `@kanbien/platform-observability`, `@kanbien/platform-contracts`, `./kanbien-core-server-persistence-configuration`.

Connected review context (`core-server-persistence-operation-producers`; this review may span several files): Target-owned administration/role/credential/verifier observations identify actual predicates and call boundaries without SQL, credential, provider-message or identity values. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `restore-connection-diagnostics`, `platform-shell-payload`, `deployment-operation-diagnostics-regression`, `diagnostic-catalog-readers`, `persistence-provider-regression`, `persistence-diagnostic-mapping-regression`, `persistence-payload-regression`, `security-cognito-diagnostics`, `security-shared-rate-limit-diagnostics`, `cloudwatch-observability-runtime`, `ecs-fargate-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=063b0f38be4025d98957d24b5cb6a123a7265ac04585a18d909dc05936b0ff30 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.ts -->

### kanbien-core-server-persistence-postgresql.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql.ts) · **Snapshot:** modified existing file; 94 added / 23 removed lines. These are textual counts, not a count of new features.

**What it does:** Composes PostgreSQL persistence for target acceptance create/read/delete work.

**Before:** The target already performed these operations and existing reconciliation.

**After:** Adds optional diagnostic delivery and selected source retention around the actual operation/result/reconciliation boundaries, preserving writer results and SQL.

**Why:** The target must not replace provider evidence with only a feature-level acceptance failure or call an uncertain write not-attempted.

Changed declaration anchors: `KanbienCoreServerPostgreSqlPersistenceOptions`, `createKanbienCoreServerPostgreSqlPersistenceRuntime`, `createRecord`, `reconciledAcceptanceOutcome`, `readRecord`, `deleteRecord`, `acceptanceTable`, `observeAcceptanceFailure`.

New declarations within this existing file: `reconciledAcceptanceOutcome`, `observeAcceptanceFailure`.

Added import edges: `@kanbien/core/shared`, `@kanbien/platform-persistence`, `@kanbien/platform-security`.

Connected review context (`core-server-persistence-target`; this review may span several files): Connection/IAM/administrator/source/certificate observations and bounded configuration aggregation retain existing defaults, SQL, validation order and outward codes. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=9c7375d504bfa0a619d28765f4b8ffb218c31e6d91994b6ce97fac63a9bc1962 after=a2fa024e40857d334eb1b72f3b9343813da9c525725ec2655e92aaf396bf026d -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts -->

### kanbien-core-server-persistence-restore-verifier.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts) · **Snapshot:** modified existing file; 36 added / 17 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs the target's bounded restore verification program.

**Before:** Restore verification and its existing result/task protocol already existed.

**After:** Preserves selected configuration, source and invocation evidence, and reports existing restore/cleanup failure locations without changing SQL or the historical outcome protocol.

**Why:** A failed verification call, wrong returned proof and cleanup problem need honest separation; this does not perform a new restore or certify live recovery.

Changed declaration anchors: `runKanbienCoreServerPersistenceRestoreVerifier`, `rejectedInvocation`, `rejected`.

New declarations within this existing file: `rejectedInvocation`.

Added import edges: `@kanbien/core/diagnostics`, `./kanbien-core-server-persistence-operation-diagnostics`.

Connected review context (`core-server-persistence-target`; this review may span several files): Connection/IAM/administrator/source/certificate observations and bounded configuration aggregation retain existing defaults, SQL, validation order and outward codes. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=5fb9b66ff5d9322e9e26b681c691cb626e527902da0d61ac883885ceed806acc after=9929ddccce9aeabf345fc979eea857b7fff6ed989c6c1cb9998b409b8c216729 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-role-credential.ts -->

### kanbien-core-server-persistence-role-credential.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-role-credential.ts) · **Snapshot:** modified existing file; 65 added / 22 removed lines. These are textual counts, not a count of new features.

**What it does:** Checks or establishes the existing bounded database login-role conditions.

**Before:** Role restrictions, IAM membership and quoted-identifier checks already existed with coarser failures.

**After:** Adds predicate and call-boundary observations at the actual role/query checks, retaining original SQL, privilege rules, getter order and thrown values.

**Why:** The agent can identify the failed restriction or uncertain query without learning role identifiers or broadening administrative authority.

Changed declaration anchors: `ensureBoundedLoginRole`, `requireBoundedExistingRole`, `ensureRdsIamAuthentication`, `roleFacts`, `requireBoundedRole`, `requireNoElevatedRole`, `quotedIdentifier`.

Added import edges: `./kanbien-core-server-persistence-operation-diagnostics`.

Connected review context (`core-server-persistence-operation-producers`; this review may span several files): Target-owned administration/role/credential/verifier observations identify actual predicates and call boundaries without SQL, credential, provider-message or identity values. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `restore-connection-diagnostics`, `platform-shell-payload`, `deployment-operation-diagnostics-regression`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=19f0541ac5388a7bcf0d3f22a4cf38efb3d1e9768be900ed76694321f000cdf5 after=7f32f0735c785946c59bd5fa20aac45988de235a10b8e455854455bc9c929647 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-runtime-credential.ts -->

### kanbien-core-server-persistence-runtime-credential.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-runtime-credential.ts) · **Snapshot:** modified existing file; 54 added / 23 removed lines. These are textual counts, not a count of new features.

**What it does:** Revokes or restores runtime IAM access under existing task policy.

**Before:** These lifecycle actions and their SQL were already implemented.

**After:** Adds target operation observations for existing input/query boundaries while preserving order, authentication rules, result and cleanup semantics.

**Why:** A failed call is not proof that access was unchanged or fully restored; the next action must respect uncertainty.

Changed declaration anchors: `revokeRuntimeAccess`, `restoreRuntimeIamAccess`, `quotedIdentifier`.

Added import edges: `./kanbien-core-server-persistence-operation-diagnostics`.

Connected review context (`core-server-persistence-operation-producers`; this review may span several files): Target-owned administration/role/credential/verifier observations identify actual predicates and call boundaries without SQL, credential, provider-message or identity values. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `restore-connection-diagnostics`, `platform-shell-payload`, `deployment-operation-diagnostics-regression`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=a2dffd55551b34d1b1e20de917127c78d1b77fd97ae60f5637ba3cc610ab25e9 after=d3a9a0e4e3225be067e6a21e5b2758b3b7b327edb20e0652aafefbc29f9b4782 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.ts -->

### kanbien-core-server-persistence-verifier.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.ts) · **Snapshot:** modified existing file; 61 added / 40 removed lines. These are textual counts, not a count of new features.

**What it does:** Checks the target's private health/acceptance verification surface.

**Before:** The verifier already checked supported modes, addresses, response status and expected results.

**After:** Adds finite input/response/health predicate and invocation records, retaining the original rejected outcome and selected source evidence.

**Why:** A malformed response, rejected health result and failed HTTP invocation have different causes; raw URL, response content and credentials stay private.

Changed declaration anchors: `runKanbienCoreServerPersistenceVerifier`, `verifyHealth`, `accepted`, `rejected`, `isMode`, `isPrivateBaseUrl`, `isRecordId`, `hasOutcome`, `hasRecord`.

Added import edges: `./kanbien-core-server-persistence-operation-diagnostics`.

Connected review context (`core-server-persistence-operation-producers`; this review may span several files): Target-owned administration/role/credential/verifier observations identify actual predicates and call boundaries without SQL, credential, provider-message or identity values. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `restore-connection-diagnostics`, `platform-shell-payload`, `deployment-operation-diagnostics-regression`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=73d0ff2c86b897392f5773af689df8b44deabe7548dbc4abe47f7b0080aae209 after=e69a49d1df7dd0312e5e9c3c8c030b4404cc4aa02f0f9e5c1c941186b3c82cd1 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts -->

### kanbien-core-server-persistence.app.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.ts) · **Snapshot:** modified existing file; 92 added / 27 removed lines. These are textual counts, not a count of new features.

**What it does:** Mounts persistence acceptance routes and the target health surface.

**Before:** Routes, persistence profile and health reporting already existed.

**After:** Adds request-invalid feature records, selected persistence/security health evidence and the request-local observation bridge, retaining public responses, correlation and profile opt-outs.

**Why:** The HTTP layer needs endpoint-specific detail while internal evidence stays out of response metadata.

Changed declaration anchors: `KanbienCorePersistenceRuntime`, `persistenceProfile`, `releaseVerificationProfile`, `createKanbienCoreServerPersistenceApp`, `persistenceHealthObservation`, `healthDiagnosticEvidence`, `AcceptanceRequestReason`, `diagnosticPromiseThen`, `observeInvalidAcceptance`, `acceptanceRecordFromBody`, `acceptanceRecordIdFromQuery`.

New declarations within this existing file: `persistenceHealthObservation`, `healthDiagnosticEvidence`, `AcceptanceRequestReason`, `diagnosticPromiseThen`, `observeInvalidAcceptance`.

Added import edges: `@kanbien/platform-persistence`, `./kanbien-core-server-persistence-diagnostics`.

Declarations removed or relocated: `persistenceHealthStatus`. Read the current exports/consumer tests before assuming the public API was removed.

Connected review context (`core-server-persistence-target`; this review may span several files): Connection/IAM/administrator/source/certificate observations and bounded configuration aggregation retain existing defaults, SQL, validation order and outward codes. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=bdc0e213f39fe72b96ce7dfabebbc2ed4f9483bb77e8a2afe0e4a2ad525d3d34 after=3ee4e579a60cfbe7e299039c645696a3683a06321c1fbde1f03067f3f061d99c -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts -->

### kanbien-core-server-persistence.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.ts) · **Snapshot:** modified existing file; 50 added / 32 removed lines. These are textual counts, not a count of new features.

**What it does:** Starts the concrete persistence-backed core server.

**Before:** The main program already selected configuration, adapters and observability and started the server.

**After:** Carries structured startup/configuration observations and explicitly selected catalogs through target construction and startup-failure handling.

**Why:** Useful diagnostics must exist before app mount or listener startup; successful runtime startup is not proof of backend log delivery.

Changed declaration anchors: `runKanbienCoreServerPersistenceMain`, `persistenceObservabilityFromTargetEnvironment`, `startupFailed`.

Added import edges: `@kanbien/core`, `@kanbien/platform-persistence`, `@kanbien/platform-security`, `@kanbien/core/diagnostics`, `@kanbien/platform-contracts`.

Connected review context (`core-server-persistence-target`; this review may span several files): Connection/IAM/administrator/source/certificate observations and bounded configuration aggregation retain existing defaults, SQL, validation order and outward codes. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6216c8c7480f3bc9b0f9ea225a09fdb407ba4232a4d0d0e3a73108141ce2d392 after=999fb12d9fd20c3fc3264b80fada1de00a51ad8166d4156630001348e01f34c7 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts -->

### kanbien-core-server.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts) · **Snapshot:** modified existing file; 3 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Starts the smaller core-server release-verification target.

**Before:** This entrypoint and its release-verification observability profile already existed.

**After:** Adds the finite supported error-class declarations to that existing profile.

**Why:** The shared finite-class rule needs its actual target consumer updated, not a fabricated new diagnostic service.

Changed declaration anchors: `releaseVerificationProfile`.

Connected review context (`core-server-release-target`; this review may span several files): The bootstrap target's existing release-verification profile declares the exact Server-owned finite error classes through its real production dependency. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=e80a45b542607387eab850a5c0453b097b5aa8368c5277f581a09ce3183696fe after=31b80219c3f266816cf86075831f3581dafd7869c42cc67c638ed5209860cb34 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.ts -->

### kanbien-platform-configuration-diagnostics.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.ts) · **Snapshot:** added (absent from baseline); 114 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns platform-shell-specific configuration and source-read bindings.

**Before:** No dedicated target diagnostic module existed at this path.

**After:** Declares target setting/reason catalogs and selection helpers for environment, relational and lease-owner observations.

**Why:** Existing local consumers still need compatible evidence even though further platform-shell deployment work is now excluded.

Changed declaration anchors: `environmentSettings`, `relationalSettings`, `targetConfigurationReasons`, `TargetConfigurationReason`, `kanbienPlatformConfigurationDiagnostic`, `kanbienPlatformLeaseOwnerSourceDiagnostic`, `LeaseOwnerSourcePhase`, `LeaseOwnerSourceReason`, `targetLeaseOwnerSourceRecord`, `kanbienPlatformConfigurationDiagnosticCatalog`, `targetConfigurationDiagnosticRecord`, `targetEnvironmentConfigurationRecord` (6 more in source).

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `@kanbien/platform-config`, `@kanbien/platform-contracts`, `@kanbien/platform-observability`, `@kanbien/platform-persistence`, `@kanbien/platform-security`, `@kanbien/platform-server`, `@kanbien/platform-workers`.

Connected review context (`relational-target-configuration-bindings`; this review may span several files): Relational task configuration and injected secret guards emit exact fixed logical settings/reasons through existing catches on stderr. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `shell-package-source`, `platform-shell-payload`, `diagnostic-catalog-readers`, `sqs-queue-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=08beaa5495c1dbaa34571f8e3fd3fd69774e1e0b04679dce441b157d6f14e70f -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-delivery-diagnostics.ts -->

### kanbien-platform-delivery-diagnostics.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-delivery-diagnostics.ts) · **Snapshot:** added (absent from baseline); 138 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Binds queue/persistence delivery observations to selected target reporting.

**Before:** The dedicated delivery-binding module was absent.

**After:** Selects finite operation/disposition facts and independently delivers owned plus selected source records.

**Why:** Queue send, publish-marker and worker settlement evidence must not be flattened into one misleading delivery verdict.

Changed declaration anchors: `kanbienPlatformDeliveryBoundaryDiagnostic`, `KanbienPlatformDeliveryBoundaryDetail`, `kanbienPlatformDeliveryDiagnosticCatalog`, `KanbienPlatformDeliveryDiagnosticOptions`, `catalogs`, `deliver`, `reportKanbienPlatformQueueDiagnostic`, `allowedEnum`, `reportKanbienPlatformDeliveryFailure`, `targetDeliveryErrorSource`, `targetDeliveryDisposition`, `reportKanbienPlatformPersistenceDeliveryDiagnostic`.

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `@kanbien/core/queues`, `@kanbien/platform-contracts`, `@kanbien/platform-observability`, `@kanbien/platform-persistence`, `@kanbien/platform-workers`, `@kanbien/platform-runtime`, `@kanbien/platform-security`, `@kanbien/product-kanbien-platform`.

Connected review context (`relational-target-configuration-bindings`; this review may span several files): Relational task configuration and injected secret guards emit exact fixed logical settings/reasons through existing catches on stderr. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `shell-package-source`, `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=5868014059b0c2f0a4038bc70081d9d628a3a24f508efd5c6bceea5eb814fa08 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-observability.ts -->

### kanbien-platform-observability.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-observability.ts) · **Snapshot:** modified existing file; 150 added / 261 removed lines. These are textual counts, not a count of new features.

**What it does:** Binds target environment settings to the existing observability runtime.

**Before:** The earlier target-specific parser and defaults were implemented here.

**After:** Uses shared indexed configuration/metric-series/readiness predicates, keeps exact target bindings and reports bounded construction uncertainty.

**Why:** Provider-neutral rules should not drift between targets; concrete environment mapping stays here and supplied values stay private.

Changed declaration anchors: `TargetObservabilityConfigurationError`, `TargetReadinessObservationConfiguration`, `targetObservabilityBindings`, `Checked`, `emptyFailure`, `read`, `numberSource`, `providerSelection`, `observabilityConfigurationFromTargetEnvironment`, `readinessObservationFromTargetEnvironment`, `readinessConfiguration`, `createTargetObservabilityRuntime` (4 more in source).

New declarations within this existing file: `targetObservabilityBindings`, `Checked`, `emptyFailure`, `read`, `numberSource`, `providerSelection`, `observabilityConfigurationFromTargetEnvironment`, `readinessConfiguration` (4 more in source).

Added import edges: `@kanbien/core/config`, `@kanbien/core`, `@kanbien/core/diagnostics`.

Declarations removed or relocated: `observabilityDeliveryBoundary`, `requiredString`, `requiredBoundedName`, `positiveInteger`, `metricSeriesFromEnvironment`, `metricSeriesDefinition`, `isRecord`, `stringField`, `numberField`, `stringArrayField` (2 more in source). Read the current exports/consumer tests before assuming the public API was removed.

Connected review context (`target-observability-configuration`; this review may span several files): Explicit environment bindings and legacy Number/disabled-provider behavior compose pure shared/provider validation, safe indexed records and independent construction uncertainty. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `persistence-composition`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=af94286aee5490eb5404a81469339d784c7579dc29c2cfdaf3c80ac6068d5e0e after=bf274867e5eac7b5abe9bc1066388e4489bcd75aeb7af71333b79d4755f28ab1 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-persistence.ts -->

### kanbien-platform-persistence.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-persistence.ts) · **Snapshot:** modified existing file; 20 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Compose Kanbien staging DynamoDB persistence seams for harmless smoke acceptance, durable outbox relay, and duplicate-safe worker processing.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `KanbienPlatformSmokePersistenceOptions`, `createKanbienPlatformOutboxRelay`, `createKanbienPlatformDurableWorkerProcessing`, `reportKanbienPlatformPersistenceStartupDiagnostic` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Actual target-owned product staging retains three-write ordering while adapter sources reach invocation-local writers, background observer bridges and selected startup reporting. Compiled consumers assert receivers, profile opt-outs, actual startup/runtime context, raw constructor failures, exact SDK/queue send counts and private-value exclusion.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `KanbienPlatformSmokePersistenceOptions`, `createKanbienPlatformOutboxRelay`, `createKanbienPlatformDurableWorkerProcessing`, `reportKanbienPlatformPersistenceStartupDiagnostic`.

New declarations within this existing file: `reportKanbienPlatformPersistenceStartupDiagnostic`.

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `@kanbien/platform-observability`.

Owning registered proof: `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=545d1c1da6c6c93663051e028b379902e3722f080ed42c0788365f28f68a2cb7 after=43816f8a952bd596ccf9347c820b73e46686f7fd87aeb2a9b3a98a79a27a0932 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts -->

### kanbien-platform-postgresql-bootstrap.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts) · **Snapshot:** modified existing file; 2 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements the owning core-server composition and one-shot programs command or helper.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `main` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Relational task configuration and injected secret guards emit exact fixed logical settings/reasons through existing catches on stderr. Known master/migration/runtime/generic roles avoid arbitrary secret-name disclosure.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `main`.

Added import edges: `./kanbien-platform-configuration-diagnostics`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=a2a99d4e241129fb2e0feb4b2713dfe67bbfc9e2e5d9e457cf00a83ef9354100 after=4e80a21b5877d36faf06725ab3f0d597488ee950d9fe95acb5b44067d4eb63e5 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-migration.main.ts -->

### kanbien-platform-postgresql-migration.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-migration.main.ts) · **Snapshot:** modified existing file; 22 added / 7 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements the owning core-server composition and one-shot programs command or helper.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `main` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Relational task configuration and injected secret guards emit exact fixed logical settings/reasons through existing catches on stderr. Known master/migration/runtime/generic roles avoid arbitrary secret-name disclosure.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `main`.

Added import edges: `./kanbien-platform-configuration-diagnostics`, `./kanbien-platform-postgresql-operation-diagnostics`, `@kanbien/platform-persistence`, `./kanbien-platform-delivery-diagnostics`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=3307db04e9b43e91978ad85231db9dd2ac2db41c3fd6c88c1dc0b7aa5078fbec after=89ecd516d28cba09841b69914e205ee2a8f92a5d8e3901c25e73d20dd5979cb2 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-operation-diagnostics.ts -->

### kanbien-platform-postgresql-operation-diagnostics.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-operation-diagnostics.ts) · **Snapshot:** added (absent from baseline); 107 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Owns relational platform-target composition operation records.

**Before:** No separate target catalog existed for these concrete composition predicates.

**After:** Distinguishes schema/configuration/writer/input/staging predicates and invocation boundaries with selected Persistence sources.

**Why:** Target composition facts are not generic PostgreSQL policy, and the existing task consumers must preserve the selected evidence.

Changed declaration anchors: `persistenceCompositionBoundaryDiagnostic`, `kanbienPlatformPostgreSqlOperationDiagnosticCatalog`, `CompositionBoundaryDetail`, `KanbienPlatformPostgreSqlDiagnosticContext`, `KanbienPlatformPostgreSqlDiagnosticOptions`, `catalogs`, `nativeThen`, `isolate`, `observeKanbienPlatformPostgreSql`, `reportKanbienPlatformPostgreSqlDiagnostic`, `compositionBoundaryRecord`, `reportKanbienPlatformPostgreSqlTaskDiagnostic` (1 more in source).

Added import edges: `@kanbien/core`, `@kanbien/core/diagnostics`, `@kanbien/platform-contracts`, `@kanbien/platform-observability`, `@kanbien/platform-persistence`, `@kanbien/platform-adapter-aws-persistence-postgresql`, `@kanbien/platform-security`, `@kanbien/platform-config`, `./kanbien-platform-configuration-diagnostics`.

Connected review context (`relational-postgresql-operation-binding`; this review may span several files): A separate target-owned composition catalog observes the actual PostgreSQL schema/configuration/writer/input/statement-staging boundary without coupling target configuration or queue vocabulary. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=b0e4f7ff4f92b98f2296ade7c1433b90dfb3a8880071cec39c5505ade5fd8cea -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence.ts -->

### kanbien-platform-postgresql-persistence.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence.ts) · **Snapshot:** modified existing file; 48 added / 10 removed lines. These are textual counts, not a count of new features.

**What it does:** Compose the harmless platform-smoke work-item persistence seam with the PostgreSQL adapter for disposable and later staging reference proofs.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `kanbienPlatformSmokePostgreSqlMigration`, `createKanbienPlatformPostgreSqlSmokePersistence`, `platformSmokeWorkItemInsert`, `platformSmokeWorkItemTable` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): A separate target-owned composition catalog observes the actual PostgreSQL schema/configuration/writer/input/statement-staging boundary without coupling target configuration or queue vocabulary. Real task consumers select the catalog and independently deliver own plus selected selected source primary plus eight related records.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `kanbienPlatformSmokePostgreSqlMigration`, `createKanbienPlatformPostgreSqlSmokePersistence`, `platformSmokeWorkItemInsert`, `platformSmokeWorkItemTable`.

Added import edges: `./kanbien-platform-postgresql-operation-diagnostics`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=98402fd7e96fac297e682949c18ba7d8b7163b9b44a5b980263c7b674a6b032f after=83523d64135e15048f3dd5c5c04898269c31082c7ab03b35235b6eac6a52ca5d -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-relay.main.ts -->

### kanbien-platform-postgresql-relay.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-relay.main.ts) · **Snapshot:** modified existing file; 39 added / 10 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements the owning core-server composition and one-shot programs command or helper.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `main`, `requiredEnvironment` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Relational task configuration and injected secret guards emit exact fixed logical settings/reasons through existing catches on stderr. Known master/migration/runtime/generic roles avoid arbitrary secret-name disclosure.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `main`, `requiredEnvironment`.

Added import edges: `./kanbien-platform-configuration-diagnostics`, `./kanbien-platform-delivery-diagnostics`, `./kanbien-platform-persistence`, `@kanbien/core/monitoring`, `./kanbien-platform-postgresql-operation-diagnostics`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=fa1ef323cb35528f960f3f376aabd048d04311fcf2039c2267c1ce0db4e61af8 after=da55104535f9ed02173fd1f8a34556c63c7450c7fb6ec21198660bda9f4f2243 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-restore-verify.main.ts -->

### kanbien-platform-postgresql-restore-verify.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-restore-verify.main.ts) · **Snapshot:** modified existing file; 8 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements the owning core-server composition and one-shot programs command or helper.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `main`, `databaseErrorCode`, `restoreHostFromEnvironment` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Relational task configuration and injected secret guards emit exact fixed logical settings/reasons through existing catches on stderr. Known master/migration/runtime/generic roles avoid arbitrary secret-name disclosure.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `main`, `databaseErrorCode`, `restoreHostFromEnvironment`.

Added import edges: `./kanbien-platform-configuration-diagnostics`, `./kanbien-platform-postgresql-operation-diagnostics`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=9d0ccad10c18731b15b5bdf40723a079751d811b8bd2d69d96c0f81bb3622b83 after=0f9994c4ce0cb906cec028bdae9c24c06623aa4d676ea714f58d396e695b1380 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-task.ts -->

### kanbien-platform-postgresql-task.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-task.ts) · **Snapshot:** modified existing file; 55 added / 35 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements the owning core-server composition and one-shot programs command or helper.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `secretFromEnvironment`, `credentialsFromEnvironment`, `configurationFromEnvironment`, `connectionConfiguration`, `closePool`, `secretObjectFromEnvironment`, `credentialsFromSecret` (3 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Relational task configuration and injected secret guards emit exact fixed logical settings/reasons through existing catches on stderr. Known master/migration/runtime/generic roles avoid arbitrary secret-name disclosure.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `secretFromEnvironment`, `credentialsFromEnvironment`, `configurationFromEnvironment`, `connectionConfiguration`, `closePool`, `secretObjectFromEnvironment`, `credentialsFromSecret`, `stringField`, `numberField`, `relationalConfigurationError`.

New declarations within this existing file: `relationalConfigurationError`.

Added import edges: `./kanbien-platform-configuration-diagnostics`, `@kanbien/platform-persistence`, `./kanbien-platform-postgresql-operation-diagnostics`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=90b5810de09068fb1f639d15dbe2a16b11ec46dfd55f2e5e96b339fdfa5f050a after=a6c61609eaeb8c3c821bebdae45dee7604498a572b7c26b1dd417932aec9e299 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-worker.main.ts -->

### kanbien-platform-postgresql-worker.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-worker.main.ts) · **Snapshot:** modified existing file; 50 added / 12 removed lines. These are textual counts, not a count of new features.

**What it does:** Implements the owning core-server composition and one-shot programs command or helper.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `main`, `payloadOutboxEntryId`, `requiredEnvironment` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Relational task configuration and injected secret guards emit exact fixed logical settings/reasons through existing catches on stderr. Known master/migration/runtime/generic roles avoid arbitrary secret-name disclosure.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `main`, `payloadOutboxEntryId`, `requiredEnvironment`.

Added import edges: `./kanbien-platform-configuration-diagnostics`, `./kanbien-platform-delivery-diagnostics`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=343bbcf65d1a1a6786e8d551db456a8e0d7a3f4c0572d2ab89ac2f2f6ac555ee after=b820e9fc230e1df34bf207c5658a4b1af2692eb87393d001ceec60ab7d6d5568 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-relay.main.ts -->

### kanbien-platform-relay.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-relay.main.ts) · **Snapshot:** modified existing file; 34 added / 16 removed lines. These are textual counts, not a count of new features.

**What it does:** Run one bounded Kanbien staging durable-outbox relay pass through the selected DynamoDB and SQS adapters.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `TargetRelayConfigurationError`, `runKanbienPlatformRelayMain`, `relayConfigurationFromTargetEnvironment`, `relayLeaseOwnerFromTargetEnvironment`, `requiredString`, `boundedPositiveInteger`, `relayConfigurationError` (1 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Target-owned logical environment/provider/lease bindings use upstream checked factories; arbitrary metadata fetch/JSON/status/identity/derivation failures retain unknown cause and actual phase. Local URL/hostname/brand predicates remain configuration, source calls/read order and historical exits/summaries are preserved.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `TargetRelayConfigurationError`, `runKanbienPlatformRelayMain`, `relayConfigurationFromTargetEnvironment`, `relayLeaseOwnerFromTargetEnvironment`, `requiredString`, `boundedPositiveInteger`, `relayConfigurationError`, `writeStartupFailure`.

Added import edges: `@kanbien/core/diagnostics`, `./kanbien-platform-configuration-diagnostics`, `./kanbien-platform-delivery-diagnostics`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=d5259d03c0b50d7b708be335272f9aa3e3ef1860e576f8c6c2135648ad5d94b2 after=9a52af9dc67c6a72be567484e75e78a401784237d878d7fc35f2eeba2b898e89 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts -->

### kanbien-platform-server.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.ts) · **Snapshot:** modified existing file; 42 added / 22 removed lines. These are textual counts, not a count of new features.

**What it does:** Start the platform server shell with the Kanbien Platform product app composition.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `TargetRuntimeConfigurationError`, `runKanbienPlatformServerMain`, `authenticationFromTargetEnvironment`, `runtimeConfigurationFromTargetEnvironment`, `productOptionsFromTargetEnvironment`, `rateLimiterFromTargetEnvironment`, `clientAddressResolverFromTargetEnvironment` (2 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Target server now binds exact provider/exposure/transport/persistence settings and retains selected Core/config/contracts/security/observability/server/worker/persistence/target primary and companions. Safe early reporting precedes unchanged legacy startup summaries; no supplied value or raw provider message becomes diagnostic detail.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `TargetRuntimeConfigurationError`, `runKanbienPlatformServerMain`, `authenticationFromTargetEnvironment`, `runtimeConfigurationFromTargetEnvironment`, `productOptionsFromTargetEnvironment`, `rateLimiterFromTargetEnvironment`, `clientAddressResolverFromTargetEnvironment`, `transportFromTargetEnvironment`, `targetRuntimeConfigurationError`.

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/platform-persistence`, `./kanbien-platform-configuration-diagnostics`.

Owning registered proof: `shell-package-source`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=24ce0a06e3ddad5ffec7099802f564b5f735ed3d38f487a784524018b280fd16 after=6e970686fe924a5b4a769c29edb8457db4c327f4ea12c8414e601f5b92fd0963 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-task-lease-owner.ts -->

### kanbien-platform-task-lease-owner.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-task-lease-owner.ts) · **Snapshot:** modified existing file; 27 added / 13 removed lines. These are textual counts, not a count of new features.

**What it does:** Derive a non-sensitive unique durable lease owner for one Kanbien staging Fargate task.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `TargetTaskLeaseOwnerError`, `targetTaskLeaseOwnerFromEnvironment`, `taskLeaseOwnerFromFargateMetadata`, `taskLeaseOwnerSourceError`, `taskLeaseOwnerError` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Target-owned logical environment/provider/lease bindings use upstream checked factories; arbitrary metadata fetch/JSON/status/identity/derivation failures retain unknown cause and actual phase. Local URL/hostname/brand predicates remain configuration, source calls/read order and historical exits/summaries are preserved.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `TargetTaskLeaseOwnerError`, `targetTaskLeaseOwnerFromEnvironment`, `taskLeaseOwnerFromFargateMetadata`, `taskLeaseOwnerSourceError`, `taskLeaseOwnerError`.

New declarations within this existing file: `taskLeaseOwnerSourceError`.

Added import edges: `@kanbien/core/diagnostics`, `./kanbien-platform-configuration-diagnostics`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ef7fb68b26b7c117d6a1e9bf1a7d8142f6a13adafc81bdfe658f935813de0137 after=ac8083d3cbe8842436753c4caa50b0343b4dd2d57253f8b4639a22c44e90a4b6 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/kanbien-platform-worker.main.ts -->

### kanbien-platform-worker.main.ts

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-worker.main.ts) · **Snapshot:** modified existing file; 62 added / 19 removed lines. These are textual counts, not a count of new features.

**What it does:** Run the Kanbien Platform product's declared jobs through the selected staging SQS delivery adapter and optional durable outbox-processing seam.

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `TargetWorkerConfigurationError`, `runKanbienPlatformWorkerMain`, `workerConfigurationFromTargetEnvironment`, `oneShotSuccessfulDeliveryLimit`, `durableOutboxProcessingFromTargetEnvironment`, `durableLeaseOwnerFromTargetEnvironment`, `durableLeaseDurationFromTargetEnvironment` (4 more in source) at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): The worker reports the exact validated observability configuration record through the selected internal catalog and preserves its legacy outward startup code before polling. Worker composition also retains exact queue/provider/backoff/exit-limit/persistence/lease/source diagnostics through its safe startup wrapper.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `TargetWorkerConfigurationError`, `runKanbienPlatformWorkerMain`, `workerConfigurationFromTargetEnvironment`, `oneShotSuccessfulDeliveryLimit`, `durableOutboxProcessingFromTargetEnvironment`, `durableLeaseOwnerFromTargetEnvironment`, `durableLeaseDurationFromTargetEnvironment`, `pollUntilStopped`, `positiveInteger`, `targetWorkerConfigurationError`, `writeStartupFailure`.

Added import edges: `@kanbien/core/diagnostics`, `@kanbien/platform-workers`, `./kanbien-platform-configuration-diagnostics`, `./kanbien-platform-delivery-diagnostics`.

Owning registered proof: `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=4610927ad950a1c4a07fb162bf5d690b26825acd6a2f1bbe4b93cf967dd96a00 after=13463992fb3b2b97bd357ef6ab5ae9b0e83b54a3aa3c8ea26c435058ecfc9d45 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which fact can the target add that a provider-neutral Core package must not hard-code?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No SQL, database privilege, authentication rule, extra retry or administration action is authorized by diagnostic reporting. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../infra/04.deploy/03.product/entrypoints) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L090 infra/04.deploy/03.product/entrypoints/contracts](090-03-product-entrypoints-contracts.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 30 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
