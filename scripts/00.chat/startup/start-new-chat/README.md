<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.startup.start-new-chat.readme
  version: 1
  status: active
  layer: 00.chat
  domain: startup
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the new-chat startup wrapper.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.commands.readme
    path: .agentic/00.chat/commands/README.md
  - id: chat.script.startup.start-new-chat
    path: scripts/00.chat/startup/start-new-chat/script.sh
-->
# Start New Chat

`script.sh` is the canonical startup wrapper used by the public `new` command.
It delegates to `scripts/00.chat/startup/start-chat-session/script.sh`.

This wrapper exists so the public command surface can use a human phrase
(`new`) while the full startup engine keeps its descriptive capability name.

It can create branches, worktrees, and session logs through the startup engine.

