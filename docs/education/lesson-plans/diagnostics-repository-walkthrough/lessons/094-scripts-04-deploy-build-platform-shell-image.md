<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l094
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/build-platform-shell-image.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L094 — scripts/04.deploy/build-platform-shell-image

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/build-platform-shell-image -->

## What you will understand

Build and image tooling turns source into a runnable artifact. The payload is the compiled files and dependencies actually included in that artifact.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **7 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Remove either core-server diagnostic module from an assembled test payload. The import-closure check must reject it with its fixed code. A Dockerfile mentioning a source file is not, by itself, proof that the resulting image runs.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work.

**After:** Packaging includes required diagnostic modules and checks actual import closure. Existing registered checks are reused with source identity, and omission counterexamples prove missing modules are caught.

**Why this was needed:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

This directory contains `implementation`, `test` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/build-platform-shell-image/check-source.sh -->

### check-source.sh

[Open current source](../../../../../scripts/04.deploy/build-platform-shell-image/check-source.sh) · **Snapshot:** modified existing file; 10 added / 5 removed lines. These are textual counts, not a count of new features.

**What it does:** Run the existing product, server and assembled runtime-payload checks before packaging.

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Verification orchestration requests the registered server, product and compiled-payload units through the existing trusted local runner. Closed arguments, failure propagation and aggregate child-contract/input/runtime bindings preserve the source preflight without adding runtime diagnostics or deployment authority.

**Why:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

Owning registered proof: `diagnostic-catalog-readers`, `shell-package-source`, `check-selection-mechanics`, `check-selection-repository-contracts`, `bootstrap-payload-regression`, `persistence-payload-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=34ffb556445df3289e2b331fcdaaa140cebe3f393c57941bbffd36156b4f5d87 after=766d24c213dc81bcae7a49443ea7a948b180b7ea1e1f0e19a5d8957cc5b69006 -->

<!-- course-file: scripts/04.deploy/build-platform-shell-image/configuration-diagnostic-test.mjs -->

### configuration-diagnostic-test.mjs

[Open current source](../../../../../scripts/04.deploy/build-platform-shell-image/configuration-diagnostic-test.mjs) · **Snapshot:** added (absent from baseline); 411 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for assembled image and payload safety.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Actual blank/oversized table/index predicates bind persistence-owned closed fields. entries/getter order, first failure, historical tableName detail for oversized indices and missing-to-empty target reduction remain, without inventing absent-value evidence.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `verifyTargetConfigurationDiagnostics`, `verifyLeaseOwnerSourceDiagnostics`, `verifySqsConstructorConfigurationDiagnostics`, `verifyTargetNumericGuardInvocationCounts`, `verifySqsBridgeSelection`.

Added import edges: `node:assert/strict`, `node:child_process`, `node:path`, `node:url`, `node:module`, `node:crypto`.

Owning registered proof: `platform-persistence-runtime`, `diagnostic-catalog-readers`, `shell-package-source`, `platform-shell-payload`, `sqs-queue-runtime`, `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=aa7bfc954bb374b0f3f2ad652f45f546bd46f417846ea3a712ef21a12a865a56 -->

<!-- course-file: scripts/04.deploy/build-platform-shell-image/delivery-diagnostic-test.mjs -->

### delivery-diagnostic-test.mjs

[Open current source](../../../../../scripts/04.deploy/build-platform-shell-image/delivery-diagnostic-test.mjs) · **Snapshot:** added (absent from baseline); 651 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for assembled image and payload safety.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Relational task configuration and injected secret guards emit exact fixed logical settings/reasons through existing catches on stderr. Known master/migration/runtime/generic roles avoid arbitrary secret-name disclosure.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `entry`, `expectedOutbox`, `record`, `own`, `observed`, `scope`, `capture`, `environment`, `deferred`, `bounded`, `verifyTargetDeliveryDiagnostics` (13 more in source).

Added import edges: `node:assert/strict`, `node:module`, `node:path`.

Owning registered proof: `platform-shell-payload`, `diagnostic-catalog-readers`, `platform-contracts-runtime`, `platform-observability-runtime`, `persistence-composition`, `shell-package-source`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=16769665890535012991badd094bd321b7c525694d644409116eb0e96a3e7e54 -->

<!-- course-file: scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs -->

### prepare-runtime.mjs

[Open current source](../../../../../scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs) · **Snapshot:** modified existing file; 17 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Prepare CommonJS package shims for the platform shell image runtime payload.

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `preparationPhase`, `preparationLocation`, `writePackageShim` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Expose the public security package's actual Core security dependency in all three prepared runtime payloads; derive missing core exports from compiled imports and reject them before image construction. B10 preserves these exact physical owners and bounds image-script child execution; direct preparation/verification CLI native failures remain separately reviewable.

**Why:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

Changed declaration anchors: `preparationPhase`, `preparationLocation`, `writePackageShim`.

New declarations within this existing file: `preparationPhase`, `preparationLocation`.

Declarations removed or relocated: `coreModules`. Read the current exports/consumer tests before assuming the public API was removed.

Owning registered proof: `bootstrap-payload-regression`, `persistence-payload-regression`, `shell-package-source`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=cd6eba6a4002ce2d6df53e1a6b5e510148ddad08fa6a34c76de4159ebd17dddd after=130a02008092bc9783d26ebff4b6638dbff99999fd1a889df08a2a76a1d6c8ef -->

<!-- course-file: scripts/04.deploy/build-platform-shell-image/process-diagnostic-test.mjs -->

### process-diagnostic-test.mjs

[Open current source](../../../../../scripts/04.deploy/build-platform-shell-image/process-diagnostic-test.mjs) · **Snapshot:** added (absent from baseline); 279 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for assembled image and payload safety.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): The bootstrap target's existing release-verification profile declares the exact Server-owned finite error classes through its real production dependency. Constant declaration guards, route, HTTP response and process startup/close behavior are unchanged.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `canary`, `record`, `selectedState`, `failedStep`, `capture`, `environment`, `diagnostics`, `verifyTargetProcessDiagnostics`, `verifyDynamoConstructorTargets`, `verifyCorePersistenceStartup`, `verifyEcsConstructorTarget`, `verifyEcsProcessDiagnostics`.

Added import edges: `node:assert/strict`, `node:module`, `node:path`, `./delivery-diagnostic-test.mjs`.

Owning registered proof: `persistence-composition`, `platform-shell-payload`, `diagnostic-catalog-readers`, `shell-package-source`, `platform-runtime-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `ecs-fargate-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=19b50f8499bf720f1dbccab1cb64486a925f3ec7644e43813f80dcc016898e60 -->

<!-- course-file: scripts/04.deploy/build-platform-shell-image/script.sh -->

### script.sh

[Open current source](../../../../../scripts/04.deploy/build-platform-shell-image/script.sh) · **Snapshot:** modified existing file; 5 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Build the platform shell container image from the governed infra image boundary.

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Retain image selection/build/package/HTTP/metric/relational predicates and cleanup order. Fixed child concern/stage summaries replace raw consequential command failures, including the previously suppressed builder result; output is excluded without changing child counts/status or successful control flow.

**Why:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

Owning registered proof: `package-custody-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=149a9ab9746834db997ebeac61c2dddb901326146d0ff0d396182b2dd76f4283 after=f568dc67f05f4ac820bba6cc6a3b3e1da31c85bc3fa62e31ea52fa2907c1b8d8 -->

<!-- course-file: scripts/04.deploy/build-platform-shell-image/verify-runtime-payload.mjs -->

### verify-runtime-payload.mjs

[Open current source](../../../../../scripts/04.deploy/build-platform-shell-image/verify-runtime-payload.mjs) · **Snapshot:** modified existing file; 142 added / 4 removed lines. These are textual counts, not a count of new features.

**What it does:** Prove the compiled platform shell payload starts with its generated package shims rather than workspace TypeScript sources.

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work. In this file the change is localized by the symbols and source comparison below.

**After:** Updates `verifyCompiledPersistenceComposition`, `verifyCompiledStoreObserverBridges`, `verifySecurityConfigurationRetention`, `verifyObservabilityConfigurationRetention` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Preserve provider-neutral authentication observations; distinguish absent/empty settings, JSON/container/entry failures, exact missing or wrong-type mapping attributes and permission item index without exposing configured values.

**Why:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

Changed declaration anchors: `verifyCompiledPersistenceComposition`, `verifyCompiledStoreObserverBridges`, `verifySecurityConfigurationRetention`, `verifyObservabilityConfigurationRetention`.

New declarations within this existing file: `verifyCompiledStoreObserverBridges`, `verifySecurityConfigurationRetention`, `verifyObservabilityConfigurationRetention`.

Added import edges: `node:assert/strict`, `./configuration-diagnostic-test.mjs`, `./process-diagnostic-test.mjs`.

Owning registered proof: `security-cognito-diagnostics`, `shell-package-source`, `security-shared-rate-limit-diagnostics`, `platform-server-runtime`, `platform-shell-payload`, `persistence-composition`, `diagnostic-catalog-readers`, `core-dependency-boundary`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=01b7a2c4f3c7b964eb2c2998e7da04e4261e3b788769defc2e379330ad3f0536 after=acac4de90d6628832104c1b46f70a0c4a91e5df5a4d052f56456f69f0a17de5a -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why could TypeScript compilation pass while the deployed image fails at startup?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local image qualification is not publication, target alignment or live acceptance. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/build-platform-shell-image) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L110 scripts/04.deploy/smoke-test-platform-shell-image](110-scripts-04-deploy-smoke-test-platform-shell-image.md) · [L111 scripts/04.deploy/validate-container-boundaries](111-scripts-04-deploy-validate-container-boundaries.md) · [L112 scripts/04.deploy/inventory-deploy-control](112-scripts-04-deploy-inventory-deploy-control.md) · [L127 scripts/04.deploy](127-scripts-04-deploy.md) · [L152 scripts/04.deploy/reconcile-platform-shell-staging](152-scripts-04-deploy-reconcile-platform-shell-staging.md) · [L153 scripts/04.deploy/shared](153-scripts-04-deploy-shared.md) · [L155 scripts/04.deploy/verify-platform-shell-deploy-readiness](155-scripts-04-deploy-verify-platform-shell-deploy-readiness.md) · [L168 scripts/04.deploy/verify-platform-shell-deployment-workflow](168-scripts-04-deploy-verify-platform-shell-deployment-workflow.md) · [L169 scripts/04.deploy/verify-platform-shell-infrastructure](169-scripts-04-deploy-verify-platform-shell-infrastructure.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 7 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
