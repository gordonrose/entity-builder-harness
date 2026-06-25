<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.closeout.readme
  version: 1
  status: active
  layer: 00.chat
  domain: closeout
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain closeout scripts that prepare governed end-of-chat prompts.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.commands.readme
    path: .agentic/00.chat/commands/README.md
  - id: chat.script.closeout.build-closeout-prompt.readme
    path: scripts/00.chat/closeout/build-closeout-prompt/README.md
-->
# Closeout Scripts

Closeout scripts prepare the handoff from active work to a final agent turn.
They do not commit or merge work by themselves. Instead, they build the prompt
that tells the next agent how to inspect the current chat, run required gates,
commit approved work, and report the result.

This keeps terminal shortcuts convenient without hiding approval boundaries.

