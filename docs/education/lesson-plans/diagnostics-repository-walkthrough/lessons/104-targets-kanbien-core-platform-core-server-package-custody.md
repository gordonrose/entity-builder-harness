<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l104
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L104 — scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody -->

## What you will understand

Build and image tooling turns source into a runnable artifact. The payload is the compiled files and dependencies actually included in that artifact.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Remove either core-server diagnostic module from an assembled test payload. The import-closure check must reject it with its fixed code. A Dockerfile mentioning a source file is not, by itself, proof that the resulting image runs.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work.

**After:** Packaging includes required diagnostic modules and checks actual import closure. Existing registered checks are reused with source identity, and omission counterexamples prove missing modules are caught.

**Why this was needed:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

This directory contains `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/verify-workflow.py -->

### verify-workflow.py

[Open current source](../../../../../scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/verify-workflow.py) · **Snapshot:** modified existing file; 3 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Reject an unsafe target-bound package workflow before it can publish an image.

**Before:** Local compilation could see modules on disk that were missing from the image COPY list. Broad source checks also repeated already-owned verification work. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Retain fixed publication/qualification/workflow and IAM access requirements, exact protected builder bodies and original child status. Failed policy extraction now emits a bounded concern before its temporary report disappears; Unicode/workflow failures remain fixed concerns.

**Why:** A source-level pass is insufficient if deployment cannot import a diagnostic dependency at startup. The artifact, not only the checkout, must be runnable.

Current reading anchors (not all are new): `qualification_route_valid`, `custody_route_valid`, `main`.

Owning registered proof: `core-package-custody-regression`, `package-custody-regression`, `delivery-access-contract-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=de4a6f3908120a2b3460d0c3bdec00221851fccc8ca6062f73454613db599568 after=d15a585d8bdfd6b0ad8fd060cb3cde9a186a60cbfd2a7b0cbe4855da331b5666 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why could TypeScript compilation pass while the deployed image fails at startup?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Local image qualification is not publication, target alignment or live acceptance. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L105 scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/validate-delivery-access](105-kanbien-core-platform-core-server-package-custody-validate-delivery-access.md) · [L106 scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody](106-targets-kanbien-core-platform-core-server-persistence-observability-collector-package-custody.md) · [L107 scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody](107-targets-kanbien-core-platform-core-server-persistence-package-custody.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
