<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.main-refresh.readme
  version: 1
  status: active
  layer: 00.chat
  domain: main-refresh
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain scripts for refreshing chat branches from local main.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-refresh-from-main
    path: .agentic/00.chat/workflows/chat-refresh-from-main.md
  - id: chat.script.main-refresh.rehearse-refresh-from-main.readme
    path: scripts/00.chat/main-refresh/rehearse-refresh-from-main/README.md
-->
# Main Refresh Scripts

Main-refresh scripts help a chat branch catch up with local `main` without
rewriting history or hiding conflicts.

The domain is split into inspection, readiness classification, rehearsal, and
apply steps. Rehearsal lets the harness discover conflicts in a disposable
preflight branch/worktree before the real chat branch is changed.

Conflict capabilities in this domain:

- `classify-conflict/` classifies known main-refresh conflict shapes using the
  governed conflict type standard.
- `verify-conflict-audit/` checks that conflicted paths have matching
  `## Main Refresh Conflicts` session-log entries before a resolved preflight
  is applied or promoted.

These scripts do not push. They coordinate local chat branch refresh behavior.
