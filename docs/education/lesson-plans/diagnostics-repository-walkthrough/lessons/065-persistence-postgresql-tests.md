<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l065
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/persistence/postgresql/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L065 — platform/adapters/aws/persistence/postgresql/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/persistence/postgresql/tests -->

## What you will understand

The PostgreSQL adapter implements Platform persistence against a relational database and binds connection, credentials, queries and transactions.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **5 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare an authentication-related native code with prose that merely says authentication failed. The classifier must rely on its supported machine evidence or retain unknown. Compare a pool query failure with cleanup end failing afterward; preserve the original outcome.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence.

**After:** The adapter observes configuration, credential, connect/query/transaction/cleanup boundaries and uses declared machine signals where available. Shared Security owns certificate/TLS meanings; Persistence supplies operation context.

**Why this was needed:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/persistence/postgresql/tests/postgresql-diagnostics.test.ts -->

### postgresql-diagnostics.test.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/tests/postgresql-diagnostics.test.ts) · **Snapshot:** modified existing file; 66 added / 6 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for postgresql: provider evidence.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Translate bounded machine-code, causal and actual-invocation evidence; recover observed phases through private wrappers, retain the existing primary classification precedence and attach selected shared-security observations only to TLS-classified failures. No provider fault, safe replay or schema/capacity cause is inferred.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `fixtureStage`, `lastSafeFacts`, `fixtureDeadlines`, `failedConnection`, `main`.

New declarations within this existing file: `fixtureStage`, `lastSafeFacts`, `fixtureDeadlines`.

Owning registered proof: `postgresql-connection-diagnostics`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=0566d3f2097cd84ce6e6a83d7ce06d45e71bd72b6198b354596c909b0b646556 after=d68f6077a04956aa344a0d95d7e0be0f9246e43f6abbc0c95ff05d782906141a -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/tests/postgresql-persistence-adapter-boundaries.test.mjs -->

### postgresql-persistence-adapter-boundaries.test.mjs

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/tests/postgresql-persistence-adapter-boundaries.test.mjs) · **Snapshot:** modified existing file; 2 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for postgresql: provider evidence.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): The optional existing persistence diagnostic port observes local telemetry encoding versus sink callback failure, consumes returned rejection without awaiting/replay, and independently retains selected selected source primary plus eight related records. A failed operation getter does not invent an owning operation.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `allowedSourceImportPattern`.

Owning registered proof: `postgresql-connection-diagnostics`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=791d2d2b9ccbba8c3c2d888735346b1b2e40d7c743ba9b4981c84a427f881c5d after=e167dff6fe7e105a3db9ae63879280898ebcc11540c61c48af90ab48ad45d790 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/tests/postgresql-persistence-adapter-runtime.test.ts -->

### postgresql-persistence-adapter-runtime.test.ts

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/tests/postgresql-persistence-adapter-runtime.test.ts) · **Snapshot:** modified existing file; 675 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for postgresql: provider evidence.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. The newly visible named cases below provide concrete reading anchors. Connected proving scope (the review spans related files, not only this test): Validate already-parsed credential fields with exact value-free reasons; preserve accepted bytes and distinguish structural validation from actual database authentication.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`, `details`, `boundaryDetail`, `sourceDefinition`, `sourceRecords`, `safeSource`, `telemetryObservations`, `boundaryObservations`, `atomicObservations`, `invocationDiagnostics`, `migrationObservations`, `rowsPool` (9 more in source).

New declarations within this existing file: `details`, `boundaryDetail`, `sourceDefinition`, `sourceRecords`, `safeSource`, `telemetryObservations`, `boundaryObservations`, `atomicObservations` (12 more in source).

Added import edges: `node:events`, `@kanbien/core/diagnostics`, `@kanbien/platform-security`, `../src/observations`.

Added named test anchors: `_`.

Owning registered proof: `postgresql-connection-diagnostics`, `diagnostic-catalog-readers`, `persistence-composition`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f27f4bb4773e7426d13d26bd85ad5adb2a9babe59a0094bea0c187abf3e4f269 after=d05caa067a693ea7ed3d87529e3f1177ccd7c451125be969cd4d1311f4949c6d -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/tests/run-local-integration-tests.mjs -->

### run-local-integration-tests.mjs

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/tests/run-local-integration-tests.mjs) · **Snapshot:** modified existing file; 5 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreModules`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=ec78ef91e9689f53b6079b4d355de3a1fa09e65a2dae84c70b870d399877e351 after=b64ca537aa998f65b39c7f63fd023eedeb826a9e8c94c45c89d591846d48853b -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 2 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreModules`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=8be2269fc8395ac1c295d0f3635da648d3d624b24099654e003d9f3ff529cf84 after=ed8b5eb7196b2d5fd8049f1753869d23054c4cd7726924a18b5feae58dd90a04 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why is matching an English error sentence less reliable than an explicitly supported native code?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Certificate parsing proves syntax, not peer identity, trust-chain validity or a successful live RDS connection. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/persistence/postgresql/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L063 platform/adapters/aws/persistence/postgresql](063-aws-persistence-postgresql.md) · [L064 platform/adapters/aws/persistence/postgresql/src](064-persistence-postgresql-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 5 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
