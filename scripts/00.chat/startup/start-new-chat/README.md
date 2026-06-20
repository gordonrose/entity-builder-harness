<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the new-chat startup wrapper.
domain: startup
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/commands/README.md
  - scripts/00.chat/startup/start-new-chat/script.sh
-->

# Start New Chat

`script.sh` is the canonical startup wrapper used by the public `new` command.
It delegates to `scripts/00.chat/startup/start-chat-session/script.sh`.

This wrapper exists so the public command surface can use a human phrase
(`new`) while the full startup engine keeps its descriptive capability name.

It can create branches, worktrees, and session logs through the startup engine.

