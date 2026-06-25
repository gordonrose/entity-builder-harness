<!-- agentic-artifact:
schema: agentic-artifact/v2
id: shared.standards.readme
version: 1
status: active
layer: 05.shared
domain: governance
disciplines:
- agentic
kind: readme
purpose: Index the Shared Standards artifact family.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: repo.agents
  path: AGENTS.md
-->

# Shared Standards

Shared standards govern cross-layer expectations that more than one layer can
reuse.

## Standards

- `upstream-repo-bootstrap.md` - bootstrap reusable upstream repos from a
  source repo without leaking source-specific behavior.

