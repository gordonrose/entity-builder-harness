<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l168
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/verify-platform-shell-deployment-workflow.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L168 — scripts/04.deploy/verify-platform-shell-deployment-workflow

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/verify-platform-shell-deployment-workflow -->

## What you will understand

The check selector maps changed inputs to required checks and reuses prior passing results only when their source/runtime/contract identity still matches.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **1 changed file** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

An HTTP-only implementation edit should select relevant runtime and repository-contract proof, not fixture-only runner mechanics. Changing the selector itself should select mechanics. Change an input after a receipt: matching reuse must stop.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Broad inputs and mixed suites caused ordinary runtime changes to select runner-mechanics tests and repeat checks inside aggregate wrappers. Runtime identity work also repeated expensive scans.

**After:** Registered leaves, closed aggregate dispatch, separated mechanics/repository-contract suites, narrower review ownership and bounded identity reuse remove duplicate work while retaining obligation and invalidation checks.

**Why this was needed:** Speed should come from not doing the same valid work twice, not from skipping a required assertion or trusting a stale result.

This directory contains `implementation` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh -->

### script.sh

[Open current source](../../../../../scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh) · **Snapshot:** modified existing file; 10 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Statically enforce that the Kanbien staging workflow scans, creates an SBOM, attests, and publishes an immutable image without deploying it.

**Before:** Broad inputs and mixed suites caused ordinary runtime changes to select runner-mechanics tests and repeat checks inside aggregate wrappers. Runtime identity work also repeated expensive scans. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Existing static workflow guard now requires additive registered preparation and focused payload proof before the unchanged five npm commands and container-boundary check. Caller regressions prove fail-stop ordering and original lifecycle behavior; static/source proof is not a CI execution or published-image receipt.

**Why:** Speed should come from not doing the same valid work twice, not from skipping a required assertion or trusting a stale result.

Owning registered proof: `shell-publication`, `diagnostic-catalog-readers`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=671796a7bc0e3429dec803d970680fb01a5d30f29acbc67130f769f551829453 after=c5efa01284a7e799f631ac68ceff1f817b6a2a98b771e917ba25f301ea133119 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What evidence must remain equal before a previous passing check can be reused?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** The optimization is not a promise that every change is fast; changes to verification authority legitimately select broad proof. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/verify-platform-shell-deployment-workflow) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L094 scripts/04.deploy/build-platform-shell-image](094-scripts-04-deploy-build-platform-shell-image.md) · [L110 scripts/04.deploy/smoke-test-platform-shell-image](110-scripts-04-deploy-smoke-test-platform-shell-image.md) · [L111 scripts/04.deploy/validate-container-boundaries](111-scripts-04-deploy-validate-container-boundaries.md) · [L112 scripts/04.deploy/inventory-deploy-control](112-scripts-04-deploy-inventory-deploy-control.md) · [L127 scripts/04.deploy](127-scripts-04-deploy.md) · [L152 scripts/04.deploy/reconcile-platform-shell-staging](152-scripts-04-deploy-reconcile-platform-shell-staging.md) · [L153 scripts/04.deploy/shared](153-scripts-04-deploy-shared.md) · [L155 scripts/04.deploy/verify-platform-shell-deploy-readiness](155-scripts-04-deploy-verify-platform-shell-deploy-readiness.md) · [L169 scripts/04.deploy/verify-platform-shell-infrastructure](169-scripts-04-deploy-verify-platform-shell-infrastructure.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 1 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
