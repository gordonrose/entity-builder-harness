<!-- agentic-artifact:
owner: harness
kind: readme
purpose: Index harness workflows, standards, data, and architecture docs.
domain: governance
portability: llm-workbench-required
used_by:
  - AGENTS.md
-->

# Harness Workflow Index

Use `workflows/change-harness.md` for changes to AGENTS.md, CLAUDE.md, .agentic structure, routing, workflows, skills, agents, gates, adapters, or instruction/token rules.

## Standards

- `standards/agentic-artifact-standards.md` - decides which artifact type should own new harness capabilities, including workflows, skills, standards, gates, hooks, evals, templates, examples, memory, agents, adapters, and scripts.
- `standards/governed-script-permissions.md` - defines how persistent vendor command permissions target the governed script runner instead of broad shell access.
- `standards/missing-governance-stop-condition.md` - defines how agents stop and report when a necessary action, recovery path, workaround, or substitution is not governed by the current workflow, gate, script, or standard.

## Architecture

- `docs/harness/architecture/chat-workbench-public-repo-readiness.md` - defines the current export boundary for bootstrapping a standalone public chat workbench repo.
- `docs/harness/architecture/script-layout.md` - explains the current script layout after the chat harness script migration.

## Bootstrap Templates

- `docs/harness/bootstrap/llm-workbench-template/` - starter public repo shell files for the first `llm-workbench` bootstrap.

## Data

- `data/openai-chat-pricing.json` - versioned pricing snapshot used by chat cost estimation scripts.
