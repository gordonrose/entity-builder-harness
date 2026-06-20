<!-- agentic-artifact:
owner: 00.chat
kind: layer-readme
purpose: Explain the chat lifecycle governance layer and its canonical surfaces.
domain: governance
portability: llm-workbench-required
used_by:
  - AGENTS.md
  - .agentic/00.chat/migration-plan.md
-->

# 00.chat Layer

## Purpose

Own chat lifecycle governance for this harness.

This layer covers chat creation, session metadata, chat-owned worktrees,
session logs, commit checkpoints, main-refresh coordination, closeout,
cleanup, shortcuts, and on-demand chat reports.

## Source Of Truth

- Active chat state: current branch session log under `commitLogs/`
- Chat lifecycle workflows: `.agentic/00.chat/workflows/`
- Chat lifecycle checklists: `.agentic/00.chat/checklists/`
- Chat lifecycle skills: `.agentic/00.chat/skills/`
- Chat lifecycle standards: `.agentic/00.chat/standards/`
- Chat command shortcuts: `.agentic/00.chat/commands/`
- Chat lifecycle migration plan: `.agentic/00.chat/migration-plan.md`
- Public chat commands: `package.json` `chat:*` scripts
- Shared harness governance helpers: `scripts/01.harness/`

## Migration Policy

Move chat-specific instructions here. Retired compatibility paths should stay
retired unless an active session recovery explicitly requires a governed
restore.

Use `npm run chat:*` package scripts for public chat-layer command entrypoints.
The package scripts delegate to canonical capability scripts under
`scripts/00.chat/`.

Do not add new chat lifecycle scripts under `scripts/shared/git/` or
`scripts/shared/chat/`. Those locations were retired as compatibility surfaces;
new chat-owned behavior belongs under `scripts/00.chat/<domain>/<capability>/`.

Use `bash scripts/00.chat/migration/audit-chat-layer-migration/script.sh` to inspect the
current migration state before moving more chat lifecycle behavior.

Use `bash scripts/00.chat/session-log/record-main-refresh-conflict/script.sh` to append the
required session-log audit trail for governed main-refresh conflict recovery.

## Reporting Policy

Do not maintain an always-generated aggregate `commitLogs/README.md`.

Generate chat/session summaries only on request, using the on-demand reporting
skill or script. Individual session logs remain the durable source evidence.
