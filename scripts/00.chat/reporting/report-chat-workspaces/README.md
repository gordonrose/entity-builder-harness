<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain chat branch and worktree status reporting.
domain: reporting
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-cleanup.md
  - scripts/00.chat/reporting/report-chat-workspaces/script.sh
-->

# Report Chat Workspaces

`script.sh` prints a table of local `chat/*` branches, ahead/behind state,
recorded log head state, and worktree path.

Use this before cleanup or promotion when a human needs to understand which
chat branches are active, stale, missing logs, or checked out elsewhere.

The script is read-only. It does not delete branches, clean worktrees, merge,
or push.

