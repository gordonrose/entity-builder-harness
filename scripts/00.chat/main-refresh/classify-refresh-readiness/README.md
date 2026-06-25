<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.main-refresh.classify-refresh-readiness.readme
  version: 1
  status: active
  layer: 00.chat
  domain: main-refresh
  disciplines:
  - agentic
  kind: guide
  purpose: Explain dirty-state classification before refreshing a chat branch from main.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.main-refresh.classify-refresh-readiness
    path: scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh
  - id: chat.script.main-refresh.classify-refresh-readiness.smoke-test
    path: scripts/00.chat/main-refresh/classify-refresh-readiness/smoke-test.sh
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
