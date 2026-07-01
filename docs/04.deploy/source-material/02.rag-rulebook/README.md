<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.02-rag-rulebook.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: source-material-readme
purpose: Define the RAG/rulebook deploy source-material track for context-provider and MCP server deployment concerns.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.source-material.readme
  path: docs/04.deploy/source-material/README.md
- id: deploy.source-material.mcp-server-deployment
  path: docs/04.deploy/source-material/02.rag-rulebook/mcp-server-deployment.md
-->
# 02.rag-rulebook Deploy Source Material

Use this track for deploying RAG/rulebook capabilities.

This includes local-to-remote RAG progression, corpus publishing, remote context
providers, validated context packets, corpus-version checks, and MCP server
surfaces for resources, prompts, and later governed tools.

Deployment governance remains owned by `04.deploy`; this track names the system
being deployed.
