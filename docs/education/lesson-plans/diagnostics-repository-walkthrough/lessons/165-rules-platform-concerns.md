<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l165
  version: 2
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder docs/03.product/rules/platform/concerns.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L165 — docs/03.product/rules/platform/concerns

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: docs/03.product/rules/platform/concerns -->

## What you will understand

The harness tells agents what complete work requires, who owns it, which compatibility boundaries to preserve and what proof must be recorded.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

A change adds a new integration call. Locate the actual failure observation, upstream definition, adapter mapping, selected catalog, delivery reader and tests before calling the change complete. Do not start the expensive full gate while a required consumer is still being edited.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Existing governance required safety and verification, but did not make connected diagnostic producers, consumers and source-matched review explicit enough.

**After:** The shared workflow/standard requires bounded responsibility and consumer inventories, upstream ownership, safe detail, source review and stopped inputs before expensive final verification.

**Why this was needed:** A schema with no producer or a producer with no reader is incomplete. More written instructions alone cannot establish compliance, so executable checks complement human review.

This directory contains `documentation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: docs/03.product/rules/platform/concerns/config-runtime-settings.yml -->

### config-runtime-settings.yml

[Open current source](../../../../../.agentic/03.product/standards/config-runtime-settings.md) · **Snapshot:** modified existing file; 3 added / 2 removed lines. These are textual counts, not a count of new features.

**Current location:** DIAG-002 converted these requirements into a harness
standard. The old YAML is now a pointer, not a ruleset. The before/after text,
file marker and hashes below describe the original course snapshot, not the
later migration.

**What it did at the snapshot:** Machine-readable rule/schema declaration.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Reconciles the declaration for rules for future changes; read the sections `id: harness.architecture.rules.concerns.config-runtime-settings`, `version: 2`, `status: active`, `created_on: "2026-06-23"`, `updated_on: "2026-10-27"`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `agentic-artifact:`; `schema: agentic-artifact/v3`; `id: harness.architecture.rules.concerns.config-runtime-settings`; `version: 2`; `status: active`; `created_on: "2026-06-23"`.

Proving boundary: source/document consistency and the actual evidence referenced by this record. Reading a plan or finding a valid metadata header is not runtime proof.

<!-- course-source-sha256: before=ef8dad5efaef528b7c371df9ae5c8e831ac389b4eb792f19829efbb271f6df8f after=f7a6e1d68db3d6d180bc552f0637a86354aa45eea95da722d42d9df0805143ed -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which requirements can a script check, and which need architectural judgment about what the operation actually knows?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Governance cannot guarantee that an agent never makes mistakes or that every possible future failure is already covered. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../03.product/rules/platform/concerns) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L166 docs/03.product/rules/platform/layers](166-rules-platform-layers.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
