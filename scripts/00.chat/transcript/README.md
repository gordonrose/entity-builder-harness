<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain transcript discovery and registration scripts.
domain: transcript
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-start.md
  - scripts/00.chat/transcript/register-codex-session-log/README.md
-->

# Transcript Scripts

Transcript scripts connect chat session logs to local Codex JSONL transcripts.
That link lets later commit recording estimate transcript size, token usage,
and cost metadata from real session evidence.

These scripts inspect local transcript files. They do not upload transcripts or
depend on network access.

