<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.worktree.ensure-chat-worktree.readme
  version: 1
  status: active
  layer: 00.chat
  domain: worktree
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain creating or verifying the chat-owned worktree for a session.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.startup.start-chat-session
    path: scripts/00.chat/startup/start-chat-session/script.sh
  - id: chat.script.worktree.ensure-chat-worktree
    path: scripts/00.chat/worktree/ensure-chat-worktree/script.sh
-->
# Ensure Chat Worktree

`script.sh` creates or verifies the canonical worktree for the chat branch named
in a session log.

Startup uses this so the session branch has a separate physical checkout for
task work. If the worktree already exists, the script verifies that it belongs
to the same repository and is on the expected branch.

The script prints the worktree path. It does not stage task files, commit, merge,
push, or clean existing work.

