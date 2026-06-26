<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.00-chat.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: source-material-readme
purpose: Define the chat deploy source-material track for LLM Workbench and chat harness deployment concerns.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.source-material.readme
  path: docs/04.deploy/source-material/README.md
-->
# 00.chat Deploy Source Material

Use this track for deploying chat lifecycle and LLM Workbench capabilities.

This includes chat startup surfaces, git-governance services, chat-session
state, worktree orchestration, and remote workbench deployment concerns.

Deployment governance remains owned by `04.deploy`; this track names the system
being deployed.
