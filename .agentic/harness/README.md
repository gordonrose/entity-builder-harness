# Harness Workflow Index

Use `workflows/change-harness.md` for changes to AGENTS.md, CLAUDE.md, .agentic structure, routing, workflows, skills, agents, gates, adapters, or instruction/token rules.

## Standards

- `standards/agentic-artifact-standards.md` - decides which artifact type should own new harness capabilities, including workflows, skills, standards, gates, hooks, evals, templates, examples, memory, agents, adapters, and scripts.
- `standards/missing-governance-stop-condition.md` - defines how agents stop and report when a necessary action, recovery path, workaround, or substitution is not governed by the current workflow, gate, script, or standard.

## Data

- `data/governed-script-allowlist.txt` - repo-relative scripts permitted through the governed script runner.
- `data/openai-chat-pricing.json` - versioned pricing snapshot used by chat cost estimation scripts.
