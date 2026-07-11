<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.rules.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: rulebook-readme
purpose: Define the deploy corpus structured rulebook area before index and chunk support is added.
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
# Deploy Rules

This directory contains structured YAML rules for `corpus.04.deploy`.

These rules are RAG-readable governance content. They do not by themselves
authorize AWS mutation, GitHub workflow deployment, or production exposure.

Index, chunk, and selector-evaluation support for this directory is tracked as
a separate RAG/rulebook follow-up.

Track-specific rules:

- `02.rag-rulebook/` for RAG/rulebook services and MCP exposure.
- `03.product/` for product applications, product services, and platform
  runtime services.
