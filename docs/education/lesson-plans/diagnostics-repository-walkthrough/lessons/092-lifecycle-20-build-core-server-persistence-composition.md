<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l092
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L092 — scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition -->

## What you will understand

Entrypoints assemble concrete settings, catalogs, adapters, reporters and programs. A one-shot program performs a task such as migration or verification and exits.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **8 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Follow a missing IAM username from its target binding through Core validation, the structured failure, selected catalog and safe task output to the Python reader. At no step is the username value required. Contrast source-read failure and permission proof rejection.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text.

**After:** Target bindings connect reusable definitions to actual settings and call boundaries. Administration/verifier observations preserve primary failure, bounded source companions, operation progress and existing SQL/privilege/cleanup behavior.

**Why this was needed:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

This directory contains `documentation`, `test`, `implementation`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/README.md -->

### README.md

[Open current source](../../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/README.md) · **Snapshot:** modified existing file; 22 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for core-server composition and one-shot programs; read the sections `Core-server persistence composition proof`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Core-server persistence composition proof`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=a657f760b530bbc5e0c4d8ea51488e7ced658cb827b5672f7ac7414997f070c5 after=f75a2b8781639e0b97643181dfa7d0c47a50d6fc7e97972d243abb61813ea710 -->

<!-- course-file: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs -->

### configuration-test.mjs

[Open current source](../../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs) · **Snapshot:** modified existing file; 504 added / 15 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for core-server composition and one-shot programs.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Validate already-parsed credential fields with exact value-free reasons; preserve accepted bytes and distinguish structural validation from actual database authentication.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `compiled`, `rejectedCases`, `taskDiagnostics`, `privateTaskDiagnosticRegression`, `certificateReadError`, `certificateSourceRegression`, `rejectedBeforePool`, `administratorCredentialRegression`, `administrationConfigurationRegression`, `iamConfigurationRegression`, `roleCredentialRegression`, `operationProducerRegression` (2 more in source).

New declarations within this existing file: `rejectedCases`, `taskDiagnostics`, `privateTaskDiagnosticRegression`, `certificateReadError`, `certificateSourceRegression`, `administratorCredentialRegression`, `administrationConfigurationRegression`, `iamConfigurationRegression` (2 more in source).

Added import edges: `./fixture-runtime.mjs`.

Owning registered proof: `persistence-composition`, `restore-connection-diagnostics`, `platform-shell-payload`, `deployment-operation-diagnostics-regression`, `diagnostic-catalog-readers`, `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=88f7b9fa681ed2710f7b9b210c026530b2c9f8e7fc50534c3836ab1fc7a2e166 after=e33bd13b9bfab9bdc7959aeb15a71f12c1630931b0fb19a1dc01d9271379ea67 -->

<!-- course-file: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-isolation-test.mjs -->

### fixture-isolation-test.mjs

[Open current source](../../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-isolation-test.mjs) · **Snapshot:** added (absent from baseline); 47 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for core-server composition and one-shot programs.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Verification-only helper gives each real fixture an independent copied module tree, fingerprints the immutable compiled baseline and cleans disposable payloads on process exit. Order/repetition, sibling mutation and child-failure cleanup are proved without claiming new operational diagnostics or container qualification.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `source`, `helper`.

Added import edges: `node:assert/strict`, `node:child_process`, `node:fs`, `node:os`, `node:path`.

Owning registered proof: `persistence-composition`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=c3c28e67d651d204e4bd82b47f28a8d0db5a343ae377c806dafc6628df1c3ebe -->

<!-- course-file: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-runtime.mjs -->

### fixture-runtime.mjs

[Open current source](../../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-runtime.mjs) · **Snapshot:** added (absent from baseline); 56 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Give each compiled persistence fixture a disposable independent module tree and clean it after failure or success.

**Before:** This implementation/helper file was absent at the baseline; its surrounding capability may already have existed.

**After:** Updates `fixtureRuntime`, `fixtureFingerprint` at this file's existing responsibility. Connected implementation context from the owner review (spanning related files): Verification-only helper gives each real fixture an independent copied module tree, fingerprints the immutable compiled baseline and cleans disposable payloads on process exit. Order/repetition, sibling mutation and child-failure cleanup are proved without claiming new operational diagnostics or container qualification.

**Why:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

Changed declaration anchors: `fixtureRuntime`, `fixtureFingerprint`.

Added import edges: `node:fs`, `node:crypto`, `node:os`, `node:path`, `node:url`.

Owning registered proof: `persistence-composition`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=ea2de5129b13eeddd83f7b0cb49e99d7307d4a961513bf98e4267b7a0ae8e98b -->

<!-- course-file: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/observability-runtime-test.mjs -->

### observability-runtime-test.mjs

[Open current source](../../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/observability-runtime-test.mjs) · **Snapshot:** modified existing file; 267 added / 11 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for core-server composition and one-shot programs.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Verification-only helper gives each real fixture an independent copied module tree, fingerprints the immutable compiled baseline and cleans disposable payloads on process exit. Order/repetition, sibling mutation and child-failure cleanup are proved without claiming new operational diagnostics or container qualification.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `compiled`, `records`, `failedReadiness`, `startupConfiguration`, `choiceCodes`, `startupChoices`, `diagnostic`, `expectedChoices`, `expectedOmissions`, `failure`, `healthFailure`, `exportFailures` (1 more in source).

New declarations within this existing file: `records`, `failedReadiness`, `startupConfiguration`, `choiceCodes`, `startupChoices`, `diagnostic`, `expectedChoices`, `expectedOmissions` (3 more in source).

Added import edges: `./fixture-runtime.mjs`, `@aws-sdk/rds-signer`, `@kanbien/platform-adapter-aws-observability-cloudwatch`.

Owning registered proof: `platform-contracts-runtime`, `platform-observability-runtime`, `platform-shell-payload`, `persistence-composition`, `diagnostic-catalog-readers`, `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `cloudwatch-observability-runtime`, `core-dependency-boundary`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=ecee98dc715eff231991525d5f70327d7db35e7230ee337ff40d50b7699b7ff8 after=6df6e44d517233f360048e43af5900753988d1d47a596fee6471921157b183b3 -->

<!-- course-file: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/restore-diagnostic-test.mjs -->

### restore-diagnostic-test.mjs

[Open current source](../../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/restore-diagnostic-test.mjs) · **Snapshot:** modified existing file; 69 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for core-server composition and one-shot programs.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Target-owned administration/role/credential/verifier observations identify actual predicates and call boundaries without SQL, credential, provider-message or identity values. The original rejected task is serialized first; bounded private own observations and complete selected source bundles follow independently, with explicit overflow occurrence counts.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `compiled`, `restoreCleanupRegression`.

New declarations within this existing file: `restoreCleanupRegression`.

Added import edges: `node:module`, `./fixture-runtime.mjs`.

Owning registered proof: `persistence-composition`, `restore-connection-diagnostics`, `platform-shell-payload`, `deployment-operation-diagnostics-regression`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f157857c424744ee133f144b538433dd7d97542a516f15f3a0242905cd2b9e15 after=9a4b77aa29d60e0027d4da94ad56755d61dab6e0503931e083ee1418ece69aee -->

<!-- course-file: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/runtime-test.mjs -->

### runtime-test.mjs

[Open current source](../../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/runtime-test.mjs) · **Snapshot:** modified existing file; 406 added / 5 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for core-server composition and one-shot programs.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Health-owned closed records distinguish returned degraded/unhealthy states, invocation throw, completion rejection, public projection failure and lifecycleReady=false without guessing a cause. Zero-based check indices avoid arbitrary names; actual upstream primary/related evidence is forwarded only for nonhealthy/projection-failure paths.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `buildOutput`, `proveAcceptanceRequestPredicates`, `acceptancePredicateRecord`, `proveAcceptanceDiagnosticDelivery`, `proveAcceptanceObserverIsolation`, `proveDetailedReadiness`, `proveHealthDiagnosticDelivery`, `proveHealthObservationSelection`, `proveUnavailableDependency`, `proveRuntimeIdentityRevocationAndRestoration`, `proveTaskVerifierDiagnostics`, `start` (1 more in source).

New declarations within this existing file: `proveAcceptanceRequestPredicates`, `acceptancePredicateRecord`, `proveAcceptanceDiagnosticDelivery`, `proveAcceptanceObserverIsolation`, `proveDetailedReadiness`, `proveHealthDiagnosticDelivery`, `proveHealthObservationSelection`, `proveTaskVerifierDiagnostics`.

Added import edges: `node:assert/strict`, `./fixture-runtime.mjs`, `node:crypto`.

Owning registered proof: `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `persistence-composition`, `diagnostic-catalog-readers`, `platform-shell-payload`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=708e9ceff8c5da950a77f31041cb0dde009de31c93313784b71a628c3601760d after=1b1897b9c820feda232c1e2750b7fa9e2bf0c14a2ec3e56cd9b9b0ad89d76059 -->

<!-- course-file: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh -->

### smoke-test.sh

[Open current source](../../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh) · **Snapshot:** modified existing file; 13 added / 8 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Owning registered proof: `persistence-composition`, `core-dependency-boundary`, `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=eb275046d0a31ec8b08bf8fed4baa057181ad9551905392a86874bb52d8d4833 after=ddb3788fa0e941b594cdcfcc7075aca2e7c186c82c163b485443dd4f3e814dbf -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which fact can the target add that a provider-neutral Core package must not hard-code?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No SQL, database privilege, authentication rule, extra retry or administration action is authorized by diagnostic reporting. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L095 scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary](095-lifecycle-20-build-core-server-dependency-boundary.md) · [L096 scripts/04.deploy/lifecycle/20-build/runnable-program-contract](096-lifecycle-20-build-runnable-program-contract.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 8 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
