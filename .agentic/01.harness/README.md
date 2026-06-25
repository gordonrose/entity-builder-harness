<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.readme
version: 1
status: active
layer: 01.harness
domain: governance
disciplines:
- agentic
kind: readme
purpose: Index harness workflows, standards, data, and architecture docs.
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

# Harness Workflow Index

Use `workflows/change-harness.md` for changes to AGENTS.md, CLAUDE.md, .agentic structure, routing, workflows, skills, agents, gates, adapters, or instruction/token rules.

Use `workflows/migrate-artifact-paths.md` for moving, renaming, retiring, or removing committed files or directories.

## Architecture Rulebook Operating Pack

This folder includes operating guidance for Codex while building the architecture
rules and rule packs. It is not the runtime harness, and it does not replace
`docs/harness/architecture`.

RAG/rulebook machinery now has its own layer at `.agentic/02.rag-rulebook/`.
The architecture rulebook artifacts referenced here remain a prototype corpus
until a governed migration assigns final domain corpus homes.

Canonical architecture source remains
`docs/harness/architecture/guides/markdown`.

Canonical rules remain `docs/harness/architecture/rules`.

Canonical rule packs remain `docs/harness/architecture/rule-packs`.

Future Codex sessions continuing rulebook work should start by reading
`manifest.yml` and `operator-guide.md`.

## Capabilities

- `artifact-metadata/` - owns the versioned artifact metadata model, taxonomy,
  v2 schema contract, and future artifact index generator guidance.

## Standards

- `standards/agentic-artifact-standards.md` - decides which artifact type should own new harness capabilities, including workflows, skills, standards, gates, hooks, evals, templates, schemas, examples, memory, agents, adapters, and scripts.
- `standards/artifact-metadata-headers.md` - defines the compatibility v1 metadata header format and points to the versioned artifact metadata capability.
- `standards/artifact-path-migrations.md` - defines compatibility rules for moving, renaming, retiring, or removing repository artifact paths.
- `standards/evaluation-fixtures.md` - defines how harness evaluation fixtures are authored, owned, validated, and evolved.
- `standards/governed-script-permissions.md` - defines how persistent vendor command permissions target the governed script runner instead of broad shell access.
- `standards/missing-governance-stop-condition.md` - defines how agents stop and report when a necessary action, recovery path, workaround, or substitution is not governed by the current workflow, gate, script, or standard.

## Chat Workbench Docs

- `docs/00.chat/` - indexes chat-owned docs for portable chat harness and public workbench bootstrap behavior.
- `docs/00.chat/chat-workbench-public-repo-readiness.md` - defines the current export boundary for bootstrapping a standalone public chat workbench repo.
- `docs/00.chat/script-layout.md` - explains the numbered `scripts/` layer command-surface convention after the chat harness script migration.

## Bootstrap Templates

- `docs/00.chat/bootstrap/llm-workbench-template/` - starter public repo shell files for the first `llm-workbench` bootstrap.

## Scripts

- `scripts/01.harness/artifact-metadata/check-headers/script.sh` - capability-scoped entrypoint for artifact metadata header checks.
- `scripts/01.harness/artifact-metadata/generate-index/script.sh` - emits a JSON artifact index from v1 and v2 metadata headers.
- `scripts/01.harness/check-rule-test-taxonomy.sh` - validates declared architecture rulebook layer test taxonomy scope, CI vocabulary references, substitute limits, and negative-evidence guardrails.

## Data

- `data/openai-chat-pricing.json` - versioned pricing snapshot used by chat cost estimation scripts.
