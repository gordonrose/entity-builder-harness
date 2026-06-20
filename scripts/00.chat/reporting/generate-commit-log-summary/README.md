<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain on-demand aggregate summaries from chat session logs.
domain: reporting
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/skills/session-summary.md
  - scripts/00.chat/reporting/generate-commit-log-summary/script.sh
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

