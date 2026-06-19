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
latest_commit_at_utc: 2026-06-19T11:47:36Z
latest_commit_sha: 6d5cdc6
chat_duration: 1548s (00:00:25:48)
estimated_chat_tokens: 117922 estimated from chat transcript bytes (471686 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/19/rollout-2026-06-19T12-20-16-019edf9c-326b-7e63-b1b7-f23415a772f7.jsonl)
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


### 2026-06-19T11:47:36Z - Commit recorded

Commit: `6d5cdc6`

Message: Add chat command shortcuts

Summary: Added extensible chat-command dispatcher, new/close commands, command docs, VS Code task routing, and smoke coverage.

ADR impact: ADR not needed; small chat-layer automation extension using existing artifact ownership.

## Commits



- Commit: `6d5cdc6`
  Time UTC: 2026-06-19T11:47:36Z
  Message: Add chat command shortcuts
  Summary: Added extensible chat-command dispatcher, new/close commands, command docs, VS Code task routing, and smoke coverage.
  ADR impact: ADR not needed; small chat-layer automation extension using existing artifact ownership.

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
Latest commit at UTC: 2026-06-19T11:47:36Z
Latest commit SHA: 6d5cdc6
Chat duration: 1548s (00:00:25:48)
Estimated chat tokens: 117922 estimated from chat transcript bytes (471686 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/19/rollout-2026-06-19T12-20-16-019edf9c-326b-7e63-b1b7-f23415a772f7.jsonl)

## Notes

- None recorded yet.
