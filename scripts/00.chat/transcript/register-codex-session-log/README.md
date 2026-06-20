<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain recording the local Codex transcript path in the current chat log.
domain: transcript
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-start.md
  - scripts/00.chat/transcript/register-codex-session-log/script.sh
-->

# Register Codex Session Log

`script.sh` discovers the current chat's local Codex JSONL transcript and
records that path in the current session log metadata.

Registration lets later commit recording estimate transcript-derived metrics
without rediscovering the transcript from scratch.

This script writes session-log metadata. It does not create commits or copy
transcript content into the repository.

