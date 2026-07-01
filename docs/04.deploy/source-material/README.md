<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: source-material-readme
purpose: Define the holding area for deploy corpus source material before structured rulebook conversion.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.corpus.readme
  path: docs/04.deploy/README.md
- id: rag-rulebook.corpus-gap.04-deploy.mcp-server-deployment
  path: .agentic/02.rag-rulebook/corpus-gaps/04.deploy/mcp-server-deployment.yml
-->
# Deploy Source Material

This directory holds human-readable deploy source material before it becomes
structured YAML rules, generated chunks, and retrieval selector evaluations.

Source material is allowed to be explanatory, but it must be precise enough to
convert into rules, checks, stop conditions, rollback expectations, and named
gaps.

Source material does not authorize deployment or AWS mutation.

## Tracks

Use tracks so deployment guidance stays narrow:

- `shared/` contains reusable deployment source material, such as GitHub to AWS
  boundaries, identity, observability, rollback, and release control.
- `00.chat/` contains deployment source material for chat startup, git
  governance, and LLM Workbench style services.
- `02.rag-rulebook/` contains deployment source material for local or remote
  RAG/rulebook services, corpus publishing, context providers, and MCP server
  exposure.
- `03.product/` contains deployment source material for product applications,
  product services, and app/runtime targets.

Shared deploy material can be referenced by a track, but track-specific material
should not be merged into shared unless it applies to more than one deploy
target.
