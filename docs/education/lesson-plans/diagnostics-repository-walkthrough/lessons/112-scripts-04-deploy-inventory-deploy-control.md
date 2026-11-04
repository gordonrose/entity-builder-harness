<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l112
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/04.deploy/inventory-deploy-control.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L112 — scripts/04.deploy/inventory-deploy-control

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/04.deploy/inventory-deploy-control -->

## What you will understand

Alignment tooling compares declared target requirements and observed provider conditions before build or deployment.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **4 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Compare a supported DescribeDBInstances not-found response with a bare error-code string or a failure from another operation. Only the exact supported observation can establish the declared absence condition.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** The declarations and read-only checks already existed. Unreadable files, malformed provider responses and command failures could be confused with a valid empty observation.

**After:** Finite diagnostics distinguish declaration/shape/predicate/native-command boundaries while preserving existing comparison rules and actual command order.

**Why this was needed:** If an AWS observation fails, the agent must not conclude the resource is absent or aligned. Unknown is materially different from a checked negative result.

This directory contains `documentation`, `test`, `implementation`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/04.deploy/inventory-deploy-control/README.md -->

### README.md

[Open current source](../../../../../scripts/04.deploy/inventory-deploy-control/README.md) · **Snapshot:** modified existing file; 12 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for target declarations and provider observation; read the sections `Delivery Control Inventory`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Delivery Control Inventory`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=2c855f3fb024e0d34fb2b9f6ba0d81ec0244c57159c87f3d674236dd60735588 after=cd69b0dabd1170b6e5931831e57ea793e7d0e6eb4c61e4bbc45a43c716811b35 -->

<!-- course-file: scripts/04.deploy/inventory-deploy-control/delivery-smoke-test.py -->

### delivery-smoke-test.py

[Open current source](../../../../../scripts/04.deploy/inventory-deploy-control/delivery-smoke-test.py) · **Snapshot:** modified existing file; 96 added / 5 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for target declarations and provider observation.

**Before:** The file already tested the capability; the patch adds or changes the diagnostic/consumer assertions listed below.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. The newly visible named cases below provide concrete reading anchors. Connected proving scope (the review spans related files, not only this test): Retain requirement/check chains, legitimate missing paths, applicability and configuration projection. Rejected references cannot reappear through inputs/consumers/findings, and invalid logical identities use fixed report markers without changing admission.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Added named test anchors: `test_policy_extraction_preserves_full_census_through_reachable_nested_members`; `test_unrelated_catalog_inputs_and_focused_prerequisites_do_not_bind_delivery`; `test_reachable_member_dag_rejects_malformed_unknown_cycles_and_boundary_laundering`; `test_catalog_member_edit_selects_independent_census_via_real_consumer_metadata`.

Owning registered proof: `delivery-inventory-regression`, `persistence-composition`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=6d3e65d47bfa984bdbaae1b40766a92c5afea631654ce361bb472f5d3410545e after=9c060a8cc6b54dfbf8f1bbdce5b57840a25d83405288a4c6139c266bdb12d8a2 -->

<!-- course-file: scripts/04.deploy/inventory-deploy-control/delivery_inventory.py -->

### delivery_inventory.py

[Open current source](../../../../../scripts/04.deploy/inventory-deploy-control/delivery_inventory.py) · **Snapshot:** modified existing file; 54 added / 1 removed lines. These are textual counts, not a count of new features.

**What it does:** Reconcile a physical delivery census with existing declarations and emit source-bound coverage without provider access.

**Before:** The declarations and read-only checks already existed. Unreadable files, malformed provider responses and command failures could be confused with a valid empty observation. In this file the change is localized by the symbols and source comparison below.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Read-only delivery census traces only declared route proof roots and their reachable catalog members, preserving extracted policy consumers without globally registering catalog entries, directory inputs or conditional prerequisites. Tests reject malformed, unknown, cyclic, missing-command and stage/effect/header disagreements, prove no command execution, require actual covered census and verify the real catalog consumer selection edge.

**Why:** If an AWS observation fails, the agent must not conclude the resource is absent or aligned. Unknown is materially different from a checked negative result.

Current reading anchors (not all are new): `document`, `module`, `under`, `dormant_roots`, `dormant_package_commands`, `dormant_governed_action`, `files`, `repository_ci_findings`, `effects`, `fixture_source` (7 more in source).

Owning registered proof: `delivery-inventory-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=470ec9f0a1ae6aec6a34950d532781242c23d6bf9342bd8da7d043cbbf97744f after=aaca02f682138a112adcaf6c34eb436057ceee5d6432992a6606497145b1115c -->

<!-- course-file: scripts/04.deploy/inventory-deploy-control/smoke-test.sh -->

### smoke-test.sh

[Open current source](../../../../../scripts/04.deploy/inventory-deploy-control/smoke-test.sh) · **Snapshot:** modified existing file; 4 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Owning registered proof: `delivery-inventory-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=f2807329479f6926d36a9903da4446b02fb219f7d99aac561906520cf59ed9e0 after=747301b85604bbec96c99c205d6817b37eed37ed5b132dda52e6c44b00c96609 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: When is an empty result evidence of absence, and when is it evidence that observation failed?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Fixtures prove local classification. No live AWS observation was executed to prepare this course. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/04.deploy/inventory-deploy-control) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L094 scripts/04.deploy/build-platform-shell-image](094-scripts-04-deploy-build-platform-shell-image.md) · [L110 scripts/04.deploy/smoke-test-platform-shell-image](110-scripts-04-deploy-smoke-test-platform-shell-image.md) · [L111 scripts/04.deploy/validate-container-boundaries](111-scripts-04-deploy-validate-container-boundaries.md) · [L127 scripts/04.deploy](127-scripts-04-deploy.md) · [L152 scripts/04.deploy/reconcile-platform-shell-staging](152-scripts-04-deploy-reconcile-platform-shell-staging.md) · [L153 scripts/04.deploy/shared](153-scripts-04-deploy-shared.md) · [L155 scripts/04.deploy/verify-platform-shell-deploy-readiness](155-scripts-04-deploy-verify-platform-shell-deploy-readiness.md) · [L168 scripts/04.deploy/verify-platform-shell-deployment-workflow](168-scripts-04-deploy-verify-platform-shell-deployment-workflow.md) · [L169 scripts/04.deploy/verify-platform-shell-infrastructure](169-scripts-04-deploy-verify-platform-shell-infrastructure.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 4 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
