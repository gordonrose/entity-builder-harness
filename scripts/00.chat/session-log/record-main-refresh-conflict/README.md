<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.session-log.record-main-refresh-conflict.readme
  version: 1
  status: active
  layer: 00.chat
  domain: session-log
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain recording governed main-refresh conflict resolutions.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-refresh-from-main
    path: .agentic/00.chat/workflows/chat-refresh-from-main.md
  - id: chat.script.session-log.record-main-refresh-conflict
    path: scripts/00.chat/session-log/record-main-refresh-conflict/script.sh
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

