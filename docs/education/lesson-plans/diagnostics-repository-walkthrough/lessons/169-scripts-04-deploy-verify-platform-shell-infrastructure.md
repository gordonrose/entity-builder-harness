<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l169
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/verify-platform-shell-infrastructure.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L169 — scripts/04.deploy/verify-platform-shell-infrastructure

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/verify-platform-shell-infrastructure -->

## What you will understand

The check selector maps changed inputs to required checks and reuses prior passing results only when their source/runtime/contract identity still matches.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **2 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

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

<!-- course-file: scripts/04.deploy/verify-platform-shell-infrastructure/policy.sh -->

### policy.sh

[Open current source](../../../../../scripts/04.deploy/verify-platform-shell-infrastructure/policy.sh) · **Snapshot:** added (absent from baseline); 2522 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Holds the extracted infrastructure static-policy assertions.

**Before:** The policy body lived inside the aggregate script.

**After:** Preserves the policy assertions in a separately owned unit, while executable child checks become catalog-owned leaves.

**Why:** Extraction reduces duplicate execution; it does not remove policy assertions or certify runtime diagnostic completeness.

Added import edges: `node:crypto`.

Connected review context (`shell-infrastructure-static-policy`; this review may span several files): Extracted verification-only policy preserves the original policy body and assertion failures; executable child checks are separately catalog-owned. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `shell-infrastructure-policy`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=7eb05f6474dc16f02c13b7d9361180c2f11915ce808bba8cdb961a480a18a94d -->

<!-- course-file: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh -->

### script.sh

[Open current source](../../../../../scripts/04.deploy/verify-platform-shell-infrastructure/script.sh) · **Snapshot:** modified existing file; 2 added / 2504 removed lines. These are textual counts, not a count of new features.

**What it does:** Requests the complete registered infrastructure aggregate.

**Before:** Ran a long embedded policy plus many children directly.

**After:** Dispatches the aggregate through the selector so all members remain required and matching passes can be reused.

**Why:** A shorter wrapper is not a smaller safety requirement; catalog membership and failure propagation tests preserve the obligations.

Connected review context (`shell-infrastructure-aggregate-dispatch`; this review may span several files): Verification wrapper dispatches the complete catalog-owned static policy and seventeen existing child checks through the trusted runner. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `shell-infrastructure`, `diagnostic-catalog-readers`, `check-selection-mechanics`, `check-selection-repository-contracts`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=b4c33c039aadde726992c9a8ac6f90b1e3a32da1c3f77ca449589d4ffa02faac after=1938d4044951732d5499c30be5f0fa380dd2b7d5cfed931a95ca4a96fbd4c98c -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What evidence must remain equal before a previous passing check can be reused?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** The optimization is not a promise that every change is fast; changes to verification authority legitimately select broad proof. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/verify-platform-shell-infrastructure) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L094 scripts/04.deploy/build-platform-shell-image](094-scripts-04-deploy-build-platform-shell-image.md) · [L110 scripts/04.deploy/smoke-test-platform-shell-image](110-scripts-04-deploy-smoke-test-platform-shell-image.md) · [L111 scripts/04.deploy/validate-container-boundaries](111-scripts-04-deploy-validate-container-boundaries.md) · [L112 scripts/04.deploy/inventory-deploy-control](112-scripts-04-deploy-inventory-deploy-control.md) · [L127 scripts/04.deploy](127-scripts-04-deploy.md) · [L152 scripts/04.deploy/reconcile-platform-shell-staging](152-scripts-04-deploy-reconcile-platform-shell-staging.md) · [L153 scripts/04.deploy/shared](153-scripts-04-deploy-shared.md) · [L155 scripts/04.deploy/verify-platform-shell-deploy-readiness](155-scripts-04-deploy-verify-platform-shell-deploy-readiness.md) · [L168 scripts/04.deploy/verify-platform-shell-deployment-workflow](168-scripts-04-deploy-verify-platform-shell-deployment-workflow.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 2 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
