<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l170
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/repo/check-selection.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L170 — scripts/repo/check-selection

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/repo/check-selection -->

## What you will understand

The check selector maps changed inputs to required checks and reuses prior passing results only when their source/runtime/contract identity still matches.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **9 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

An HTTP-only implementation edit should select relevant runtime and repository-contract proof, not fixture-only runner mechanics. Changing the selector itself should select mechanics. Change an input after a receipt: matching reuse must stop.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Broad inputs and mixed suites caused ordinary runtime changes to select runner-mechanics tests and repeat checks inside aggregate wrappers. Runtime identity work also repeated expensive scans.

**After:** Registered leaves, closed aggregate dispatch, separated mechanics/repository-contract suites, narrower review ownership and bounded identity reuse remove duplicate work while retaining obligation and invalidation checks.

**Why this was needed:** Speed should come from not doing the same valid work twice, not from skipping a required assertion or trusting a stale result.

This directory contains `documentation`, `selection`, `implementation`, `test`, `dispatch` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/repo/check-selection/README.md -->

### README.md

[Open current source](../../../../../scripts/repo/check-selection/README.md) · **Snapshot:** modified existing file; 173 added / 2 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** The existing document described the earlier boundary without this project's additional diagnostic requirements.

**After:** Explains the diagnostic responsibilities and compatibility limits for verification ownership and safe reuse; read the sections `Focused Repository Verification`, `Runner verification ownership`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Focused Repository Verification`; `Runner verification ownership`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=f2d56a3220c089a3e0ee5368256ee75e45636ba183f13bdfe41d08c4ee170a6e after=651679fde3a22d3793ea84fe3c073eb569df95785f2f11cff8e4250e53dd23e5 -->

<!-- course-file: scripts/repo/check-selection/checks.yml -->

### checks.yml

[Open current source](../../../../../scripts/repo/check-selection/checks.yml) · **Snapshot:** modified existing file; 1184 added / 152 removed lines. These are textual counts, not a count of new features.

**What it does:** Maps checks to inputs, commands, dependencies and execution stages.

**Before:** Broad declarations and aggregate-owned commands caused repeated proof and overly broad selection.

**After:** Registers independently owned leaves, exact input closures, runner-suite partitions and diagnostic proof, retaining explicit later-stage boundaries.

**Why:** Efficiency comes from selecting/reusing the same obligations correctly, not deleting them.

Reading anchors: `agentic-artifact:`; `schema: agentic-artifact/v3`; `id: repo.check-selection.catalog`; `version: 8`; `status: active`; `created_on: "2026-10-24"`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=35a899d9c4d73883d050f91ecd312b2b2d962975fc7bcfcc706e6f33f5de2e84 after=775fe24f6e8f32872c1947ae655da6c26eebe77848f591fc8278a5e2d54b6af9 -->

<!-- course-file: scripts/repo/check-selection/local_cache.py -->

### local_cache.py

[Open current source](../../../../../scripts/repo/check-selection/local_cache.py) · **Snapshot:** modified existing file; 185 added / 49 removed lines. These are textual counts, not a count of new features.

**What it does:** Builds and validates trusted local result identities.

**Before:** Identity construction repeatedly traversed installed runtime inputs and repeated compatible work in a single run.

**After:** Shares equivalent identity components and bounded receipt windows while retaining fresh validation at required command/final boundaries.

**Why:** A cached pass is useful only when its full relevant inputs still match; changed/failing/partial evidence must not be reused.

Current reading anchors (not all are new): `__init__`, `local_check_diagnostic`, `valid_node_package`, `__init__`, `clear`, `require_root`, `node_installation_identity`, `frame`, `contained`, `walk` (19 more in source).

Connected review context (`runner-core-verification-enforcement`; this review may span several files): Runner and cache proof ownership is separate from runtime exports and adapter behavior. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `check-selection-mechanics`, `check-selection-repository-contracts`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=c106163dd9d6c280bb97eb8f70791e9051275a55a2efce4c506a628fc7842f74 after=85e3b5e9943c11aaa10aa5794db16f13f6a1c52934386a74cd0aa7c29bb13cbb -->

<!-- course-file: scripts/repo/check-selection/mechanics_test.py -->

### mechanics_test.py

[Open current source](../../../../../scripts/repo/check-selection/mechanics_test.py) · **Snapshot:** added (absent from baseline); 2016 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Tests selector/cache mechanics in disposable fixtures.

**Before:** These obligations lived mixed with real-repository tests in the old smoke suite.

**After:** Moves the fixture-oriented tests into their own registered suite and adds selection/reuse/invalidation/failure assertions.

**Why:** An ordinary runtime edit need not rerun fixture-only mechanics, while changes to runner authority must.

Added named test anchors: `test_artifact_migration_leaf_failure_reuse_and_invalidation`; `test_dynamodb_owned_leaf_failure_reuse_and_source_runtime_contract_invalidation`; `test_sqs_owned_leaf_failure_reuse_and_source_runtime_contract_invalidation`; `test_aws_alignment_leaf_failure_reuse_and_invalidation`; `test_provider_condition_leaf_failure_reuse_and_invalidation`; `test_core_target_leaf_failure_reuse_and_invalidation`; `test_delivery_access_leaf_failure_reuse_and_invalidation`; `test_bootstrap_controls_leaf_failure_reuse_and_invalidation`; `test_foundation_budget_leaf_failure_reuse_and_invalidation`; `test_harness_validator_leaf_failure_reuse_and_invalidation`; `test_harness_index_leaf_failure_reuse_and_invalidation`; `test_chat_export_leaf_failure_reuse_and_invalidation`; 115 further named cases remain in the file.

Connected review context (`reusable-shell-source-verification`; this review may span several files): Verification orchestration requests the registered server, product and compiled-payload units through the existing trusted local runner. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `diagnostic-catalog-readers`, `shell-package-source`, `check-selection-mechanics`, `check-selection-repository-contracts`, `shell-infrastructure`, `delivery-access-contract-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=ded3371427592db63e5613b9af5ec7c659846e26ac42371fc4773ef2dc986e5b -->

<!-- course-file: scripts/repo/check-selection/repository_contracts_test.py -->

### repository_contracts_test.py

[Open current source](../../../../../scripts/repo/check-selection/repository_contracts_test.py) · **Snapshot:** added (absent from baseline); 662 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Checks actual repository catalog and ownership wiring.

**Before:** Real-repository assertions travelled with fixture-only mechanics.

**After:** Keeps real catalog/discovery/dependency/consumer proofs in an independently selected suite.

**Why:** Narrowing selection must not remove tests that genuinely inspect the runtime-facing repository.

Added named test anchors: `test_artifact_migration_owns_complete_existing_command_and_exact_inputs`; `test_chat_export_and_metrics_own_exact_standalone_commands_inputs_and_runtime`; `test_alignment_suites_have_separate_actual_local_commands_and_input_closures`; `test_deployment_diagnostic_fixture_binds_actual_controller_and_catalog_dependencies`; `test_disposable_postgresql_proof_binds_actual_composition_dependencies`; `test_harness_index_owns_actual_complete_command_and_input_closure`; `test_harness_validator_owns_actual_complete_command_and_input_closure`; `test_target_controls_and_budget_own_actual_complete_local_commands`; `test_delivery_access_suite_and_package_fixture_dependencies_are_real_inputs`; `test_dynamodb_persistence_owns_complete_adapter_command_and_actual_inputs`; `test_ecs_runtime_uses_existing_complete_adapter_command_and_inputs`; `test_sqs_queue_owns_complete_adapter_command_and_actual_inputs`; 14 further named cases remain in the file.

Connected review context (`reusable-shell-source-verification`; this review may span several files): Verification orchestration requests the registered server, product and compiled-payload units through the existing trusted local runner. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `diagnostic-catalog-readers`, `shell-package-source`, `check-selection-mechanics`, `check-selection-repository-contracts`, `shell-infrastructure`, `delivery-access-contract-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=621e4734266d086fd83dd97802ff7a738ae1770f780ba0457696c13ff928a127 -->

<!-- course-file: scripts/repo/check-selection/script.py -->

### script.py

[Open current source](../../../../../scripts/repo/check-selection/script.py) · **Snapshot:** modified existing file; 391 added / 39 removed lines. These are textual counts, not a count of new features.

**What it does:** Plans and executes the selected verification graph.

**Before:** Aggregate callers and identity work could repeat checks and mix selection responsibilities.

**After:** Dispatches catalog-owned leaves/aggregates, tracks matching reuse and retains runtime/source freshness and original failure propagation.

**Why:** An aggregate must still require every member even if no member needs to execute twice.

Current reading anchors (not all are new): `safe_nested_execution_summary`, `seconds`, `safe_runtime_error_type`, `verification_dependencies`, `visit`, `dependency_order`, `visit`, `below`, `git`, `metadata` (23 more in source).

Connected review context (`runner-core-verification-enforcement`; this review may span several files): Runner and cache proof ownership is separate from runtime exports and adapter behavior. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `check-selection-mechanics`, `check-selection-repository-contracts`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=fec7a069b29e04bad8a51cd71422d8b65be31a5f97421b3a323a0cd37d5efc39 after=db8bacf3a59258f3809e149344edf8fd9e749d4957c452cddbbf26a635bc2399 -->

<!-- course-file: scripts/repo/check-selection/smoke-test.py -->

### smoke-test.py

[Open current source](../../../../../scripts/repo/check-selection/smoke-test.py) · **Snapshot:** modified existing file; 24 added / 1204 removed lines. These are textual counts, not a count of new features.

**What it does:** Retains the full/focused compatibility facade for the split suites.

**Before:** Contained the old mixed suite and helper definitions directly.

**After:** Loads the separated mechanics/repository-contract tests and preserves supported importing/dispatch behavior.

**Why:** Splitting files must not silently drop test discovery or break delivery tools that import the old entrypoint.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=f9ad8a4116c3e17a5fb4ac76ce688262fcda169102fe127b54db565a027ba513 after=fab4945d0136d870563f3c5fb9925224974d47b39b0b6d184dd4cd2f139f1a96 -->

<!-- course-file: scripts/repo/check-selection/smoke-test.sh -->

### smoke-test.sh

[Open current source](../../../../../scripts/repo/check-selection/smoke-test.sh) · **Snapshot:** modified existing file; 25 added / 3 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=ae1354f8ee8dddfea1c3bc4f2dc8c45d567837eb214c85cd710eca9acd27825f after=ec50c4dd1a8f0a00315d35636e2a05a487a1efccae3da421f5e03459b802a0b0 -->

<!-- course-file: scripts/repo/check-selection/test_support.py -->

### test_support.py

[Open current source](../../../../../scripts/repo/check-selection/test_support.py) · **Snapshot:** added (absent from baseline); 223 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Shares fixture helpers between split suites and foreign consumers.

**Before:** Helpers were coupled to the monolithic smoke module.

**After:** Makes helper ownership explicit while compatible imports and isolated foreign-import tests retain existing consumers.

**Why:** The first partition attempt missed a foreign importer; explicit shared support and regression coverage close that omission.

Current reading anchors (not all are new): `write`, `setUp`, `check_script`, `save`, `run_plan`, `git`, `codes`, `focused_fixture`, `prepare_selector_cli`, `run_selector_cli` (3 more in source).

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=absent after=391fd7ce3b0e7ea7e0f72e593ed3c53d8e6a2d0b2f778a02a562c3e733f7b860 -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: What evidence must remain equal before a previous passing check can be reused?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** The optimization is not a promise that every change is fast; changes to verification authority legitimately select broad proof. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/repo/check-selection) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L167 scripts/repo/diagnostic-coverage](167-scripts-repo-diagnostic-coverage.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 9 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
