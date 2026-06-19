<!-- agentic-artifact:
owner: 00.chat
kind: guide
purpose: Explain the check that decides whether a chat branch includes local main.
domain: main-refresh
portability: llm-workbench-required
used_by:
  - scripts/00.chat/main-refresh/check-chat-is-current-with-main/script.sh
-->

# Check Chat Is Current With Main

This read-only capability answers: does this chat branch already include the
latest local `main`?

It reports whether the chat branch is even, fresh-ahead, behind, or diverged
relative to a base branch, defaulting to `main`. With `--require-fresh`, it
exits non-zero when the chat branch is behind or diverged.

Use this when a workflow needs a simple freshness gate before continuing chat
work or before local merge/promotion decisions.
