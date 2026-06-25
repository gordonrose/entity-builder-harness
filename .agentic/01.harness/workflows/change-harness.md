<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.workflows.change-harness
version: 1
status: active
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
- id: chat.script.classification.classify-task
  path: scripts/00.chat/classification/classify-task/script.sh
-->

name: change-harness
layer: harness
purpose: Govern changes to AGENTS.md, CLAUDE.md, .agentic structure, routing, workflows, skills, agents, gates, adapters, and instruction/token rules.

required_gates:
  - id: dirty_worktree
    script: scripts/00.chat/worktree/dirty-worktree-check/script.sh --allow-session-bookkeeping

rules:
  - Keep AGENTS.md as a router only.
  - Consult .agentic/01.harness/standards/agentic-artifact-standards.md before adding or changing harness artifacts.
  - Use .agentic/01.harness/workflows/migrate-artifact-paths.md when moving, renaming, retiring, or removing committed files or directories.
  - Consult .agentic/01.harness/standards/missing-governance-stop-condition.md when a required harness action, recovery path, workaround, or substitution is not already governed.
  - Prefer scripts over prose where checks can be deterministic.
  - Do not duplicate rules across AGENTS.md, workflows, skills, and gates.
  - Update relevant indexes when adding or moving harness files.
  - Treat dirty worktree output of `bookkeeping-only` as acceptable after explicit write permission for the chat.
  - Stop if ownership of the rule is unclear.

blocked_response_format: "Blocked: <reason>. Confirm proceed? Layer: harness. Mode: <mode>. Workflow: .agentic/01.harness/workflows/change-harness.md."
