<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain chat-owned worktree scripts and helpers.
domain: worktree
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-start.md
  - scripts/00.chat/worktree/ensure-chat-worktree/README.md
-->

# Worktree Scripts

Worktree scripts keep chat task work in the right checkout. The root worktree is
the integration console; each chat should edit in its own sibling worktree.

This domain provides path helpers, write-location checks, dirty-state checks,
and worktree creation/verification.

The goal is not to make Git clever. The goal is to prevent accidental edits in
the wrong place.

