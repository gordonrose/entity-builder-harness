<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.session-log.readme
  version: 1
  status: active
  layer: 00.chat
  domain: session-log
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain session-log scripts for durable chat evidence.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.checklists.before-commit
    path: .agentic/00.chat/checklists/before-commit.md
  - id: chat.script.session-log.record-chat-commit.readme
    path: scripts/00.chat/session-log/record-chat-commit/README.md
-->
# Session Log Scripts

Session-log scripts read and update the durable evidence for a chat. The
session log records task intent, branch/worktree metadata, workflow routing,
activity, decisions, issues, sub-agent activity, commits, conflicts, and
metrics.

These scripts are part of why chats are auditable. They should update only the
current chat's log unless a workflow explicitly says otherwise.

The helper libraries in this domain provide shared path and metadata parsing
for other chat capabilities.
