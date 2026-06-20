<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain recording governed main-refresh conflict resolutions.
domain: session-log
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-refresh-from-main.md
  - scripts/00.chat/session-log/record-main-refresh-conflict/script.sh
-->

# Record Main Refresh Conflict

`script.sh` appends a main-refresh conflict audit entry to the current chat
session log.

Use it after a refresh from `main` encounters a conflict and the conflict has
been classified, resolved, stopped, or handed to a manual path. The entry names
the conflicted path, conflict type, reason, resolution action, mode, preflight
branch, preflight worktree, changed files, and checks.

The script records evidence. It does not resolve conflicts, apply refreshes,
merge branches, or push.

