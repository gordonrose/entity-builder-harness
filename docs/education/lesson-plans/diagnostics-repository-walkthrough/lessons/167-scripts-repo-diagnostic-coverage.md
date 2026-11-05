<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.diagnostics-course.l167
  version: 1
  status: active
  created_on: "2026-10-31"
  updated_on: "2026-11-04"
  layer: 05.education
  domain: education.diagnostics
  disciplines: [architecture, security, sre, agentic]
  kind: guide
  purpose: Teach the diagnostic changes in folder scripts/repo/diagnostic-coverage.
  portability: {class: source-only, targets: []}
  used_by:
  - id: education.diagnostics-course.readme
    path: docs/education/lesson-plans/diagnostics-repository-walkthrough/README.md
-->

# L167 — scripts/repo/diagnostic-coverage

[Course start](../README.md) · [All folder lessons](../folder-index.md) · [Teaching protocol](../facilitator-guide.md)

<!-- course-folder: scripts/repo/diagnostic-coverage -->

## What you will understand

The diagnostic-coverage tools discover relevant code, validate source-matched owner reviews and export runtime-owned definitions for other languages.

After this lesson, explain why this folder participates in diagnostics, distinguish its old and new responsibilities, and follow every changed file below. The directory owns **10 changed files** in the frozen course inventory. Subfolders have their own lessons; they are not silently absorbed into this one.

## Start with a concrete case

Change a reviewed source without updating the owner record: the source hash must no longer match. Separately add an unsupported catalog value: the compiled export/compatibility proof must reject inappropriate drift.

Before reading on, predict which facts are known and which would be guesses. This is a reasoning exercise with synthetic conditions; do not run a deployment, administration task or destructive command.

## Before and after the project

**Before:** Diagnostic knowledge was spread across conventions and specialized rules. A claim of adoption could drift away from the implementation or omit ordinary new code.

**After:** Independent discovery, reviewed source hashes, historical version checks, compiled catalog exports and strict reader tests provide executable drift detection. Review records remain distinct from runtime meaning.

**Why this was needed:** An agent changing a source must update its explanation and proof, not merely copy an old adopted label. Python must consume the same allowed values as TypeScript rather than hand-maintain another vocabulary.

This directory contains `documentation`, `implementation`, `dispatch`, `test`, `compiler` work. A test proves a boundary, a generated export shares meaning, documentation instructs, and runtime code performs or observes work. Do not confuse those roles because they share a folder prefix.

## Every changed file

The comparison is against `d94da2b9401d3abcf86618b5d497e9b93903490a`. “Added” means absent at that commit, not that the whole capability was invented here. The file-specific explanations below take precedence over the broader folder summary.

<!-- course-file: scripts/repo/diagnostic-coverage/README.md -->

### README.md

[Open current source](../../../../../scripts/repo/diagnostic-coverage/README.md) · **Snapshot:** added (absent from baseline); 121 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Human-facing ownership, contract or workflow guidance.

**Before:** This dedicated document was absent at the baseline.

**After:** Explains the diagnostic responsibilities and compatibility limits for executable adoption and compatibility checks; read the sections `Diagnostic adoption checks`. The source diff distinguishes actual rule changes from header/date updates.

**Why:** Documentation and executable rules must describe the same ownership; otherwise an agent can follow stale guidance while changing correct code. This file is not a runtime diagnostic producer.

Reading anchors: `Diagnostic adoption checks`.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=absent after=42987320686db67bdd48c97b6e2c29c07a5da3b4c019c5e8b9230ea952285ee1 -->

<!-- course-file: scripts/repo/diagnostic-coverage/compatibility.mjs -->

### compatibility.mjs

[Open current source](../../../../../scripts/repo/diagnostic-coverage/compatibility.mjs) · **Snapshot:** added (absent from baseline); 30 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Checks versioned catalog compatibility.

**Before:** There was no dedicated catalog comparator here.

**After:** Compares reviewed exported meanings and historical versions rather than accepting a changed old version as a harmless regeneration.

**Why:** Readers may still receive old records; a version number must continue to mean the same contract.

Changed declaration anchors: `canonical`, `catalogCompatible`.

Connected review context (`diagnostic-governance-enforcement`; this review may span several files): Independent ordinary-code discovery, source-matched adoption, code-owned target/security/observability/health exports, historical version retention and strict cross-language readers. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `diagnostic-catalog-readers`, `security-cognito-diagnostics`, `security-shared-rate-limit-diagnostics`, `cloudwatch-observability-runtime`, `ecs-fargate-runtime`, `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=6c6f122d44c8ee2d9c077bfe5571329419c50099020c5b3ed0ea73f82518799d -->

<!-- course-file: scripts/repo/diagnostic-coverage/export-catalogs.mjs -->

### export-catalogs.mjs

[Open current source](../../../../../scripts/repo/diagnostic-coverage/export-catalogs.mjs) · **Snapshot:** added (absent from baseline); 108 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Exports compiled code-owned definitions for tooling readers.

**Before:** Readers could rely on separately maintained diagnostic assumptions.

**After:** Selects explicit compiled catalogs, checks compatibility and writes/verifies generated JSON exports from owning runtime definitions.

**Why:** TypeScript and Python must agree on allowed detail without two independently edited vocabularies.

Changed declaration anchors: `root`, `args`, `compiled`, `packageSources`, `require`, `selections`, `failed`, `incompatible`, `outputs`.

Added import edges: `node:module`, `node:fs`, `node:path`, `node:url`, `node:child_process`, `./compatibility.mjs`.

Connected review context (`diagnostic-governance-enforcement`; this review may span several files): Independent ordinary-code discovery, source-matched adoption, code-owned target/security/observability/health exports, historical version retention and strict cross-language readers. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `diagnostic-catalog-readers`, `security-cognito-diagnostics`, `security-shared-rate-limit-diagnostics`, `cloudwatch-observability-runtime`, `ecs-fargate-runtime`, `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=2185b24cc7276318fd60826e384cec708f537b45b9dc6df34bf64e63ccfdab10 -->

<!-- course-file: scripts/repo/diagnostic-coverage/reviews.v1.json -->

### reviews.v1.json

[Open current source](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) · **Snapshot:** added (absent from baseline); 3985 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Records reviewed owner responsibilities, proof and source identities.

**Before:** No source-matched adoption ledger existed at this path.

**After:** Lists owning files, definitions, tests, check identities, source hashes, reasons and remaining limits, split where unrelated ownership previously coupled checks.

**Why:** Review evidence must match the code being assessed. This is governance data, not a second runtime diagnostic catalog or automatic completeness proof.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=absent after=96de849ef347cbcd104dd776c07823e2031c67b80726831b90e4ff946c6b3cfb -->

<!-- course-file: scripts/repo/diagnostic-coverage/runtime_contract.py -->

### runtime_contract.py

[Open current source](../../../../../scripts/repo/diagnostic-coverage/runtime_contract.py) · **Snapshot:** added (absent from baseline); 218 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Validates exported record shapes for Python tooling.

**Before:** There was no shared reader of these generated runtime-owned contracts.

**After:** Interprets the restricted exported schemas and bounds, accepting only declared code/version/detail shapes.

**Why:** Operational readers must validate task records before trusting them; arbitrary JSON must not masquerade as an approved diagnostic.

Current reading anchors (not all are new): `persistence_definitions`, `persistence_operation_definitions`, `persistence_vocabulary`, `copy_detail`, `validate_record`, `validate_selected_record`, `persistence_task_failure_contract`, `validate_persistence_task_observation`, `validate_persistence_task_source`, `validate_related_records` (3 more in source).

Connected review context (`diagnostic-governance-enforcement`; this review may span several files): Independent ordinary-code discovery, source-matched adoption, code-owned target/security/observability/health exports, historical version retention and strict cross-language readers. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `diagnostic-catalog-readers`, `security-cognito-diagnostics`, `security-shared-rate-limit-diagnostics`, `cloudwatch-observability-runtime`, `ecs-fargate-runtime`, `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=988a78b07cc36d6e35fbe8cd84804762e107c338a19ad5ee0952a19db3e632bc -->

<!-- course-file: scripts/repo/diagnostic-coverage/script.py -->

### script.py

[Open current source](../../../../../scripts/repo/diagnostic-coverage/script.py) · **Snapshot:** added (absent from baseline); 177 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Discovers candidate sources and verifies adoption records.

**Before:** There was no independent ordinary-code discovery and source-matched diagnostic adoption gate here.

**After:** Finds relevant responsibilities and checks review/source/proof ownership with explicit classifications and findings.

**Why:** New ordinary code should not evade standards simply because its author forgot to list it in the plan.

Current reading anchors (not all are new): `git`, `source_file`, `executable`, `discover`, `safe_file`, `review_document`, `review_bindings`, `review_rules`, `proof_inputs`, `validate` (1 more in source).

Connected review context (`diagnostic-governance-enforcement`; this review may span several files): Independent ordinary-code discovery, source-matched adoption, code-owned target/security/observability/health exports, historical version retention and strict cross-language readers. See the [source-matched review ledger](../../../../../scripts/repo/diagnostic-coverage/reviews.v1.json) for the complete scope and retained limitations. Historical pending wording in a review is not the final project disposition.

Owning registered proof: `diagnostic-catalog-readers`, `security-cognito-diagnostics`, `security-shared-rate-limit-diagnostics`, `cloudwatch-observability-runtime`, `ecs-fargate-runtime`, `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=c1ba759cb16706f8a0d1311dbbb1ec61ccceaea02ef19e78ec03356947cfb695 -->

<!-- course-file: scripts/repo/diagnostic-coverage/script.sh -->

### script.sh

[Open current source](../../../../../scripts/repo/diagnostic-coverage/script.sh) · **Snapshot:** added (absent from baseline); 22 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runs or assembles an existing verification unit.

**Before:** The baseline dispatcher used its earlier source list, direct commands or monolithic suite membership.

**After:** Updates setup, compiled-module wiring or registered dispatch so the diagnostic tests and their actual consumers run. Read the command list; this is proof plumbing, not new runtime policy.

**Why:** A well-written test proves nothing if its runner never loads it. Registered dispatch also makes duplicate execution and receipt reuse visible.

Owning registered proof: `diagnostic-catalog-readers`, `security-cognito-diagnostics`, `security-shared-rate-limit-diagnostics`, `cloudwatch-observability-runtime`, `ecs-fargate-runtime`, `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=e4236904073ed3dba3f6fcb54884110bba1042880c254f4e1780e9a015cb875f -->

<!-- course-file: scripts/repo/diagnostic-coverage/smoke-test.py -->

### smoke-test.py

[Open current source](../../../../../scripts/repo/diagnostic-coverage/smoke-test.py) · **Snapshot:** added (absent from baseline); 1212 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Runtime/fixture proof for executable adoption and compatibility checks.

**Before:** This dedicated test file was absent; related pre-existing tests elsewhere are not erased by that fact.

**After:** Exercises the changed diagnostic path and its compatibility boundaries. The newly visible named cases below provide concrete reading anchors. Connected proving scope (the review spans related files, not only this test): Validate already-parsed credential fields with exact value-free reasons; preserve accepted bytes and distinguish structural validation from actual database authentication.

**Why:** These assertions make the distinction between observed cause, safe detail and preserved behavior executable. Fixture success does not replace live provider or deployment proof.

Added import edges: `node:fs`, `node:path`, `./scripts/repo/diagnostic-coverage/compatibility.mjs`.

Added named test anchors: `test_aggregate_wrappers_request_complete_registered_units`; `test_runner_component_dispatch_is_closed_and_preserves_child_failure`; `test_verification_units_retain_all_original_commands`; `test_verification_units_reject_invalid_arguments_without_work`; `test_each_split_package_dispatch_preserves_command_and_failure`; `test_split_package_dispatch_retains_npm_lifecycle_hooks`; `test_deployment_ci_prepares_before_unchanged_checks_and_builder_preflight`; `test_review_inputs_preserve_overlapping_source_and_proof_ownership`; `test_review_ledger_semantics_preserve_removed_and_transferred_obligations`; `test_independent_platform_capability_reviews_keep_ownership_and_shared_proof`; `test_security_adapter_selection_rejects_unsupported_arguments`; `test_ordinary_service_and_changed_legacy_cannot_escape`; 25 further named cases remain in the file.

Owning registered proof: `persistence-composition`, `restore-connection-diagnostics`, `platform-shell-payload`, `deployment-operation-diagnostics-regression`, `diagnostic-catalog-readers`, `platform-contracts-runtime`, `platform-observability-runtime`, `platform-health-runtime`, `platform-server-runtime`, `platform-workers-runtime`, `persistence-diagnostic-mapping-regression`, `persistence-payload-regression`, `persistence-provider-regression`, `security-cognito-diagnostics`, `security-shared-rate-limit-diagnostics`, `cloudwatch-observability-runtime`, `ecs-fargate-runtime`, `shell-package-source`, `check-selection-mechanics`, `check-selection-repository-contracts`, `shell-infrastructure`, `shell-publication`, `postgresql-connection-diagnostics`, `platform-security-runtime`, `core-dependency-boundary`, `core-runtime`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=b45bebf78761a7c349ff24093dff212f8d65561843aa4ec4f0ad61866ff58f16 -->

<!-- course-file: scripts/repo/diagnostic-coverage/tsconfig.json -->

### tsconfig.json

[Open current source](../../../../../scripts/repo/diagnostic-coverage/tsconfig.json) · **Snapshot:** added (absent from baseline); 45 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Configures which sources/dependencies the test compiler can resolve.

**Before:** The existing compiler scope did not include all newly referenced diagnostic/security dependencies.

**After:** Extends the relevant compilation inputs or aliases for the tests; the JSON diff is the exact declaration change.

**Why:** Runtime tests must exercise the implementation that consumers actually import, rather than fail resolution or omit the new modules.

Proving boundary: inspect the affected file's registered inputs in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml) and its linked neighboring tests. Setup/export files are not independently operating services.

<!-- course-source-sha256: before=absent after=af453384cf12d6a8b998d732d735d7bdbf52e8ebbf5c08fa21c9216b35420af3 -->

<!-- course-file: scripts/repo/diagnostic-coverage/verify.sh -->

### verify.sh

[Open current source](../../../../../scripts/repo/diagnostic-coverage/verify.sh) · **Snapshot:** added (absent from baseline); 58 added / 0 removed lines. These are textual counts, not a count of new features.

**What it does:** Verify executable diagnostic contracts, exports, affected runtime boundaries and cross-language readers locally.

**Before:** This implementation/helper file was absent at the baseline; its surrounding capability may already have existed.

**After:** Updates the existing command/declaration and its safe failure or consumer boundary. Connected implementation context from the owner review (spanning related files): Independent ordinary-code discovery, source-matched adoption, code-owned target/security/observability/health exports, historical version retention and strict cross-language readers. Additive health/readiness identities retain exact phase/effect schemas and narrow operation/configuration/related-security readers.

**Why:** An agent changing a source must update its explanation and proof, not merely copy an old adopted label. Python must consume the same allowed values as TypeScript rather than hand-maintain another vocabulary.

Owning registered proof: `diagnostic-catalog-readers`, `security-cognito-diagnostics`, `security-shared-rate-limit-diagnostics`, `cloudwatch-observability-runtime`, `ecs-fargate-runtime`, `deployment-operation-diagnostics-regression`. Look up their exact commands and execution stages in [the check catalog](../../../../../scripts/repo/check-selection/checks.yml). A check name here identifies ownership, not a claim that this course ran it.

<!-- course-source-sha256: before=absent after=575c6dc698fe62af821eca3c738f1b62fccc64fa36fb5ba06f8657625aa93f3d -->

## Work through it together

Use the [30-minute core / 50-minute extension protocol](../facilitator-guide.md). The core follows one worked example; a large folder's remaining file entries continue in subsequent meetings rather than being marked covered by a quick skim.

1. Open each source link above, then read its before/after entry aloud in your own words. Mark each file separately in [the file checklist](../file-index.md).
2. Find one actual guard, call, declaration or assertion behind the explanation. For documentation/receipts, find the rule or evidence being recorded instead.
3. Answer: Why does a matching review hash not prove that the review made the right architectural judgment?
4. Trace one upstream owner and one downstream consumer. If a module has no deployed consumer, stop at its actual caller/test; do not invent one.
5. State what the observation proves, what stays unknown, and which sensitive values are deliberately absent.

**Debrief / answer direction:** Adopted/partial/support/legacy are evidence classifications, not a mathematical measure of diagnostic completeness. A strong answer distinguishes observed location, supported cause and effect; an unsupported certainty is not extra granularity.

## Evidence and boundaries

[Folder in the checkout](../../../../../scripts/repo/diagnostic-coverage) · [Baseline, current proof and deferrals](../sources-and-limits.md) · [Plain-language glossary](../glossary.md)

Neighboring folder lessons: [L170 scripts/repo/check-selection](170-scripts-repo-check-selection.md).

**Facilitator check:** begin with the concrete case, explain only the terms needed here, let the learner predict before showing the source, and do not mark the folder complete until all 10 file entries have been discussed. Clarify any source/annotation disagreement in the notes instead of explaining it away.
