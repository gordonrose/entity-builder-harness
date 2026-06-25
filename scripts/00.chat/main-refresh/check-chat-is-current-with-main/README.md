<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.main-refresh.check-chat-is-current-with-main.readme
  version: 1
  status: active
  layer: 00.chat
  domain: main-refresh
  disciplines:
  - agentic
  kind: guide
  purpose: Explain the check that decides whether a chat branch includes local main.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.main-refresh.check-chat-is-current-with-main
    path: scripts/00.chat/main-refresh/check-chat-is-current-with-main/script.sh
-->
# Check Chat Is Current With Main

This read-only capability answers: does this chat branch already include the
latest local `main`?

It reports whether the chat branch is even, fresh-ahead, behind, or diverged
relative to a base branch, defaulting to `main`. With `--require-fresh`, it
exits non-zero when the chat branch is behind or diverged.

Use this when a workflow needs a simple freshness gate before continuing chat
work or before local merge/promotion decisions.
