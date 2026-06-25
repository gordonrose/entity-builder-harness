<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.session-log.rename-current-chat-log-folder.readme
  version: 1
  status: active
  layer: 00.chat
  domain: session-log
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain renaming the current chat session log folder.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-start
    path: .agentic/00.chat/workflows/chat-start.md
  - id: chat.script.session-log.rename-current-chat-log-folder
    path: scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh
-->
# Rename Current Chat Log Folder

`script.sh` renames the current chat session log folder to a shorter human
summary while preserving the existing branch name and session metadata.

This is useful when an auto-generated session slug is too long or unclear. The
session remains the same chat; only the log folder path changes.

Because this writes files, it is approval-sensitive through the governed runner.
It does not rename branches, rewrite commits, or change task ownership.

