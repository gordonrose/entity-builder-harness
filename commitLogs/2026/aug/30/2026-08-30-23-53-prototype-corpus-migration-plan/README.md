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
latest_commit_at_utc: 2026-08-31T19:42:58Z
latest_commit_sha: eac8713
chat_duration: 74981s (00:20:49:41)
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
- Started execution slice 4 by adding `docs/00.chat/adrs/` and moving
  chat-owned ADRs 0001, 0002, 0004, 0005, 0006, 0007, 0009, 0010, 0011,
  0013, 0014, 0019, and 0030 into the chat docs corpus with compatibility
  pointers.
- Started execution slice 5 by moving harness-owned ADRs 0003, 0008, 0012,
  0017, 0018, 0020, and 0021 into `docs/01.harness/adrs/`, adding
  `docs/06.shared/adrs/`, and moving shared ADR 0015 there with compatibility
  pointers.
- Started execution slice 6 by moving product source-material Markdown files,
  product architecture guide Markdown derivatives, and guide original PDFs
  into `docs/03.product/source-material/`.
- Added product source-material README artifacts, directory-level old-path
  compatibility pointers, a product architecture guide corpus gap, and a
  retirement record for removed exact prototype source-material paths.
- Updated product source projections, derivation reports, selector fixtures,
  rule source-derivation paths and hashes, recognition sources, source-root
  checks, explanation-readiness smoke expectations, and rulebook index
  discovery so moved product source material remains sectioned
  `source-explanation` evidence.
- Updated the artifact path migration checker and smoke test so governed
  RAG/rulebook retirement records can preserve old paths as audit evidence
  without counting as active old-path references.
- Started execution slice 7 by moving product structured rules and product
  task rule packs from the prototype corpus into `docs/03.product/rules/**`
  and `docs/03.product/rule-packs/**`.
- Added product rule and rule-pack README artifacts plus compatibility pointer
  READMEs at the old prototype roots.
- Updated harness forward guidance, active rule graph references, source
  derivation paths and hashes, migration-map statuses, generated recognition
  sources, rulebook index discovery, runtime smoke expectations, and the
  product rule retirement record.

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
- The full selector fixture matrix again ran silently during slice 6 and was
  stopped after several polling windows. The focused product source-material
  selector set passed 14/14 and remains the validation evidence for this slice.
- The generated rulebook index still reports one unrelated warning for
  `.agentic/shared/workflows/deployment-process.md` from
  `artifact.concern.mcp.server.deployment.architecture`; validators and smoke
  checks continue to pass.

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
- Chat ADRs 0001, 0002, 0004, 0005, 0006, 0007, 0009, 0010, 0011, 0013,
  0014, 0019, and 0030 are now canonical under `docs/00.chat/adrs/`.
- Active chat/public/education references to the moved chat ADR batch now use
  the canonical chat ADR paths.
- Harness ADRs 0003, 0008, 0012, 0017, 0018, 0020, and 0021 are now
  canonical under `docs/01.harness/adrs/`.
- Shared ADR 0015 is now canonical under `docs/06.shared/adrs/`.
- Active harness, chat, product-migration, retrieval-policy, and selector
  fixture references to the moved harness/shared ADR batch now use canonical
  owner-aligned paths.
- Product source material for packages/core, platform runtime obligations, and
  platform infra capability layering is now canonical under
  `docs/03.product/source-material/core/` and
  `docs/03.product/source-material/platform/`.
- Long-form product architecture guides and their original PDFs are now
  canonical product source evidence under
  `docs/03.product/source-material/guides/`.
- The moved long-form guides remain source material for explanation and future
  derivation; the new product architecture guide corpus gap records that their
  broad prose has not yet been reviewed into focused structured rules or
  selector fixtures.
- `generate-rulebook-index` now prevents explanation Markdown roots from being
  rediscovered as generic process sources, so moved source material is indexed
  through sectioned `source-explanation` chunks rather than whole-file
  `source-excerpt` chunks.
- Exact retired prototype source-material paths are covered by
  `.agentic/02.rag-rulebook/retirements/03.product/2026-08-31-product-source-material-paths.yml`.
- Artifact path migration checks exclude governed RAG/rulebook retirement
  records when searching for active old-path references.
- Product structured rules and product task rule packs are now canonical under
  `docs/03.product/rules/**` and `docs/03.product/rule-packs/**`.
- Old product rule and rule-pack prototype roots now contain compatibility
  pointer README artifacts, not duplicate product YAML.
- Active references to the moved product YAML artifacts now use canonical
  product corpus paths; exact retired prototype YAML paths are preserved in
  `.agentic/02.rag-rulebook/retirements/03.product/2026-08-31-product-rules-and-packs.yml`.
- `generate-rulebook-index` now skips live current-corpus YAML entries already
  represented by the migration map so migrated artifacts keep their mapped
  subcorpus metadata without duplicate discovered entries.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Execution slice 1 is covered by the governed corpus split plan, document placement standard, canonical product plan, compatibility pointer, refreshed recognition sources, root-discovery script updates, runtime freshness, and focused selector fixture coverage.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Execution slice 2 is covered by ADR 0032, the corpus split migration plan, product ADR canonical files and pointers, updated retrieval evidence, refreshed recognition sources, and focused selector fixture coverage.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Execution slice 3 is covered by ADR 0032, the corpus split migration plan, canonical RAG/rulebook and deploy ADR roots, old-path compatibility pointers, updated deploy evidence for ADR 0028, refreshed recognition sources, runtime freshness, and focused selector fixture coverage.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Execution slice 4 is covered by ADR 0032, the corpus split migration plan, the canonical chat ADR root, old-path compatibility pointers, updated chat/public/education references, refreshed recognition sources, runtime freshness, and focused chat selector fixture coverage.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Execution slice 5 is covered by ADR 0032, the corpus split migration plan, canonical harness and shared ADR roots, old-path compatibility pointers, updated active references, refreshed recognition sources, runtime freshness, and focused selector fixture coverage.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Execution slice 6 is covered by the corpus split migration plan, product source-material README artifacts, canonical product source-material files, directory compatibility pointers, source projection updates, the product guide corpus gap, the product source-material retirement record, refreshed recognition sources, runtime freshness, and focused selector fixture coverage.


- Decision: Record RAG knowledge disposition: covered
  Rationale: Execution slice 7 is covered by the corpus split migration plan, product rules and rule-pack README artifacts, canonical product structured rule YAML, canonical product task packs, old-root compatibility pointers, updated rule graph references, source derivation hash updates, the product rules retirement record, refreshed recognition sources, runtime freshness, and focused selector fixture coverage.

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
- Slice 4 work continues in the same chat-owned worktree. Old chat ADR paths
  now contain compatibility pointers, not duplicate ADR text.
- Slice 5 work continues in the same chat-owned worktree. Old harness/shared
  ADR paths now contain compatibility pointers, not duplicate ADR text.
- Slice 6 work continues in the same chat-owned worktree. Old source-material
  and guide roots now contain directory-level compatibility pointers, not
  duplicate source material.
- The three removed exact source-material paths have an accepted retirement
  record with prior SHA-256 hashes and replacement product paths.
- The moved product guide prose is intentionally tracked by a corpus gap until
  future source-to-rule review extracts focused product rules or explicit
  no-rule dispositions.
- Historical `commitLogs/**` references to old paths were left as audit
  history.
- Slice 7 work continues in the same chat-owned worktree. Old product rule and
  rule-pack roots now contain compatibility pointer READMEs, not duplicate
  product YAML.
- The moved product source-material hashes changed only because their metadata
  `used_by` paths now point at canonical product rule files.
- Historical `commitLogs/**` references to old product rule and rule-pack paths
  were left as audit history.

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

### 2026-08-31T01:32:22Z - Execution slice 4 started

Added `docs/00.chat/adrs/README.md` as the owner-aligned ADR root for chat
lifecycle and portable workbench decisions.

Moved chat-owned ADRs 0001, 0002, 0004, 0005, 0006, 0007, 0009, 0010, 0011,
0013, 0014, 0019, and 0030 to `docs/00.chat/adrs/`. Preserved stable
artifact IDs on canonical ADRs and left compatibility pointers at the old
prototype ADR paths.

Updated active references in chat workflow/public docs, education article
evidence, and the script-layout ADR to use the canonical chat ADR paths.

Focused path-migration checks passed for all 13 moved chat ADRs with approved
active old-path pointer compatibility.

Focused selector validation passed:

- `timeout 300 bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-chat-public-beta-portability.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-chat-session-metrics.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-chat-upstream-reusable-lesson.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-chat-worktree-recovery.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-chat-local-main-promotion.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-rag-commit-gates.yml`

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


### 2026-08-31T01:32:52Z - Decision

Decision: Record RAG knowledge disposition: covered

Rationale: Execution slice 4 is covered by ADR 0032, the corpus split migration plan, the canonical chat ADR root, old-path compatibility pointers, updated chat/public/education references, refreshed recognition sources, runtime freshness, and focused chat selector fixture coverage.


### 2026-08-31T01:36:43Z - Commit recorded

Commit: `b6c60e5`

Message: Move chat ADRs to chat corpus

Summary: Added the chat ADR root, moved chat-owned ADRs 0001, 0002, 0004, 0005, 0006, 0007, 0009, 0010, 0011, 0013, 0014, 0019, and 0030 into docs/00.chat/adrs with compatibility pointers, updated active chat/public/education references, and refreshed retrieval evidence.

ADR impact: ADR 0032 already records the owner-aligned ADR root decision; this slice applies it to the chat-owned ADR batch.

### 2026-08-31T11:55:56Z - Execution slice 5 started

Added `docs/06.shared/adrs/README.md` as the owner-aligned ADR root for
deliberately cross-layer shared decisions.

Moved harness-owned ADRs 0003, 0008, 0012, 0017, 0018, 0020, and 0021 to
`docs/01.harness/adrs/`. Moved shared ADR 0015 to `docs/06.shared/adrs/`.
Preserved stable artifact IDs on canonical ADRs and left compatibility
pointers at the old prototype ADR paths.

Updated active references in harness standards/workflows, chat public docs,
product migration planning, retrieval selector policy, and selector fixtures
to use the canonical harness/shared ADR paths.

Focused path-migration checks passed for all 8 moved harness/shared ADRs with
approved active old-path pointer compatibility.

Focused selector validation passed after updating the illustrative example
fixture to expect the canonical ADR 0021 selector artifact ID:

- `timeout 300 bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-harness-artifact-path-migration.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-missing-governance-stop-condition.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/illustrative-example-paths-deprioritized.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-chat-public-beta-portability.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/question-category-chat-upstream-reusable-lesson.yml`

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


### 2026-08-31T11:56:26Z - Decision

Decision: Record RAG knowledge disposition: covered

Rationale: Execution slice 5 is covered by ADR 0032, the corpus split migration plan, canonical harness and shared ADR roots, old-path compatibility pointers, updated active references, refreshed recognition sources, runtime freshness, and focused selector fixture coverage.


### 2026-08-31T12:04:50Z - Commit recorded

Commit: `9534f395e1955e83937985cf6c02416a1c473a98`

Message: Move harness and shared ADRs to owner corpora

Summary: Moved harness ADRs 0003, 0008, 0012, 0017, 0018, 0020, and 0021 to docs/01.harness/adrs and shared ADR 0015 to docs/06.shared/adrs with compatibility pointers, updated active references, and refreshed retrieval evidence.

ADR impact: ADR 0032 already records the owner-aligned ADR root decision; this slice applies it to the harness/shared ADR batch.

### 2026-08-31T12:31:51Z - Execution slice 6 started

Moved product source material to the owner-aligned product corpus:

- `docs/03.product/source-material/core/packages-core-contract-surface-v1.md`
- `docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md`
- `docs/03.product/source-material/platform/platform-infra-capability-layering-v1.md`

Moved seven long-form product architecture guide Markdown derivatives and their
original PDFs under `docs/03.product/source-material/guides/`. Added product
source-material README artifacts and directory-level compatibility pointers
under the old prototype source-material and guide roots.

Updated source projections, derivation reports, selector fixtures,
source-derivation paths and hashes, generated recognition sources, source-root
checks, and explanation-readiness smoke expectations. Added
`.agentic/02.rag-rulebook/corpus-gaps/03.product/product-architecture-guides.yml`
to track future focused source-to-rule review for broad product guide prose.

Added
`.agentic/02.rag-rulebook/retirements/03.product/2026-08-31-product-source-material-paths.yml`
for the three removed exact prototype source-material paths, including prior
SHA-256 hashes and replacement product source paths.

Adjusted `scripts/02.rag-rulebook/generate-rulebook-index/script.sh` so
migration-map Markdown entries and explanation Markdown roots are not
rediscovered as generic process-source artifacts. This keeps moved source
material indexed as bounded `source-explanation` sections instead of
whole-file `source-excerpt` evidence.

Adjusted `scripts/01.harness/check-artifact-path-migration.sh` and its smoke
test so RAG/rulebook retirement records are ignored as active old-path
references. The three direct source-material path migration checks passed
without an active old-path compatibility override.

Focused selector validation passed:

- `bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-audit-contract.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-contract-compatibility.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-contract-surface.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-diagnostics-self-healing.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-events-contract.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-files-contract.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-i18n-localization-contract.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-monitoring-contract.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-persistence-contract.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-queues-contract.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/packages-core-security-contract.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/platform-infra-capability-layering.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/platform-runtime-enterprise-obligations.yml --fixture .agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/platform-runtime-source-explanation.yml`

Validation passed:

- `bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check`
- `bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh`
- `bash scripts/02.rag-rulebook/check-source-projections/script.sh --current`
- `bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-retirement-records/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh --current`
- `bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh`
- `bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh --current`
- `bash scripts/02.rag-rulebook/audit-explanation-readiness/script.sh --current`
- `bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`
- `bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`
- `bash scripts/01.harness/smoke-test-artifact-path-migration.sh`
- `bash scripts/01.harness/check-artifact-path-migration.sh --plan .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md docs/harness/architecture/source-material/packages-core-contract-surface-v1.md docs/03.product/source-material/core/packages-core-contract-surface-v1.md`
- `bash scripts/01.harness/check-artifact-path-migration.sh --plan .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md docs/harness/architecture/source-material/platform-runtime-enterprise-obligations-v1.md docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md`
- `bash scripts/01.harness/check-artifact-path-migration.sh --plan .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md docs/harness/architecture/source-material/platform-infra-capability-layering-v1.md docs/03.product/source-material/platform/platform-infra-capability-layering-v1.md`
- `bash scripts/01.harness/check-governed-script-command-drift.sh`
- `git diff --check`

Non-blocking validation note:

- `bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh --current` was stopped after several silent polling windows with no report. The focused product source-material selector set passed 14/14.


### 2026-08-31T12:33:01Z - Decision

Decision: Record RAG knowledge disposition: covered

Rationale: Execution slice 6 is covered by the corpus split migration plan, product source-material README artifacts, canonical product source-material files, directory compatibility pointers, source projection updates, the product guide corpus gap, the product source-material retirement record, refreshed recognition sources, runtime freshness, and focused selector fixture coverage.


### 2026-08-31T12:41:40Z - Commit recorded

Commit: `e5a4cbd05636d470a3b6a244fcd2cfbd602717b1`

Message: Move product source material to product corpus

Summary: Moved product source-material Markdown files, long-form guide derivatives, and guide originals into docs/03.product/source-material; added product source-material READMEs, old-directory compatibility pointers, product guide corpus-gap tracking, retirement proof for exact old source paths, source projection updates, refreshed recognition evidence, and indexer/path-migration guard fixes.

ADR impact: No new ADR; this slice applies ADR 0032 and the accepted corpus split migration plan to product source material and guide evidence.

### 2026-08-31T19:37:14Z - Execution slice 7 started

Moved product structured rules into the owner-aligned product corpus:

- `docs/03.product/rules/apps/layers/apps.yml`
- `docs/03.product/rules/core/layers/packages-core.yml`
- `docs/03.product/rules/core/concerns/validation-api-errors.yml`
- `docs/03.product/rules/design-system/layers/design-system.yml`
- `docs/03.product/rules/design-system/concerns/design-label-theming.yml`
- `docs/03.product/rules/frontend-kit/layers/frontend-kit.yml`
- `docs/03.product/rules/platform/layers/platform.yml`
- `docs/03.product/rules/platform/concerns/config-runtime-settings.yml`
- `docs/03.product/rules/platform/concerns/events-messaging-async.yml`
- `docs/03.product/rules/platform/concerns/identity-access-security.yml`
- `docs/03.product/rules/platform/concerns/notifications.yml`
- `docs/03.product/rules/platform/concerns/persistence-files-storage.yml`
- `docs/03.product/rules/platform/concerns/platform-adapter-consumption.yml`
- `docs/03.product/rules/platform/concerns/platform-infra-capability-layering.yml`
- `docs/03.product/rules/platform/concerns/reporting-analytics-audit.yml`
- `docs/03.product/rules/platform/concerns/tenancy.yml`
- `docs/03.product/rules/concerns/i18n-localization.yml`

Moved product task rule packs into product subcorpora:

- `docs/03.product/rule-packs/apps/create-entity.yml`
- `docs/03.product/rule-packs/core/add-core-module.yml`
- `docs/03.product/rule-packs/design-system/add-design-system-component.yml`
- `docs/03.product/rule-packs/platform/add-platform-adapter.yml`

Added `docs/03.product/rules/README.md`,
`docs/03.product/rule-packs/README.md`,
`docs/harness/architecture/rules/README.md`, and
`docs/harness/architecture/rule-packs/README.md` so forward placement and
legacy compatibility are explicit.

Updated harness forward guidance, product ADR/source references,
source-derivation paths and hashes, rule-pack `required_rulesets`, migration
map statuses, generated recognition sources, runtime smoke expectations, and
the rulebook index generator's current-corpus YAML discovery.

Added
`.agentic/02.rag-rulebook/retirements/03.product/2026-08-31-product-rules-and-packs.yml`
for the removed exact prototype product YAML paths, including prior SHA-256
hashes and replacement product paths.

Focused selector validation passed:

- `bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh` with the 27 fixtures that cite `docs/03.product/rules` or `docs/03.product/rule-packs`.

Validation passed:

- `bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
- `bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check`
- `bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current`
- `bash scripts/02.rag-rulebook/check-source-projections/script.sh --current`
- `bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh --current`
- `bash scripts/02.rag-rulebook/validate-retirement-records/script.sh --current`
- `bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh --current`
- `bash scripts/02.rag-rulebook/audit-explanation-readiness/script.sh --current`
- `bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`
- `bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/build-local-runtime/script.sh`
- `bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh`
- `bash scripts/02.rag-rulebook/query-local-context/smoke-test.sh`
- `bash scripts/02.rag-rulebook/run-local-service/smoke-test.sh`
- `bash scripts/01.harness/check-governed-script-command-drift.sh`
- `git diff --check`

Concrete path-migration checks passed for all 21 moved product rule and
rule-pack source/target pairs. A focused stale-reference scan found no active
old product rule or rule-pack references outside governed retirement evidence
and historical session logs.

Non-blocking validation note:

- `bash scripts/02.rag-rulebook/validate-rulebook-index/script.sh --index /tmp/current-rulebook-index.json` passed with one unrelated warning for `.agentic/shared/workflows/deployment-process.md` from `artifact.concern.mcp.server.deployment.architecture`.


### 2026-08-31T19:37:44Z - Decision

Decision: Record RAG knowledge disposition: covered

Rationale: Execution slice 7 is covered by the corpus split migration plan,
product rules and rule-pack README artifacts, canonical product structured rule
YAML, canonical product task packs, old-root compatibility pointers, updated
rule graph references, source derivation hash updates, the product rules
retirement record, refreshed recognition sources, runtime freshness, and
focused selector fixture coverage.


### 2026-08-31T19:42:58Z - Commit recorded

Commit: `eac8713`

Message: Move product rules and packs to product corpus

Summary: Moved product structured rules and product task rule packs into docs/03.product/rules and docs/03.product/rule-packs with compatibility pointers, updated harness guidance, rule graph references, source derivation hashes, migration metadata, generated recognition evidence, and rulebook index discovery.

ADR impact: No new ADR; this slice applies ADR 0032 and the accepted corpus split migration plan to product rules, product task packs, and old-path compatibility.

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


- Commit: `b6c60e5`
  Time UTC: 2026-08-31T01:36:43Z
  Message: Move chat ADRs to chat corpus
  Summary: Added the chat ADR root, moved chat-owned ADRs 0001, 0002, 0004, 0005, 0006, 0007, 0009, 0010, 0011, 0013, 0014, 0019, and 0030 into docs/00.chat/adrs with compatibility pointers, updated active chat/public/education references, and refreshed retrieval evidence.
  ADR impact: ADR 0032 already records the owner-aligned ADR root decision; this slice applies it to the chat-owned ADR batch.


- Commit: `9534f395e1955e83937985cf6c02416a1c473a98`
  Time UTC: 2026-08-31T12:04:50Z
  Message: Move harness and shared ADRs to owner corpora
  Summary: Moved harness ADRs 0003, 0008, 0012, 0017, 0018, 0020, and 0021 to docs/01.harness/adrs and shared ADR 0015 to docs/06.shared/adrs with compatibility pointers, updated active references, and refreshed retrieval evidence.
  ADR impact: ADR 0032 already records the owner-aligned ADR root decision; this slice applies it to the harness/shared ADR batch.


- Commit: `e5a4cbd05636d470a3b6a244fcd2cfbd602717b1`
  Time UTC: 2026-08-31T12:41:40Z
  Message: Move product source material to product corpus
  Summary: Moved product source-material Markdown files, long-form guide derivatives, and guide originals into docs/03.product/source-material; added product source-material READMEs, old-directory compatibility pointers, product guide corpus-gap tracking, retirement proof for exact old source paths, source projection updates, refreshed recognition evidence, and indexer/path-migration guard fixes.
  ADR impact: No new ADR; this slice applies ADR 0032 and the accepted corpus split migration plan to product source material and guide evidence.


- Commit: `eac8713`
  Time UTC: 2026-08-31T19:42:58Z
  Message: Move product rules and packs to product corpus
  Summary: Moved product structured rules and product task rule packs into docs/03.product/rules and docs/03.product/rule-packs with compatibility pointers, updated harness guidance, rule graph references, source derivation hashes, migration metadata, generated recognition evidence, and rulebook index discovery.
  ADR impact: No new ADR; this slice applies ADR 0032 and the accepted corpus split migration plan to product rules, product task packs, and old-path compatibility.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/01.harness/adrs/0032-use-owner-aligned-adr-roots.md
Reason: ADR 0032 records the owner-aligned ADR root decision. Execution slice
7 applies that accepted decision to product structured rules, product task
rule packs, and old-path compatibility without introducing a new ADR-level
policy change.

## Session Metrics

Raised at UTC: 2026-08-30T22:53:17Z
Latest commit at UTC: 2026-08-31T19:42:58Z
Latest commit SHA: eac8713
Chat duration: 74981s (00:20:49:41)
Estimated chat tokens: unavailable; transcript source not supplied by chat
Estimated chat cost: unavailable; estimated chat tokens are unavailable
Estimated chat cost basis: unavailable; estimated chat tokens are unavailable

## Notes

- None recorded yet.

## RAG Knowledge Disposition

Status: covered
Reason: Execution slice 7 is covered by the corpus split migration plan, product rules and rule-pack README artifacts, canonical product structured rule YAML, canonical product task packs, old-root compatibility pointers, updated rule graph references, source derivation hash updates, the product rules retirement record, refreshed recognition sources, runtime freshness, and focused selector fixture coverage.
Evidence:
- .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
- docs/03.product/rules/README.md
- docs/03.product/rule-packs/README.md
- docs/03.product/rules/platform/layers/platform.yml
- docs/03.product/rules/core/layers/packages-core.yml
- docs/03.product/rules/apps/layers/apps.yml
- docs/03.product/rule-packs/platform/add-platform-adapter.yml
- docs/03.product/rule-packs/core/add-core-module.yml
- .agentic/02.rag-rulebook/source-projections/v1.yml
- .agentic/02.rag-rulebook/retirements/03.product/2026-08-31-product-rules-and-packs.yml
- .agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml
Corpus gaps:
- None.
