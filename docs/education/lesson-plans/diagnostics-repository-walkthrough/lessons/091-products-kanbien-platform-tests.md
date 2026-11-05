<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l091
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder products/kanbien-platform/tests.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L091 — products/kanbien-platform/tests

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: products/kanbien-platform/tests -->

## What you will understand

Entrypoints assemble concrete settings, catalogs, adapters, reporters and programs. A one-shot program performs a task such as migration or verification and exits.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Follow a missing IAM username from its target binding through Core validation, the structured failure, selected catalog and safe task output to the Python reader. At no step is the username value required. Contrast source-read failure and permission proof rejection.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Core-server persistence, administration, IAM authentication, migrations and verification already existed. Combined guards and task wrappers could discard the exact reason or expose native text.

**After:** Target bindings connect reusable definitions to actual settings and call boundaries. Administration/verifier observations preserve primary failure, bounded source companions, operation progress and existing SQL/privilege/cleanup behavior.

**Why this was needed:** A library cannot know the deployment variable name or which target program called it. Composition must connect that final context without becoming a second source of generic security or persistence rules.

This directory contains `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: products/kanbien-platform/tests/run-runtime-tests.mjs -->

### run-runtime-tests.mjs

[Open current source](../../../../../products/kanbien-platform/tests/run-runtime-tests.mjs) · **Snapshot:** modified existing file; 1 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Changed declaration anchors: `coreModules`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=d3964b4d610bb8891d780bedbc75e6860cca00e2a4f6febcc15026ddcf186187 after=da45c70d41f820ed5614b40475f8e13cecb58e168f8af32c2395f0a0ebba5b0c -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Which fact can the target add that a provider-neutral Core package must not hard-code?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** No SQL, database privilege, authentication rule, extra retry or administration action is authorized by diagnostic reporting. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../products/kanbien-platform/tests) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
