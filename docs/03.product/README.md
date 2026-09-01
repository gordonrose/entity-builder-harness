<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.corpus.readme
version: 1
status: active
layer: 03.product
domain: requirements
disciplines:
- agentic
- architecture
kind: corpus-readme
purpose: Define the RAG-readable product corpus boundary for product source material, rules, rule packs, and runtime contract knowledge.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.standards.document-artifact-placement
  path: .agentic/01.harness/standards/document-artifact-placement.md
- id: rag-rulebook.standard.domain-corpus-package
  path: .agentic/02.rag-rulebook/standards/domain-corpus-package.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# 03.product Corpus

This directory is the RAG-readable product corpus package for
`corpus.03.product` and its product subcorpora.

The governing workflows for product and runtime-contract work live under
`.agentic/03.product/`. Runtime contract source code remains under product
implementation paths such as `packages/core/` and `platform/contracts/`. This
directory contains product source material and structured rulebook content that
the RAG/rulebook service can index, chunk, cite, and evaluate.

Use this corpus for product architecture guides, product source material,
apps rules, packages/core rules, design-system rules, frontend-kit rules,
platform/runtime rules, product task rule packs, and product-owned ADRs.

Product ADRs live under `adrs/`. Product guides and source material live under
`source-material/`. Product structured rules live under `rules/`. Product task
rule packs live under `rule-packs/`.

Product corpus material may be subdivided by owner topic, including `apps`,
`core`, `design-system`, `frontend-kit`, and `platform`.

Do not store deployment operations, infrastructure runbooks, or RAG/rulebook
service machinery here unless the material is product-facing source evidence
for a product rule.

The legacy prototype architecture corpus has been retired after its content
moved to owner-aligned roots.
