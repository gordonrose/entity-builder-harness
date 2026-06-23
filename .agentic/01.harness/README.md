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

Use `workflows/migrate-artifact-paths.md` for moving, renaming, retiring, or removing committed files or directories.

## Architecture Rulebook Operating Pack

This folder includes operating guidance for Codex while building the architecture
rules and rule packs. It is not the runtime harness, and it does not replace
`docs/harness/architecture`.

Canonical architecture source remains
`docs/harness/architecture/guides/markdown`.

Canonical rules remain `docs/harness/architecture/rules`.

Canonical rule packs remain `docs/harness/architecture/rule-packs`.

Future Codex sessions continuing rulebook work should start by reading
`manifest.yml` and `operator-guide.md`.

## Standards

- `standards/agentic-artifact-standards.md` - decides which artifact type should own new harness capabilities, including workflows, skills, standards, gates, hooks, evals, templates, examples, memory, agents, adapters, and scripts.
- `standards/artifact-path-migrations.md` - defines compatibility rules for moving, renaming, retiring, or removing repository artifact paths.
- `standards/governed-script-permissions.md` - defines how persistent vendor command permissions target the governed script runner instead of broad shell access.
- `standards/missing-governance-stop-condition.md` - defines how agents stop and report when a necessary action, recovery path, workaround, or substitution is not governed by the current workflow, gate, script, or standard.

## Chat Workbench Docs

- `docs/00.chat/` - indexes chat-owned docs for portable chat harness and public workbench bootstrap behavior.
- `docs/00.chat/chat-workbench-public-repo-readiness.md` - defines the current export boundary for bootstrapping a standalone public chat workbench repo.
- `docs/00.chat/script-layout.md` - explains the current script layout after the chat harness script migration.

## Bootstrap Templates

- `docs/harness/bootstrap/llm-workbench-template/` - starter public repo shell files for the first `llm-workbench` bootstrap.

## Scripts

- `scripts/01.harness/check-rule-test-taxonomy.sh` - validates architecture rulebook layer test taxonomy structure and CI vocabulary references.

## Data

- `data/openai-chat-pricing.json` - versioned pricing snapshot used by chat cost estimation scripts.
