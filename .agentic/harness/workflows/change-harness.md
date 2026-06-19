name: change-harness
layer: harness
purpose: Govern changes to AGENTS.md, CLAUDE.md, .agentic structure, routing, workflows, skills, agents, gates, adapters, and instruction/token rules.

required_gates:
  - id: dirty_worktree
    script: scripts/00.chat/worktree/dirty-worktree-check/script.sh --allow-session-bookkeeping

rules:
  - Keep AGENTS.md as a router only.
  - Consult .agentic/harness/standards/agentic-artifact-standards.md before adding or changing harness artifacts.
  - Consult .agentic/harness/standards/missing-governance-stop-condition.md when a required harness action, recovery path, workaround, or substitution is not already governed.
  - Prefer scripts over prose where checks can be deterministic.
  - Do not duplicate rules across AGENTS.md, workflows, skills, and gates.
  - Update relevant indexes when adding or moving harness files.
  - Treat dirty worktree output of `bookkeeping-only` as acceptable after explicit write permission for the chat.
  - Stop if ownership of the rule is unclear.

blocked_response_format: "Blocked: <reason>. Confirm proceed? Layer: harness. Mode: <mode>. Workflow: .agentic/harness/workflows/change-harness.md."
