<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.standards.readme
version: 2
status: active
created_on: "2026-06-19"
updated_on: "2026-10-25"
layer: 06.shared
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

- `require-safe-diagnostic-record.md` - safe, bounded, actionable diagnostic
  records shared by product and deployment controls.
- `upstream-repo-bootstrap.md` - bootstrap reusable upstream repos from a
  source repo without leaking source-specific behavior.
- [Require change completion](require-change-completion.md) - connected implementation, consumer impact, proportionate verification and evidence-based completion.
