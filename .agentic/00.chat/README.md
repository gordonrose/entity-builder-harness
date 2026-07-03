<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.readme
  version: 1
  status: active
  layer: 00.chat
  domain: governance
  disciplines:
  - agentic
  kind: layer-readme
  purpose: Explain the chat lifecycle governance layer and its canonical surfaces.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: repo.agents
    path: AGENTS.md
  - id: chat.migration-plan
    path: .agentic/00.chat/migration-plan.md
-->
# 00.chat Layer

## Purpose

Own chat lifecycle governance for this harness.

This layer covers chat creation, session metadata, chat-owned worktrees,
session logs, commit checkpoints, main-refresh coordination, closeout,
cleanup, shortcuts, and on-demand chat reports.

<!-- deterministic-check: allow reason="prompt routing may be manual or repo-specific; no universal script can decide whether a context router exists" -->
This layer does not assign a whole chat one durable layer, mode, or workflow.
Prompt interpretation uses the current request, repo assistant instructions,
and any repo-provided context router if one exists. When a router returns a
context packet, the chat layer may record the latest packet ID and summary for
continuity, but chat lifecycle metadata remains about branch, worktree, session
log, metrics, transcript, and git state.

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

Use `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/record-main-refresh-conflict/script.sh`
to append the required session-log audit trail for governed main-refresh
conflict recovery.

## Reporting Policy

Do not maintain an always-generated aggregate `commitLogs/README.md`.

Generate chat/session summaries only on request, using the on-demand reporting
skill or script. Individual session logs remain the durable source evidence.
