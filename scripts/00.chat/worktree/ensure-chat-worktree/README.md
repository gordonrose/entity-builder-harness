<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain creating or verifying the chat-owned worktree for a session.
domain: worktree
portability: llm-workbench-required
used_by:
  - scripts/00.chat/startup/start-chat-session/script.sh
  - scripts/00.chat/worktree/ensure-chat-worktree/script.sh
-->

# Ensure Chat Worktree

`script.sh` creates or verifies the canonical worktree for the chat branch named
in a session log.

Startup uses this so the session branch has a separate physical checkout for
task work. If the worktree already exists, the script verifies that it belongs
to the same repository and is on the expected branch.

The script prints the worktree path. It does not stage task files, commit, merge,
push, or clean existing work.

