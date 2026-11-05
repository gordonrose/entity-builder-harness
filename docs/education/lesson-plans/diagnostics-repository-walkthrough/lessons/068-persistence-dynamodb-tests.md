<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l068
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/adapters/aws/persistence/dynamodb/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L068 — platform/adapters/aws/persistence/dynamodb/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/adapters/aws/persistence/dynamodb/tests -->

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

This directory contains `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/adapters/aws/persistence/dynamodb/tests/dynamodb-persistence-adapter-runtime.test.ts -->

### dynamodb-persistence-adapter-runtime.test.ts

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/tests/dynamodb-persistence-adapter-runtime.test.ts) · **Snapshot:** modified existing file; 388 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for dynamodb persistence.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. This suite uses function/assertion-driven cases; read the changed symbols or assertions at the linked source rather than assuming there are no tests because no test(...) names appear. Connected proving scope (the review spans related files, not only this test): Finite current command/selection/encoding/callback/response/decode and durable-state observations preserve legacy getter reads, codes/params, SDK receiver and selection-before-encoding, raw throws, write ordering/counts and race validation-without-write policy. Neutral conditions are not automatic errors; transaction cancellation alone does not establish cause.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Changed declaration anchors: `main`.

Added import edges: `@kanbien/core/diagnostics`, `../src/observations`.

Owning registered proof: `dynamodb-persistence-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6a6994bf4324bfa10ffa0b18e7b9f45feab74f06feabf795382809fb069b22d6 after=626fa68ebf7d0aa999226aca741d7bbdee7d39db1e8c2ca7a80643e395eeff41 -->

<!-- course-file: platform/adapters/aws/persistence/dynamodb/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../platform/adapters/aws/persistence/dynamodb/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 4 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreModules`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=fa2782e9d4b1cce9b57f7735571ea2ae6dda976eae8de3f193255446318c4773 after=d562a59c167760e431c16b2e40462e8601c856d377bbd93c6865e9e6578c8eae -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Can a malformed stored record be diagnosed without copying its attribute values into logs?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Existing key layouts, transaction behavior and command order are not redesigned by this work. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/adapters/aws/persistence/dynamodb/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L066 platform/adapters/aws/persistence/dynamodb](066-aws-persistence-dynamodb.md) · [L067 platform/adapters/aws/persistence/dynamodb/src](067-persistence-dynamodb-src.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
