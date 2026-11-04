<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l063
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/persistence/postgresql.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L063 — platform/adapters/aws/persistence/postgresql

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/persistence/postgresql -->

## What you will understand

The PostgreSQL adapter implements Platform persistence against a relational database and binds connection, credentials, queries and transactions.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **4 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare an authentication-related native code with prose that merely says authentication failed. The classifier must rely on its supported machine evidence or retain unknown. Compare a pool query failure with cleanup end failing afterward; preserve the original outcome.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** PostgreSQL support, TLS, IAM-token support and persistence operations already existed. Native errors and generic wrappers did not always preserve precise safe evidence.

**After:** The adapter observes configuration, credential, connect/query/transaction/cleanup boundaries and uses declared machine signals where available. Shared Security owns certificate/TLS meanings; Persistence supplies operation context.

**Why this was needed:** A certificate syntax error, rejected authentication and failed SQL invocation need different investigation. Raw provider messages may contain SQL, addresses or identities and are not a safe diagnostic contract.

This directory contains `documentation`, `dependency`, `compiler` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/persistence/postgresql/README.md -->

### README.md

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/README.md) · **Snapshot:** modified existing file; 28 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for postgresql: provider evidence; read the sections `AWS PostgreSQL Persistence Adapter`, `How the atomic seam is used`, `Safety boundary`, `Failure diagnostics`, `Tests and evidence`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `AWS PostgreSQL Persistence Adapter`; `How the atomic seam is used`; `Safety boundary`; `Failure diagnostics`; `Tests and evidence`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=70c8896b40d8c30ffcec0ba7eb9a31fe59fa215eb07344a7843b8c7776a08a88 after=da8afc8cf6b7f60f77b42353fe1c05beecae82978f02b49d88666d329680ee31 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/package.json -->

### package.json

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/package.json) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Declares package dependencies used by the changed code.

**Before:** The package did not declare the newly added internal import edge(s).

**After:** Adds `@kanbien/platform-security` to the package graph.

**Why:** Explicit dependencies keep source imports, build resolution and packaged runtime agreement honest. This is not an unrelated library installation.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=6fdf974febbf2965d907bcf407006c164eb12a6d0fb67894d94c348c40f5d47a after=78b98d00369cebf552ffbe65f04c9f7b573d2ae365fdac8099d1f1c9f797625a -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/tsconfig.integration-test.json -->

### tsconfig.integration-test.json

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/tsconfig.integration-test.json) · **Snapshot:** modified existing file; 6 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Configures which sources/dependencies the test compiler can resolve.

**Before:** The existing compiler scope did not include all newly referenced diagnostic/security dependencies.

**After:** Extends the relevant compilation inputs or aliases for the tests; the JSON diff is the exact declaration change.

**Why:** Runtime tests must exercise the implementation that consumers actually import, rather than fail resolution or omit the new modules.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=305264e093c56baaf5cdef2ffc377aaa01563e4c66e02f259b043ffd1193b6d7 after=9e87c2eef862c4c27b41bda01fd0982f4b63a50e2002432539d62aa59295a143 -->

<!-- course-file: platform/adapters/aws/persistence/postgresql/tsconfig.runtime-test.json -->

### tsconfig.runtime-test.json

[Open current source](../../../../../platform/adapters/aws/persistence/postgresql/tsconfig.runtime-test.json) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Configures which sources/dependencies the test compiler can resolve.

**Before:** The existing compiler scope did not include all newly referenced diagnostic/security dependencies.

**After:** Extends the relevant compilation inputs or aliases for the tests; the JSON diff is the exact declaration change.

**Why:** Runtime tests must exercise the implementation that consumers actually import, rather than fail resolution or omit the new modules.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=2fd3f2ee3cd96e02ab15d8a522ebbbe1dd53e8aabb11ffb3378b8c6872bc6d01 after=247260cbf1fe4dccd6bcddde20a68de4b16057e056a37e189fe3b3e32603d7bf -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why is matching an English error sentence less reliable than an explicitly supported native code?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Certificate parsing proves syntax, not peer identity, trust-chain validity or a successful live RDS connection. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/persistence/postgresql) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L064 platform/adapters/aws/persistence/postgresql/src](064-persistence-postgresql-src.md) · [L065 platform/adapters/aws/persistence/postgresql/tests](065-persistence-postgresql-tests.md) · [L066 platform/adapters/aws/persistence/dynamodb](066-aws-persistence-dynamodb.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 4 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
