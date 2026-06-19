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
- Chat script aliases: `scripts/chat/`
- Legacy shared workflow locations: `.agentic/shared/workflows/`
- Legacy chat scripts: `scripts/shared/chat/` and `scripts/shared/git/`

## Migration Policy

Move chat-specific instructions here gradually. Do not perform a big-bang path
move while active chats still reference legacy workflow and script paths.

When a chat-specific process remains in a legacy location, this layer owns the
behavior and the legacy path is a compatibility location.

Use `scripts/chat/` for public chat-layer script entrypoints where available.
The wrappers delegate to canonical capability scripts under `scripts/00.chat/`.

Use `bash scripts/00.chat/migration/audit-chat-layer-migration/script.sh` to inspect the
current migration state before moving more chat lifecycle behavior.

Use `bash scripts/00.chat/session-log/record-main-refresh-conflict/script.sh` to append the
required session-log audit trail for governed main-refresh conflict recovery.

## Reporting Policy

Do not maintain an always-generated aggregate `commitLogs/README.md`.

Generate chat/session summaries only on request, using the on-demand reporting
skill or script. Individual session logs remain the durable source evidence.
