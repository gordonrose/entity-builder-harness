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
- Chat lifecycle migration plan: `.agentic/00.chat/migration-plan.md`
- Legacy shared workflow locations: `.agentic/shared/workflows/`
- Legacy chat scripts: `scripts/shared/chat/` and `scripts/shared/git/`

## Migration Policy

Move chat-specific instructions here gradually. Do not perform a big-bang path
move while active chats still reference legacy workflow and script paths.

When a chat-specific process remains in a legacy location, this layer owns the
behavior and the legacy path is a compatibility location.

Use `bash scripts/shared/chat/audit-chat-layer-migration.sh` to inspect the
current migration state before moving more chat lifecycle behavior.

## Reporting Policy

Do not maintain an always-generated aggregate `commitLogs/README.md`.

Generate chat/session summaries only on request, using the on-demand reporting
skill or script. Individual session logs remain the durable source evidence.
