<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.rules.shared.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: rulebook-readme
purpose: Define shared deploy rules that apply across deploy tracks.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.rules.readme
  path: docs/04.deploy/rules/README.md
-->
# Shared Deploy Rules

This directory contains structured deploy rules that apply across multiple
deploy tracks.

Track-specific rules stay under their owning track, such as
`rules/02.rag-rulebook/`. Use shared rules only when the requirement applies to
more than one deployable system.

