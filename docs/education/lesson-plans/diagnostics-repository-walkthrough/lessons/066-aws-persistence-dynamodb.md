<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l066
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/persistence/dynamodb.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L066 — platform/adapters/aws/persistence/dynamodb

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/persistence/dynamodb -->

## What you will understand

This adapter stores Platform records, outbox entries, claims and lineage using DynamoDB commands and existing transaction semantics.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a supported conditional rejection with a generic thrown object bearing a plausible message. The former may support the declared condition classification; the latter must not be promoted into that conclusion.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The adapter already performed these commands, but local configuration, stored attributes, condition failures and invocation failures could collapse into broad persistence errors.

**After:** Bounded observations identify the existing command or stored-field location and distinguish supported condition evidence from unknown invocation failures. Source companions survive selected wrappers.

**Why this was needed:** A condition rejection is not the same thing as inability to read the response. Incorrectly claiming absence or conflict can cause an agent to choose an unsafe recovery.

This directory contains `documentation`, `compiler` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/persistence/dynamodb/README.md -->

### README.md

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/README.md) · **Snapshot:** modified existing file; 25 added / 7 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for dynamodb persistence; read the sections `AWS DynamoDB Persistence Adapter`, `The table model`, `Conditions make concurrent changes safe`, `Transaction boundary—and its current limit`, `DynamoDB limits and target responsibilities`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `AWS DynamoDB Persistence Adapter`; `The table model`; `Conditions make concurrent changes safe`; `Transaction boundary—and its current limit`; `DynamoDB limits and target responsibilities`; `Bounded provider diagnostics`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=d7ef3579f16ed6db150e4c503aa70058b5bcc9049db0a1f828d4b35df5e92110 after=82b66256cc8c8617572e081cf021d9b2bf43623d3242efb32ab2208debb695a7 -->

<!-- course-file: platform/adapters/aws/persistence/dynamodb/tsconfig.runtime-test.json -->

### tsconfig.runtime-test.json

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/tsconfig.runtime-test.json) · **Snapshot:** modified existing file; 2 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Configures which sources/dependencies the test compiler can resolve.

**Before:** The existing compiler scope did not include all newly referenced diagnostic/security dependencies.

**After:** Extends the relevant compilation inputs or aliases for the tests; the JSON diff is the exact declaration change.

**Why:** Runtime tests must exercise the implementation that consumers actually import, rather than fail resolution or omit the new modules.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=78136121e9c31a4f330b81633e5cac1681d40e55fb1b9f408e35051fab27dcca after=726141ba1c78c9fbc9cb8d507a8ec27d18463ee3ed028f636c34673affd4f19b -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Can a malformed stored record be diagnosed without copying its attribute values into logs?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Existing key layouts, transaction behavior and command order are not redesigned by this work. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/persistence/dynamodb) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L063 platform/adapters/aws/persistence/postgresql](063-aws-persistence-postgresql.md) · [L067 platform/adapters/aws/persistence/dynamodb/src](067-persistence-dynamodb-src.md) · [L068 platform/adapters/aws/persistence/dynamodb/tests](068-persistence-dynamodb-tests.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
