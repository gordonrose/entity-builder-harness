<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.reporting.readme
  version: 1
  status: active
  layer: 00.chat
  domain: reporting
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain on-demand chat reporting scripts.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-reporting
    path: .agentic/00.chat/workflows/chat-reporting.md
  - id: chat.script.reporting.generate-commit-log-summary.readme
    path: scripts/00.chat/reporting/generate-commit-log-summary/README.md
-->
# Reporting Scripts

Reporting scripts summarize chat branches, worktrees, and session logs on
demand. They do not create always-generated aggregate artifacts.

The durable source evidence is each individual session log under `commitLogs/`.
Reports should be reproducible from those logs and should avoid reviving the
retired tracked `commitLogs/README.md` summary.

