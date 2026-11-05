<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l023
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder platform/contracts.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L023 — platform/contracts

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: platform/contracts -->

## What you will understand

Contracts define how apps declare routes, jobs, permissions, configuration, observability profiles and diagnostic catalogs without importing runtime implementations.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Register a route that references an undeclared observability profile. Observe the registration failure before listening. A structurally valid catalog with a conflicting definition must not silently replace the selected meaning.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The registration contracts already existed. Invalid declarations and profile mismatches did not always identify the exact registration predicate or preserve safe source detail.

**After:** Catalog/reporter/context interfaces, registration observations and finite error-class declarations are explicit. Runtime and test consumers share those meanings, rather than inventing parallel declarations.

**Why this was needed:** An app can declare its own safe diagnostic language upstream. A database adapter should not have to decide what an app-specific failure means.

This directory contains `documentation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: platform/contracts/README.md -->

### README.md

[Open current source](../../../../../platform/contracts/README.md) · **Snapshot:** modified existing file; 5 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for platform registration contracts; read the sections `Platform Contracts`, `Source map`, `Operational Nomenclature`, `Optional Tenant And Resource Authorization`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Platform Contracts`; `Source map`; `Operational Nomenclature`; `Optional Tenant And Resource Authorization`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=b117f11e9d3ccb589cd014719eaff09d1b90e13b5bcfda1ae4c9e363fe8d7f5d after=af8ab5e16e782dfc9645938580a9c7c11ac3e950a42521c70a3c96d330210d3c -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why should a Contracts interface not import the concrete HTTP server or AWS adapter?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Registration consistency checks cannot certify architectural judgment or all future failure modes on their own. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../platform/contracts) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L008 platform/config](008-platform-config.md) · [L024 platform/contracts/contracts](024-platform-contracts-contracts.md) · [L025 platform/contracts/src](025-platform-contracts-src.md) · [L026 platform/contracts/tests](026-platform-contracts-tests.md) · [L030 platform/runtime](030-platform-runtime.md) · [L034 platform/testing](034-platform-testing.md) · [L037 platform/server](037-platform-server.md) · [L043 platform/health](043-platform-health.md) · [L053 platform/security](053-platform-security.md) · [L058 platform/persistence](058-platform-persistence.md) · [L070 platform/workers](070-platform-workers.md) · [L077 platform/observability](077-platform-observability.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
