<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain closeout scripts that prepare governed end-of-chat prompts.
domain: closeout
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/commands/README.md
  - scripts/00.chat/closeout/build-closeout-prompt/README.md
-->

# Closeout Scripts

Closeout scripts prepare the handoff from active work to a final agent turn.
They do not commit or merge work by themselves. Instead, they build the prompt
that tells the next agent how to inspect the current chat, run required gates,
commit approved work, and report the result.

This keeps terminal shortcuts convenient without hiding approval boundaries.

