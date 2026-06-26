<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.rules.02-rag-rulebook.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: rulebook-readme
purpose: Define the structured deploy-rule track for RAG/rulebook services and MCP exposure.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.rules.readme
  path: docs/04.deploy/rules/README.md
- id: deploy.rules.02-rag-rulebook.mcp-server-deployment
  path: docs/04.deploy/rules/02.rag-rulebook/mcp-server-deployment.yml
-->
# 02.rag-rulebook Deploy Rules

Use this track for deploy rules that apply to RAG/rulebook services, corpus
publishing, remote context providers, and MCP server exposure.

Deployment governance remains owned by `04.deploy`; this track names the system
being deployed.
