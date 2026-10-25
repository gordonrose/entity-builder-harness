<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.workflows.change-harness
version: 2
status: active
created_on: "2026-06-20"
updated_on: "2026-10-25"
layer: 01.harness
domain: governance
disciplines:
- agentic
kind: workflow
purpose: Govern changes to harness routing, workflows, standards, agents, adapters,
  and instruction rules.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: repo.agents
  path: AGENTS.md
- id: artifact.agentic.routing-policy
  path: .agentic/routing-policy.yaml
-->

name: change-harness
layer: harness
purpose: Govern changes to AGENTS.md, CLAUDE.md, .agentic structure, routing, workflows, skills, agents, gates, adapters, and instruction/token rules.

rules:
  - Follow `.agentic/shared/standards/require-change-completion.md` for connected implementation, consumer impact, proportionate verification, and completion evidence.
  - Keep AGENTS.md as a router only.
  - Consult .agentic/01.harness/standards/agentic-artifact-standards.md before adding or changing harness artifacts.
  - Consult .agentic/01.harness/standards/document-artifact-placement.md before adding or moving document artifacts, corpus material, ADRs, plans, rules, or rule packs.
  - Use .agentic/01.harness/workflows/migrate-artifact-paths.md when moving, renaming, retiring, or removing committed files or directories.
  - Consult .agentic/01.harness/standards/missing-governance-stop-condition.md when a required harness action, recovery path, workaround, or substitution is not already governed.
  - Prefer scripts over prose where checks can be deterministic.
  - Do not duplicate rules across AGENTS.md, workflows, skills, and gates.
  - Update relevant indexes when adding or moving harness files.
  - Follow existing-change handling in `.agentic/00.chat/workflows/chat-start.md#existing-changes`; dirty status alone is not a blocker.
  - Stop if ownership of the rule is unclear.

blocked_response_format: "Blocked: <reason>. Confirm proceed? Layer: harness. Mode: <mode>. Workflow: .agentic/01.harness/workflows/change-harness.md."
