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

## Rule Inventory

- `mcp-server-deployment.yml` defines the overall local-first, corpus-package,
  MCP boundary, GitHub, AWS, observability, rollback, and readiness-gap rules.
- `github-to-aws-deployment.yml` defines GitHub as the release-control plane
  for AWS deployment.
- `aws-runtime-boundaries.yml` defines account, region, service, network,
  secrets, observability, health, and rollback boundaries.
- `deployment-readiness-checks.yml` defines the remote-main-to-GitHub-to-AWS
  readiness evidence required before deployment execution.

## Intended Path

The intended execution path is:

1. local RAG proves context behavior;
2. committed corpus packages are generated from remote main;
3. GitHub verifies, publishes, and authorizes deployment;
4. AWS receives an immutable artifact and versioned corpus package;
5. health, audit, and rollback evidence prove the deployment result.

Planning may explain gaps. Deployment execution must block until the relevant
readiness rules have executable or auditable proof.

The current executable proof surface is
`scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh`, which
validates a target deploy-readiness manifest before any GitHub-to-AWS
deployment execution can proceed.
