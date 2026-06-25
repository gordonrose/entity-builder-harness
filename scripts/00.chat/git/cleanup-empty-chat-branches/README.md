<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.git.cleanup-empty-chat-branches.readme
  version: 1
  status: active
  layer: 00.chat
  domain: git
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain empty chat branch and session-log cleanup.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-cleanup
    path: .agentic/00.chat/workflows/chat-cleanup.md
  - id: chat.script.git.cleanup-empty-chat-branches
    path: scripts/00.chat/git/cleanup-empty-chat-branches/script.sh
-->
# Cleanup Empty Chat Branches

`script.sh` finds `chat/*` branches with no commits beyond the base branch and
optionally removes them with their matching empty session logs.

Dry-run is the default. Use `--apply` only when deletion is explicitly approved.
The script never deletes the current branch and skips branches that are checked
out in any worktree.

A session log is deleted only when it belongs to the empty branch and contains
no recorded commits or retention marker. That protects real chat evidence while
allowing abandoned zero-work sessions to be cleaned up.

`smoke-test.sh` exercises the branch and log safety rules in a throwaway repo.

