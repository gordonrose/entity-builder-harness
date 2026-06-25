<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.transcript.discover-codex-session-log.readme
  version: 1
  status: active
  layer: 00.chat
  domain: transcript
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain local Codex transcript discovery for a chat session.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.transcript.discover-codex-session-log
    path: scripts/00.chat/transcript/discover-codex-session-log/script.sh
  - id: chat.script.transcript.register-codex-session-log
    path: scripts/00.chat/transcript/register-codex-session-log/script.sh
-->
# Discover Codex Session Log

`script.sh` searches the local Codex sessions directory for the JSONL
transcript that matches a chat session id, branch, or session log path.

It prints the newest matching transcript path. The result is used by commit
recording and transcript registration so chat metrics can be tied to actual
local evidence.

The script is read-only. It does not modify the session log or transcript.

