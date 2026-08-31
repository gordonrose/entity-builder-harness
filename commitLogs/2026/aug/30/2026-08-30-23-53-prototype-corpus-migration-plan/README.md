# Chat Session: 2026-08-30-23-53 prototype-corpus-migration-plan

<!-- agentic-session
id: 2026-08-30-23-53-is-this-folder-home-owner-projects-entity-builder-harness-00
task: is this folder (/home/owner/projects/entity-builder-harness-001/docs/harness/architecture) in a location that doesn't align with our repo layering approach? It feels like the adrs, guides, source material and plans should exist under product and the rule-packs and rules should exist under rag-rulebook no?
branch: chat/2026-08-30-23-53-is-this-folder-home-owner-projects-entity-builder-harness-00
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-08-30-23-53-is-this-folder-home-owner-projects-entity-builder-harness-00-3903744130
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-08-30T22:53:17Z
transcript_provider: 
transcript_path: 
transcript_bytes: 
transcript_source: 
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-08-31T01:21:36Z
latest_commit_sha: adc3cea
chat_duration: 8899s (00:02:28:19)
estimated_chat_tokens: unavailable; transcript source not supplied by chat
estimated_chat_cost: unavailable; estimated chat tokens are unavailable
estimated_chat_cost_basis: unavailable; estimated chat tokens are unavailable
-->

## Initial Intent

is this folder (/home/owner/projects/entity-builder-harness-001/docs/harness/architecture) in a location that doesn't align with our repo layering approach? It feels like the adrs, guides, source material and plans should exist under product and the rule-packs and rules should exist under rag-rulebook no?

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.
- Built the prototype corpus domain-split migration plan.
- Added a harness document-artifact placement standard for future ADRs, guides,
  source material, plans, rules, rule packs, and corpus docs.
- Wired the placement standard into the harness change workflow, harness
  README, artifact standard, terminology hints, and corpus migration plan.
- Refreshed generated artifact recognition sources for the new plan artifact.
- Validated metadata headers, recognition-source freshness, source projections,
  source-material coverage, rulebook index smoke, chunk generator smoke, and
  diff whitespace.
- Committed the planning/governance slice and began execution slice 1.
- Initialized the `docs/01.harness/`, `docs/03.product/`, and
  `docs/06.shared/` corpus roots with READMEs.
- Registered the new roots with metadata, recognition, corpus-root,
  source-material, runtime, YAML, explanation-readiness, and retirement
  reference checks.
- Moved the platform runtime implementation plan into the product layer and
  left a compatibility pointer at the old path.
- Rebuilt the local runtime and validated execution slice 1 with corpus,
  metadata, recognition, projection, derivation, explanation-readiness,
  migration-helper, and focused selector checks.
- Started execution slice 2 by adding ADR 0032 for owner-aligned ADR roots,
  updating the commit readiness gate to accept numbered ADR roots, and moving
  the first product-owned ADR batch into `docs/03.product/adrs/`.
- Started execution slice 3 by initializing the RAG/rulebook docs corpus root,
  adding RAG/rulebook and deploy ADR root READMEs, and moving ADRs 0016, 0022,
  0023, 0028, and 0029 into owner-aligned ADR roots with compatibility
  pointers.

## Questions Asked

- None recorded yet.

## Issues Raised

- The full retrieval selector fixture matrix did not finish within a
  10-minute bounded run and emitted no report. The focused migration selector
  set passed 5/5; treat the broad matrix runtime as a follow-up rather than a
  blocker for this focused migration slice.
- The first focused selector run after moving product ADRs failed because one
  product-contract fixture path replacement malformed a YAML list item and the
  app-mount fixture needed a clearer prompt phrase to keep the composition-root
  rule selected under the 12-chunk limit. Both fixture issues were corrected
  and the focused set passed 4/4.

## Decisions Made

- Treat `docs/harness/architecture` as the prototype corpus that should split
  by numbered owner corpus through governed artifact path migration.
- Place the durable migration plan under
  `.agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md`
  because the work is corpus packaging and source-projection coordination.
- Use pointer compatibility for old prototype paths during execution slices;
  do not move corpus files in the planning slice.
- Keep RAG/rulebook as owner of retrieval machinery and its self-corpus, not as
  the destination for every product, deploy, or harness rule.
- Route new document artifacts through
  `.agentic/01.harness/standards/document-artifact-placement.md` so future
  work uses owner-aligned layer and corpus paths instead of extending
  `docs/harness/architecture/**`.
- Treat missing numbered docs roots as governed setup work; create the root
  README, metadata allowlist support, and corpus wiring before placing ordinary
  content there.
- `docs/01.harness/`, `docs/03.product/`, and `docs/06.shared/` are now
  initialized corpus roots for forward placement.
- The platform runtime implementation plan remains stable as artifact
  `harness.architecture.plan.platform-runtime-implementation`, but its
  canonical path is now
  `.agentic/03.product/plans/implementation/platform-runtime-implementation.md`.
- Owner-aligned ADR roots are now the durable target for new and migrated
  corpus-history ADRs. The commit readiness gate accepts
  `docs/<numbered-layer>/adrs/*.md` while retaining legacy
  `docs/<track>/architecture/adrs/*.md` roots during migration.
- Product ADRs 0024, 0025, 0026, 0027, and 0031 are now canonical under
  `docs/03.product/adrs/` with stable artifact IDs preserved and old-path
  compatibility pointers left in `docs/harness/architecture/adrs/`.
- ADR 0019 remains accepted for the chat docs namespace, but its centralized
  ADR storage clause is superseded by ADR 0032.
- RAG/rulebook ADRs 0022, 0023, and 0029 are now canonical under
  `docs/02.rag-rulebook/adrs/`; deploy ADRs 0016 and 0028 are now canonical
  under `docs/04.deploy/adrs/`.
- `docs/02.rag-rulebook/` is initialized as the RAG-readable self-corpus root
  for RAG/rulebook source material, ADRs, and structured rules.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Execution slice 1 is covered by the governed corpus split plan, document placement standard, canonical product plan, compatibility pointer, refreshed recognition sources, root-discovery script updates, runtime freshness, and focused selector fixture coverage.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Execution slice 2 is covered by ADR 0032, the corpus split migration plan, product ADR canonical files and pointers, updated retrieval evidence, refreshed recognition sources, and focused selector fixture coverage.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Execution slice 3 is covered by ADR 0032, the corpus split migration plan, canonical RAG/rulebook and deploy ADR roots, old-path compatibility pointers, updated deploy evidence for ADR 0028, refreshed recognition sources, runtime freshness, and focused selector fixture coverage.

## Context Hygiene

- Work performed in the chat-owned worktree:
  `/tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-08-30-23-53-is-this-folder-home-owner-projects-entity-builder-harness-00-3903744130`.
- Root checkout had an unrelated `package-lock.json` modification; it was not
  touched in this slice.
- `docs/harness/architecture/**` files were not moved or edited.
- Generated recognition sources were updated because new indexed artifacts were
  added.
- The old platform runtime implementation plan path now contains a
  compatibility pointer, not a duplicate plan.
- Slice 2 work continues in the same chat-owned worktree. Old product ADR
  paths now contain compatibility pointers, not duplicate ADR text.
- Slice 3 work continues in the same chat-owned worktree. Old RAG/rulebook and
  deploy ADR paths now contain compatibility pointers, not duplicate ADR text.
- Historical `commitLogs/**` references to old paths were left as audit
  history.

## Activity Log

### 2026-08-30T22:53:17Z - Session started

Initial intent: is this folder (/home/owner/projects/entity-builder-harness-001/docs/harness/architecture) in a location that doesn't align with our repo layering approach? It feels like the adrs, guides, source material and plans should exist under product and the rule-packs and rules should exist under rag-rulebook no?

### 2026-08-30T23:01:35Z - Migration plan built

Created `.agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md`
as the durable, governed plan for splitting the prototype
`docs/harness/architecture` corpus into numbered domain corpus homes. Updated
the RAG/rulebook README, repo plan, existing prototype migration map, and
generated artifact recognition source to reference the new plan.

Validation passed:

- `bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check`
- `bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`
- `bash scripts/02.rag-rulebook/check-source-projections/script.sh --current`
- `bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current`
- `bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`
- `bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current`
- `git diff --check`

### 2026-08-30T23:12:40Z - Forward document placement governed

Created
`.agentic/01.harness/standards/document-artifact-placement.md` as the durable
harness rule for placing new document artifacts by owner layer and corpus.
Updated `.agentic/01.harness/workflows/change-harness.md`,
`.agentic/01.harness/README.md`,
`.agentic/01.harness/standards/agentic-artifact-standards.md`,
`.agentic/01.harness/standards/repo-terminology.md`, and
`.agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md`
to make the standard discoverable during future harness and corpus work.

Regenerated recognition sources with:

- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --write-all`

Validation passed:

- `bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check`
- `bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current`
- `bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`
- `bash scripts/02.rag-rulebook/check-source-projections/script.sh --current`
- `bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current`
- `bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`
- `git diff --check`


### 2026-08-31T00:01:48Z - Commit recorded

Commit: `95e7534`

Message: Plan prototype corpus domain split

Summary: Added the prototype corpus domain-split migration plan, a harness document-artifact placement standard, and refreshed generated recognition sources.

ADR impact: No ADR created; the slice planned the migration and added governance without moving durable docs roots.

### 2026-08-31T00:11:14Z - Execution slice 1 started

Committed the planning/governance slice as `95e7534` and checkpointed session
bookkeeping as `b3f5eac`.

Initialized these corpus roots:

- `docs/01.harness/`
- `docs/03.product/`
- `docs/06.shared/`

Updated deterministic root discovery and validation surfaces for the new roots:

- metadata header checks and artifact index generation;
- deterministic process and governed-script drift scanners;
- rulebook index default corpus roots;
- corpus-root change detection;
- source-material coverage;
- local runtime fingerprints;
- YAML syntax validation;
- explanation-readiness audit;
- retirement active-reference scanning.

Moved
`docs/harness/architecture/plans/platform-runtime-implementation-plan.md` to
`.agentic/03.product/plans/implementation/platform-runtime-implementation.md`
and left a compatibility pointer at the old path.

Focused migration check passed with approved pointer compatibility:

- `bash scripts/01.harness/check-artifact-path-migration.sh --plan .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md --allow-active-old-path docs/harness/architecture/plans/platform-runtime-implementation-plan.md .agentic/03.product/plans/implementation/platform-runtime-implementation.md`

Validation passed:

- `bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check`
- `bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current`
- `bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`
- `bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`
- `bash scripts/02.rag-rulebook/check-source-projections/script.sh --current`
- `bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh --current`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty`
- `bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh`
- `bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh`
- `bash scripts/02.rag-rulebook/audit-explanation-readiness/script.sh --current`
- `bash scripts/01.harness/smoke-test-artifact-path-migration.sh`
- `timeout 300 bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-harness-artifact-path-migration.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-domain-corpus-package.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-product-contract-surface.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-aws-workflow-split.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/platform-runtime-source-explanation.yml`
- `git diff --check`

Non-blocking validation note:

- `timeout 600 bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh --current` exited `124` with no report.


### 2026-08-31T00:35:13Z - Decision

Decision: Record RAG knowledge disposition: covered

Rationale: Execution slice 1 is covered by the governed corpus split plan, document placement standard, canonical product plan, compatibility pointer, refreshed recognition sources, root-discovery script updates, runtime freshness, and focused selector fixture coverage.


### 2026-08-31T00:38:33Z - Commit recorded

Commit: `087415a`

Message: Execute prototype corpus split slice 1

Summary: Initialized numbered corpus roots, registered root-discovery checks, moved the platform runtime plan to product governance, left a compatibility pointer, and refreshed generated recognition sources.

ADR impact: No new ADR; this starts the governed corpus split without retiring the prototype root.

### 2026-08-31T00:48:00Z - Execution slice 2 started

Added `docs/01.harness/adrs/0032-use-owner-aligned-adr-roots.md` to record
the owner-aligned ADR root decision. Added ADR root READMEs for
`docs/01.harness/adrs/` and `docs/03.product/adrs/`.

Updated the chat commit readiness gate, its smoke test, and its documentation
so ADR disposition accepts numbered ADR roots such as
`docs/01.harness/adrs/` as well as legacy transition roots such as
`docs/harness/architecture/adrs/`.

Moved product-owned ADRs 0024, 0025, 0026, 0027, and 0031 to
`docs/03.product/adrs/`, preserved their stable artifact IDs, updated active
RAG references for product-contract and app-mount evidence, and left
compatibility pointers at the old prototype ADR paths.

Focused selector validation passed after correcting product ADR path
expectations:

- `timeout 300 bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-product-contract-surface.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/platform-runtime-enterprise-obligations.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/platform-app-mount-boundary.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-domain-corpus-package.yml`

Validation passed:

- `bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
- `bash scripts/00.chat/session-log/prepare-chat-session-before-commit/smoke-test.sh`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check`
- `bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh`
- `bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`
- `bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`
- `bash scripts/02.rag-rulebook/check-source-projections/script.sh --current`
- `bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh --current`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty`
- `bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh`
- `bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh --current`
- `bash scripts/02.rag-rulebook/audit-explanation-readiness/script.sh --current`
- `bash scripts/01.harness/smoke-test-artifact-path-migration.sh`
- `bash scripts/01.harness/check-governed-script-command-drift.sh`
- `git diff --check`


### 2026-08-31T01:02:35Z - Decision

Decision: Record RAG knowledge disposition: covered

Rationale: Execution slice 2 is covered by ADR 0032, the corpus split migration plan, product ADR canonical files and pointers, updated retrieval evidence, refreshed recognition sources, and focused selector fixture coverage.


### 2026-08-31T01:07:37Z - Commit recorded

Commit: `e253afa`

Message: Move product ADRs to product corpus

Summary: Added ADR 0032 for owner-aligned ADR roots, updated commit readiness to accept numbered ADR paths, moved product ADRs 0024, 0025, 0026, 0027, and 0031 to docs/03.product/adrs with compatibility pointers, and refreshed retrieval evidence.

ADR impact: ADR 0032 records the durable owner-aligned ADR root decision.

### 2026-08-31T01:13:09Z - Execution slice 3 started

Initialized `docs/02.rag-rulebook/`, `docs/02.rag-rulebook/adrs/`, and
`docs/04.deploy/adrs/` corpus README artifacts.

Moved RAG/rulebook ADRs 0022, 0023, and 0029 to
`docs/02.rag-rulebook/adrs/`. Moved deploy ADRs 0016 and 0028 to
`docs/04.deploy/adrs/`. Preserved stable artifact IDs on the canonical ADRs
and left compatibility pointers at the old prototype ADR paths.

Updated active deployment evidence that cited ADR 0028 so source material,
structured deploy rules, derivation reports, and the planning-only infra
decision manifest point at the canonical deploy ADR path.

Focused path-migration checks passed for ADRs 0016, 0022, 0023, 0028, and
0029 with approved active old-path pointer compatibility.

Focused selector validation passed:

- `timeout 300 bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-rag-retrieval-source-of-truth.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-rag-index-selection.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-aws-workflow-split.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/deploy-planning-ecs-fargate.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-rag-commit-gates.yml`

Validation passed:

- `bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check`
- `bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh`
- `bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`
- `bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`
- `bash scripts/02.rag-rulebook/check-source-projections/script.sh --current`
- `bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh --current`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty`
- `bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh`
- `bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh --current`
- `bash scripts/02.rag-rulebook/audit-explanation-readiness/script.sh --current`
- `bash scripts/01.harness/smoke-test-artifact-path-migration.sh`
- `bash scripts/01.harness/check-governed-script-command-drift.sh`
- `git diff --check`


### 2026-08-31T01:17:07Z - Decision

Decision: Record RAG knowledge disposition: covered

Rationale: Execution slice 3 is covered by ADR 0032, the corpus split migration plan, canonical RAG/rulebook and deploy ADR roots, old-path compatibility pointers, updated deploy evidence for ADR 0028, refreshed recognition sources, runtime freshness, and focused selector fixture coverage.


### 2026-08-31T01:21:36Z - Commit recorded

Commit: `adc3cea`

Message: Move RAG and deploy ADRs to owner corpora

Summary: Moved RAG ADRs 0022, 0023, and 0029 plus deploy ADRs 0016 and 0028 into owner-aligned ADR roots with compatibility pointers and refreshed RAG/deploy evidence.

ADR impact: ADR 0032 already records the owner-aligned ADR root decision; this slice applies it to the RAG/deploy batch.

## Sub-Agent Activity

- None recorded yet.

## Commits



- Commit: `95e7534`
  Time UTC: 2026-08-31T00:01:48Z
  Message: Plan prototype corpus domain split
  Summary: Added the prototype corpus domain-split migration plan, a harness document-artifact placement standard, and refreshed generated recognition sources.
  ADR impact: No ADR created; the slice planned the migration and added governance without moving durable docs roots.


- Commit: `087415a`
  Time UTC: 2026-08-31T00:38:33Z
  Message: Execute prototype corpus split slice 1
  Summary: Initialized numbered corpus roots, registered root-discovery checks, moved the platform runtime plan to product governance, left a compatibility pointer, and refreshed generated recognition sources.
  ADR impact: No new ADR; this starts the governed corpus split without retiring the prototype root.


- Commit: `e253afa`
  Time UTC: 2026-08-31T01:07:37Z
  Message: Move product ADRs to product corpus
  Summary: Added ADR 0032 for owner-aligned ADR roots, updated commit readiness to accept numbered ADR paths, moved product ADRs 0024, 0025, 0026, 0027, and 0031 to docs/03.product/adrs with compatibility pointers, and refreshed retrieval evidence.
  ADR impact: ADR 0032 records the durable owner-aligned ADR root decision.


- Commit: `adc3cea`
  Time UTC: 2026-08-31T01:21:36Z
  Message: Move RAG and deploy ADRs to owner corpora
  Summary: Moved RAG ADRs 0022, 0023, and 0029 plus deploy ADRs 0016 and 0028 into owner-aligned ADR roots with compatibility pointers and refreshed RAG/deploy evidence.
  ADR impact: ADR 0032 already records the owner-aligned ADR root decision; this slice applies it to the RAG/deploy batch.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/01.harness/adrs/0032-use-owner-aligned-adr-roots.md
Reason: ADR 0032 records the owner-aligned ADR root decision. Execution slice
3 applies that accepted decision to the RAG/rulebook and deploy ADR batch
without introducing a new ADR-level policy change.

## Session Metrics

Raised at UTC: 2026-08-30T22:53:17Z
Latest commit at UTC: 2026-08-31T01:21:36Z
Latest commit SHA: adc3cea
Chat duration: 8899s (00:02:28:19)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- None recorded yet.

## RAG Knowledge Disposition

Status: covered
Reason: Execution slice 3 is covered by ADR 0032, the corpus split migration plan, canonical RAG/rulebook and deploy ADR roots, old-path compatibility pointers, updated deploy evidence for ADR 0028, refreshed recognition sources, runtime freshness, and focused selector fixture coverage.
Evidence:
- .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
- docs/01.harness/adrs/0032-use-owner-aligned-adr-roots.md
- docs/02.rag-rulebook/README.md
- docs/02.rag-rulebook/adrs/0022-add-rag-rulebook-layer.md
- docs/02.rag-rulebook/adrs/0023-require-rag-knowledge-disposition-for-code-changes.md
- docs/02.rag-rulebook/adrs/0029-use-purpose-and-authority-aware-rag-retrieval.md
- docs/04.deploy/adrs/0016-add-aws-layer.md
- docs/04.deploy/adrs/0028-use-client-environment-deployment-target-profiles.md
- .agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml
- .agentic/02.rag-rulebook/derivation-reports/04.deploy/2026-07-10-platform-shell-runtime-family.yml
- docs/04.deploy/rules/03.product/platform-shell-runtime-family.yml
Corpus gaps:
- None.
