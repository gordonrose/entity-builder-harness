<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.transcript.readme
  version: 1
  status: active
  layer: 00.chat
  domain: transcript
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain transcript discovery and registration scripts.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-start
    path: .agentic/00.chat/workflows/chat-start.md
  - id: chat.script.transcript.register-codex-session-log.readme
    path: scripts/00.chat/transcript/register-codex-session-log/README.md
-->
# Transcript Scripts

Transcript scripts connect chat session logs to assistant transcript evidence.
The core metadata is provider-neutral:

- `transcript_provider`
- `transcript_path`
- `transcript_bytes`
- `transcript_source`

Codex JSONL discovery is one optional adapter for filling those fields. Other
assistants can provide transcript byte counts or paths directly.

These scripts inspect local transcript files. They do not upload transcripts or
depend on network access.
