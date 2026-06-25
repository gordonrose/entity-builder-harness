<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.worktree.paths.readme
  version: 1
  status: active
  layer: 00.chat
  domain: worktree
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain helper functions for chat worktree paths and metadata.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.worktree.paths.lib
    path: scripts/00.chat/worktree/paths/lib.sh
  - id: chat.script.worktree.ensure-chat-worktree
    path: scripts/00.chat/worktree/ensure-chat-worktree/script.sh
-->
# Worktree Paths

`lib.sh` provides shell helper functions for deriving canonical chat worktree
paths.

The helpers make worktree paths deterministic from the repository root and chat
branch name. That lets startup, reporting, recovery, and verification agree on
where a chat-owned worktree should live.

This library is read-only. It does not create worktrees or change branches.

