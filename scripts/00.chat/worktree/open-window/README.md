<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain opening a VS Code window for a chat-owned worktree.
domain: worktree
portability: llm-workbench-required
used_by:
  - scripts/00.chat/worktree/open-window/script.sh
  - scripts/00.chat/command/open-window/script.sh
-->

# Open Window Worktree Capability

`script.sh` opens a new VS Code window for a chat-owned worktree.

With no argument, it reads the current chat branch session log and opens the
`worktree` metadata path. With one argument, it accepts either a worktree path
or a session-log `README.md` path.

The command is best-effort. If the `code` CLI is unavailable or cannot open the
window, the script prints a warning and exits successfully so chat startup does
not fail after branch and worktree creation.

Set `CHAT_OPEN_WORKTREE_WINDOW=skip` to suppress the window open.
