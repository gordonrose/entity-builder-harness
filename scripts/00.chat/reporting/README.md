<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain on-demand chat reporting scripts.
domain: reporting
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-reporting.md
  - scripts/00.chat/reporting/generate-commit-log-summary/README.md
-->

# Reporting Scripts

Reporting scripts summarize chat branches, worktrees, and session logs on
demand. They do not create always-generated aggregate artifacts.

The durable source evidence is each individual session log under `commitLogs/`.
Reports should be reproducible from those logs and should avoid reviving the
retired tracked `commitLogs/README.md` summary.

