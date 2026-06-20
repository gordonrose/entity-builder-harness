<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain helper functions for chat worktree paths and metadata.
domain: worktree
portability: llm-workbench-required
used_by:
  - scripts/00.chat/worktree/paths/lib.sh
  - scripts/00.chat/worktree/ensure-chat-worktree/script.sh
-->

# Worktree Paths

`lib.sh` provides shell helper functions for deriving canonical chat worktree
paths.

The helpers make worktree paths deterministic from the repository root and chat
branch name. That lets startup, reporting, recovery, and verification agree on
where a chat-owned worktree should live.

This library is read-only. It does not create worktrees or change branches.

