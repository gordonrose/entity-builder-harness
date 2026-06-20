<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the internal structured chat log update helper.
domain: session-log
portability: internal
used_by:
  - .agentic/00.chat/checklists/before-commit.md
  - scripts/00.chat/session-log/update-chat-log/script.sh
-->

# Update Chat Log

`script.sh` is an internal helper for appending structured entries to the
current chat session log.

It supports entries for questions, issues, decisions, commit summaries, and ADR
disposition. The helper keeps common log updates consistent so humans and
future agents can scan session history without guessing which section to read.

This script writes the current chat log only. It does not create commits,
record transcript metrics, or decide whether an ADR is needed.

