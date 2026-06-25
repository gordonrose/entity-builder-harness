<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: layer-readme
purpose: Define the RAG and rulebook layer boundary for standalone corpus, retrieval, and context-packet work.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: repo.agents
  path: AGENTS.md
- id: shared.routing-policy
  path: .agentic/routing-policy.yaml
-->
# 02.rag-rulebook Layer

## Purpose

Own reusable RAG and rulebook machinery.

This layer covers turning source material into structured rulebooks, defining
intent and context-packet schemas, building indexes and graph relationships,
chunking rulebook artifacts, and designing standalone retrieval services that
can serve multiple domain corpora.

## Boundary

This layer owns the reusable rulebook/RAG system, not every domain corpus.

Domain corpus IDs should align with the numbered layer system:

- `corpus.00.chat` for chat lifecycle and git governance
- `corpus.01.harness` for agentic harness work
- `corpus.02.rag-rulebook` for the RAG/rulebook service itself
- `corpus.03.product` for product, platform, apps, and design-system work
- `corpus.04.deploy` for infrastructure, release, and runtime operations
- `corpus.05.education` for teaching and publishing work
- `corpus.06.shared` for cross-layer process primitives

The RAG/rulebook service may index those corpora, but it should not merge them
into one undifferentiated instruction set.

Subcorpora may be introduced when a layer needs more precision, such as
`corpus.03.product.apps`, `corpus.03.product.design-system`, or
`corpus.03.product.platform`.

## Source Of Truth

- Layer workflows: `.agentic/02.rag-rulebook/workflows/`
- Layer standards: `.agentic/02.rag-rulebook/standards/`
- Layer schemas: `.agentic/02.rag-rulebook/schemas/`
- Layer plans: `.agentic/02.rag-rulebook/plans/`
- Layer command surface: `scripts/02.rag-rulebook/`
- Current prototype rulebook artifacts: `docs/harness/architecture/`

The current architecture YAMLs under `docs/harness/architecture/` are treated
as a prototype corpus until a governed migration gives domain rulebooks their
final homes.

## Workflows

- `workflows/default.md` - plan or change RAG/rulebook schemas, corpora,
  indexes, graph retrieval, context packets, or standalone service boundaries.

## Standards

- `standards/portable-service-contract.md` - defines the reusable service
  boundary for corpus, index, chunk, intent, retrieval, and context-packet work.
- `standards/domain-corpus-package.md` - defines the modular corpus package
  shape for numbered corpora and subcorpora.

## Schemas

- `schemas/context-packet.schema.yml` - defines the v1 context-packet contract
  returned by the portable RAG/rulebook service.

## Plans

- `plans/repo-plan.md` - records the ordered plan for turning the prototype
  rulebook into modular RAG-ready corpora and service inputs.

## Output Locations

Do not create a RAG server, MCP server, or new domain corpus without explicit
task scope.

When durable output locations are introduced, prefer modular corpus roots over
placing product, design-system, deploy, and harness rules together under one
harness-owned docs tree.
