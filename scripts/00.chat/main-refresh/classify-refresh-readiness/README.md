<!-- agentic-artifact:
owner: 00.chat
kind: guide
purpose: Explain dirty-state classification before refreshing a chat branch from main.
domain: main-refresh
portability: llm-workbench-required
used_by:
  - scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh
  - scripts/00.chat/main-refresh/classify-refresh-readiness/smoke-test.sh
-->

# Classify Refresh Readiness

This read-only capability answers: can this chat worktree refresh from `main`
right now?

It classifies the active worktree before any refresh action:

- `clean`: normal refresh or preflight can continue.
- `current-session-bookkeeping`: only the current session log is dirty.
- `repo-work`: normal repository files are dirty and need an approved commit or
  recovery path before refresh.
- `unsupported-dirty`: the workflow does not yet own a safe recovery path.

The script reports state only. Workflows decide what action is allowed next.
