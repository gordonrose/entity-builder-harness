<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain local Codex transcript discovery for a chat session.
domain: transcript
portability: llm-workbench-required
used_by:
  - scripts/00.chat/transcript/discover-codex-session-log/script.sh
  - scripts/00.chat/transcript/register-codex-session-log/script.sh
-->

# Discover Codex Session Log

`script.sh` searches the local Codex sessions directory for the JSONL
transcript that matches a chat session id, branch, or session log path.

It prints the newest matching transcript path. The result is used by commit
recording and transcript registration so chat metrics can be tied to actual
local evidence.

The script is read-only. It does not modify the session log or transcript.

