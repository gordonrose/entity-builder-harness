<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.reporting.generate-commit-log-summary.readme
  version: 1
  status: active
  layer: 00.chat
  domain: reporting
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain on-demand aggregate summaries from chat session logs.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.skills.session-summary
    path: .agentic/00.chat/skills/session-summary.md
  - id: chat.script.reporting.generate-commit-log-summary
    path: scripts/00.chat/reporting/generate-commit-log-summary/script.sh
-->
# Generate Commit Log Summary

`script.sh` builds an aggregate summary from individual chat session logs.

By default it prints the summary. With `--output <path>`, it writes to an
explicit on-demand artifact path. It must not recreate the retired tracked
`commitLogs/README.md` file.

Use this capability when a human asks for a session overview, metrics summary,
or chat history report. The individual session logs remain the durable source.

`smoke-test.sh` verifies that summary generation works and that the retired
aggregate artifact is not written by default.

