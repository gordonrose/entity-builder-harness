<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain reading current chat session metadata.
domain: session-log
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-start.md
  - scripts/00.chat/session-log/read-current-chat-log/script.sh
-->

# Read Current Chat Log

`script.sh` prints the metadata block from the current chat branch's session
log.

It is useful when a workflow or human needs to inspect the current session id,
branch, worktree, layer, mode, or workflow without opening the full log.

The script requires the current branch to be a `chat/*` branch and the matching
session log to exist. It is read-only.

