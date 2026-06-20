<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain renaming the current chat session log folder.
domain: session-log
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-start.md
  - scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh
-->

# Rename Current Chat Log Folder

`script.sh` renames the current chat session log folder to a shorter human
summary while preserving the existing branch name and session metadata.

This is useful when an auto-generated session slug is too long or unclear. The
session remains the same chat; only the log folder path changes.

Because this writes files, it is approval-sensitive through the governed runner.
It does not rename branches, rewrite commits, or change task ownership.

