<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.reporting.report-chat-workspaces.readme
  version: 1
  status: active
  layer: 00.chat
  domain: reporting
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain chat branch and worktree status reporting.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-cleanup
    path: .agentic/00.chat/workflows/chat-cleanup.md
  - id: chat.script.reporting.report-chat-workspaces
    path: scripts/00.chat/reporting/report-chat-workspaces/script.sh
-->
# Report Chat Workspaces

`script.sh` prints a table of local `chat/*` branches, ahead/behind state,
recorded log head state, and worktree path.

Use this before cleanup or promotion when a human needs to understand which
chat branches are active, stale, missing logs, or checked out elsewhere.

The script is read-only. It does not delete branches, clean worktrees, merge,
or push.

