<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain session-log scripts for durable chat evidence.
domain: session-log
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/checklists/before-commit.md
  - scripts/00.chat/session-log/record-chat-commit/README.md
-->

# Session Log Scripts

Session-log scripts read and update the durable evidence for a chat. The
session log records task intent, branch/worktree metadata, workflow routing,
activity, decisions, issues, commits, conflicts, and metrics.

These scripts are part of why chats are auditable. They should update only the
current chat's log unless a workflow explicitly says otherwise.

The helper libraries in this domain provide shared path and metadata parsing
for other chat capabilities.

