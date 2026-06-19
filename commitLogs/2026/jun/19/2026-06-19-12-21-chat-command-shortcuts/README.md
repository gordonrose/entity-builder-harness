# Chat Session: 2026-06-19-12-21 chat-command-shortcuts

<!-- agentic-session
id: 2026-06-19-12-21-i-would-like-to-add-some-commands-to-my-harness-that-trigger
task: i would like to add some commands to my harness that trigger specific workflows or prompts. for example 'new' triggers the current ctrl+shift+b inside a chat; 'close' triggers commit and merge to main workflow; this needs to be a mechanism that allows me to easily add new commands over time
branch: chat/2026-06-19-12-21-i-would-like-to-add-some-commands-to-my-harness-that-trigger
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-19-12-21-i-would-like-to-add-some-commands-to-my-harness-that-trigger-2083125693
layer: chat
mode: implementation
workflow: .agentic/00.chat/workflows/chat-promote-to-main.md
status: ready
raised_at_utc: 2026-06-19T11:21:48Z
codex_session_log_path: /home/owner/.codex/sessions/2026/06/19/rollout-2026-06-19T12-20-16-019edf9c-326b-7e63-b1b7-f23415a772f7.jsonl
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
-->

## Initial Intent

i would like to add some commands to my harness that trigger specific workflows or prompts. for example 'new' triggers the current ctrl+shift+b inside a chat; 'close' triggers commit and merge to main workflow; this needs to be a mechanism that allows me to easily add new commands over time

## Branch

`chat/2026-06-19-12-21-i-would-like-to-add-some-commands-to-my-harness-that-trigger`

## Worktree

`/tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-19-12-21-i-would-like-to-add-some-commands-to-my-harness-that-trigger-2083125693`

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made

- Add a chat command dispatcher at `scripts/shared/chat/chat-command.sh`.
- Keep commands as executable scripts under `scripts/shared/chat/commands/` so
  new commands can be added without changing dispatcher logic.
- Route the VS Code default build task through `chat-command.sh new` so
  Ctrl+Shift+B and the `new` command share the same startup path.
- Make `close` produce a governed prompt rather than silently committing,
  merging, or pushing.

## Activity Log

### 2026-06-19T11:21:48Z - Session started

Initial intent: i would like to add some commands to my harness that trigger specific workflows or prompts. for example 'new' triggers the current ctrl+shift+b inside a chat; 'close' triggers commit and merge to main workflow; this needs to be a mechanism that allows me to easily add new commands over time

### 2026-06-19T11:27:53Z - Implemented chat command shortcuts

Added the chat command dispatcher, `new` and `close` command scripts, command
documentation, and smoke coverage. Validated with:

- `bash scripts/shared/chat/smoke-test-chat-command.sh`
- `bash scripts/shared/git/smoke-test-chat-worktree-session.sh`

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This is a small chat-layer automation extension using the existing
artifact map: deterministic behavior is in scripts, shortcut guidance is in the
chat layer, and durable approval boundaries remain in existing workflows.

## Session Metrics

Raised at UTC: 2026-06-19T11:21:48Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:

## Notes

- None recorded yet.
