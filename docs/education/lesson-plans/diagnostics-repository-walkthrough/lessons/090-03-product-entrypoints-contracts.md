<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l090
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder infra/04.deploy/03.product/entrypoints/contracts.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L090 — infra/04.deploy/03.product/entrypoints/contracts

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: infra/04.deploy/03.product/entrypoints/contracts -->

## What you will understand

Entrypoints assemble concrete settings, catalogs, adapters, reporters and programs. A one-shot program performs a task such as migration or verification and exits.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **6 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Follow a missing IAM username from its target binding through Core validation, the structured failure, selected catalog and safe task output to the Python reader. At no step is the username value required. Contrast source-read failure and permission proof rejection.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text.

**After:** Target bindings connect reusable definitions to actual settings and call boundaries. Administration/verifier observations preserve primary failure, bounded source companions, operation progress and existing SQL/privilege/cleanup behavior.

**Why this was needed:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

This directory contains `catalog` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: infra/04.deploy/03.product/entrypoints/contracts/diagnostics.v1.json -->

### diagnostics.v1.json

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/contracts/diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 417 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected core-server composition and one-shot programs contract for non-TypeScript readers, including 8 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `kanbien-core-server.configuration-invalid` v1, `kanbien-core-server.iam-configuration-invalid` v1, `kanbien-core-server.administrator-credentials-invalid` v1, `kanbien-core-server.certificate-source-invalid` v1, `kanbien-core-server.certificate-source-read-failed` v1; 3 more definitions are in the export.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=94cc3cfd7447cccb98f944d7aea521a9ba4d6bf729ce11152d5f63e2b36f3463 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-acceptance-diagnostics.v1.json -->

### kanbien-core-server-acceptance-diagnostics.v1.json

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-acceptance-diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 68 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected core-server composition and one-shot programs contract for non-TypeScript readers, including 1 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `kanbien-core-server.acceptance.request-invalid` v1.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=9d6be401e15fd04dcfb85c1c075c32219fbb7de79fe283ccf0fb959aeb5b78ed -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-persistence-operation-diagnostics.v1.json -->

### kanbien-core-server-persistence-operation-diagnostics.v1.json

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/contracts/kanbien-core-server-persistence-operation-diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 470 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected core-server composition and one-shot programs contract for non-TypeScript readers, including 4 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `kanbien-core-server.operations.administration-predicate-rejected` v1, `kanbien-core-server.operations.administration-boundary-failed` v1, `kanbien-core-server.operations.verification-predicate-rejected` v1, `kanbien-core-server.operations.verification-boundary-failed` v1.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=8d1689d49c4851c06309a1af1dd7b3baebfa96f58a1fe40ff219e3a58c15fbed -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-delivery-diagnostics.v1.json -->

### kanbien-platform-delivery-diagnostics.v1.json

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-delivery-diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 108 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected core-server composition and one-shot programs contract for non-TypeScript readers, including 1 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `kanbien-platform.delivery.boundary-observed` v1.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=34bf22de6af278b831260f440a783588e661810627e4e359954b5e3fe24298d8 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-diagnostics.v1.json -->

### kanbien-platform-diagnostics.v1.json

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 171 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected core-server composition and one-shot programs contract for non-TypeScript readers, including 2 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `kanbien-platform.configuration-invalid` v1, `kanbien-platform.lease-owner-source-failed` v1.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=70557f78b2a69b6326eacbe2c8461539130d5e629c2c7e38be456d832e8f76a1 -->

<!-- course-file: infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-postgresql-operation-diagnostics.v1.json -->

### kanbien-platform-postgresql-operation-diagnostics.v1.json

[Open current source](../../../../../infra/04.deploy/03.product/entrypoints/contracts/kanbien-platform-postgresql-operation-diagnostics.v1.json) · **Snapshot:** added (absent from baseline); 68 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Generated, machine-readable export of code-owned diagnostic definitions.

**Before:** This JSON export was absent from the baseline; that does not mean the capability itself was absent.

**After:** Exports the selected core-server composition and one-shot programs contract for non-TypeScript readers, including 1 definitions. Its values come from runtime code, not from a second manually invented taxonomy.

**Why:** Regeneration/freshness and compatibility checks keep readers aligned with the producer; manually editing this export would not be the normal way to change meaning.

Exported code examples: `kanbien-platform.postgresql.composition-boundary-failed` v1.

Proving boundary: compiled export freshness, retained-version compatibility and strict-reader tests in [diagnostic coverage tooling](../../../../../scripts/repo/diagnostic-coverage/README.md). Generated JSON alone does not establish producer behavior.

<!-- course-source-sha256: before=absent after=2879a47277b3134863c562790a12ed71d348f038f900b651d170d60801e6e7a1 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which fact can the target add that a provider-neutral Core package must not hard-code?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No SQL, database privilege, authentication rule, extra retry or administration action is authorized by diagnostic reporting. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../infra/04.deploy/03.product/entrypoints/contracts) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L089 infra/04.deploy/03.product/entrypoints](089-04-deploy-03-product-entrypoints.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 6 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
