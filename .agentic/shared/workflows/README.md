<!-- agentic-artifact:
schema: agentic-artifact/v2
id: shared.workflows.readme
version: 1
status: active
layer: 05.shared
domain: process
disciplines:
- agentic
kind: readme
purpose: Index the active shared process workflows.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: repo.agents
  path: AGENTS.md
- id: chat.migration-plan
  path: .agentic/00.chat/migration-plan.md
-->

# Shared Workflows

Shared workflows govern cross-layer process that does not belong to one
specialized layer. Chat lifecycle ownership belongs in `.agentic/00.chat/`.

## Workflows

- `change-shared-process.md` - change cross-layer git, commit, merge, handoff,
  deployment, release, or context-preservation process.
- `capability-resolution-workflow.md` - propose or resolve capabilities before
  implementation.
