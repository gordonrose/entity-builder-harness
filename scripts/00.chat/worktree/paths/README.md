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

The helpers make worktree paths deterministic from the primary repository
worktree and chat branch name. New chat worktrees default to
`$HOME/projects/.chat-worktrees/<repo-name>-<repo-id>/<chat-branch>-<branch-id>`.
Set the absolute `AGENTIC_CHAT_WORKTREE_ROOT` variable to override that root for
one repository; `.agentic/env.local` can set it for ordinary local use.

When a branch already has one Git-registered worktree, the helpers return that
path instead of recomputing the new-worktree destination. This keeps legacy
sessions usable after the default changes. Multiple registered worktrees for the
same branch are rejected as ambiguous.

This library is read-only. It does not create worktrees or change branches.
