<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.transcript.register-codex-session-log.readme
  version: 1
  status: active
  layer: 00.chat
  domain: transcript
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain recording the local Codex transcript path in the current chat log.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-start
    path: .agentic/00.chat/workflows/chat-start.md
  - id: chat.script.transcript.register-codex-session-log
    path: scripts/00.chat/transcript/register-codex-session-log/script.sh
-->
# Register Codex Session Log

`script.sh` discovers the current chat's local Codex JSONL transcript and
records that path in the current session log metadata.

Registration lets later commit recording estimate transcript-derived metrics
without rediscovering the transcript from scratch.

This script writes session-log metadata. It does not create commits or copy
transcript content into the repository.

