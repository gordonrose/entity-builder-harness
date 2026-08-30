<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.migration-plan.agentic-product-namespace
version: 1
status: active
layer: 03.product
domain: migration
disciplines:
- agentic
- architecture
kind: migration-plan
purpose: Track migration from the legacy .agentic/product governance path to the canonical .agentic/03.product layer path.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
- id: harness.architecture.adr.0018-govern-artifact-path-migrations
  path: docs/harness/architecture/adrs/0018-govern-artifact-path-migrations.md
-->
# 03.product Agentic Namespace Migration

## Purpose

Move product-layer governance from `.agentic/product/` to the canonical
numbered layer path `.agentic/03.product/`.

The commit log records chat activity. This plan is the durable coordination
artifact for the migration and may be updated across sessions.

## Scope

- Old path: `.agentic/product`
- New path: `.agentic/03.product`
- Matching script namespace: `scripts/product` to `scripts/03.product`
- Compatibility choice: `retired`
- Historical session logs: leave unchanged as audit history

The matching script namespace has no `scripts/product` source path today.
`scripts/03.product` is already the reserved future product command surface.

## Status

Complete on 2026-08-30.

Final planner state:

- `.agentic/product` no longer exists.
- `.agentic/03.product` exists and owns the product layer README, workflow index,
  product workflows, and this migration plan.
- Old `.agentic/product` references remain only in this migration plan and
  historical `commitLogs/` entries.
- Old `scripts/product` references remain only in this migration plan.

## Initial Reference Inventory

<!-- deterministic-check: allow reason="this section records planner output evidence; executable validation is listed separately" -->
Recorded before edits on 2026-08-30:

- `.agentic/product -> .agentic/03.product`: old path exists, new path did not
  exist before creating this plan, and the planner found 64 old-path references.
- `scripts/product -> scripts/03.product`: old path does not exist, new path does
  not exist, and the planner found no old-path references.

Active `.agentic/product` references were found in:

- routing: `AGENTS.md` and `.agentic/routing-policy.yaml`
- workflow and fixture sources under `.agentic/`
- scripts under `scripts/00.chat`, `scripts/01.harness`, and
  `scripts/02.rag-rulebook`
- bootstrap documentation and export scripts
- architecture ADRs and the platform runtime implementation plan
- generated RAG recognition sources

Session-history references under `commitLogs/` are intentionally not migrated.

## Plan

1. Complete: update artifact-path migration governance so harness-built plans are
   standalone artifacts under `plans/migration/` or `plans/implementation/`.
2. Complete: update migration helper scripts so an explicit migration-plan
   artifact can mention the old path without masking other active old-path
   references.
3. Complete: move product governance workflows into
   `.agentic/03.product/workflows/`.
4. Complete: add product layer and workflow indexes under `.agentic/03.product/`.
5. Complete: update active references from `.agentic/product` to
   `.agentic/03.product`.
6. Complete: regenerate generated RAG recognition sources.
7. Complete: validate the artifact path migration, metadata headers, generated
   sources, and affected smoke tests.

## Validation Plan

- Passed: `bash scripts/01.harness/smoke-test-artifact-path-migration.sh`
- Passed: `bash scripts/01.harness/check-artifact-path-migration.sh --plan .agentic/03.product/plans/migration/agentic-product-namespace.md .agentic/product .agentic/03.product`
- Passed: `bash scripts/01.harness/check-artifact-path-migration.sh --plan .agentic/03.product/plans/migration/agentic-product-namespace.md scripts/product scripts/03.product`
- Passed: `bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all`
- Passed: `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check`
- Passed: `bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`
- Passed: `bash scripts/02.rag-rulebook/generate-retrieval-selector-fixture/smoke-test.sh`
- Passed: `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/query-local-context/smoke-test.sh`
- Passed: `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/run-local-service/smoke-test.sh`
- Passed: `bash scripts/00.chat/classification/classify-task/check-fixtures.sh`
- Passed: `git diff --check`

## Recovery

If validation fails because active references still rely on the legacy path,
update those references to `.agentic/03.product` or explicitly choose a
temporary pointer/alias before treating the migration as complete.
