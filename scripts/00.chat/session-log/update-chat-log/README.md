<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.session-log.update-chat-log.readme
  version: 1
  status: active
  layer: 00.chat
  domain: session-log
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the internal structured chat log update helper.
  portability:
    class: internal
    targets: []
  used_by:
  - id: chat.checklists.before-commit
    path: .agentic/00.chat/checklists/before-commit.md
  - id: chat.script.session-log.update-chat-log
    path: scripts/00.chat/session-log/update-chat-log/script.sh
-->
# Update Chat Log

`script.sh` is an internal helper for appending structured entries to the
current chat session log.

It supports entries for questions, issues, decisions, commit summaries, and ADR
disposition. The helper keeps common log updates consistent so humans and
future agents can scan session history without guessing which section to read.

This script writes the current chat log only. It does not create commits,
record transcript metrics, or decide whether an ADR is needed.

