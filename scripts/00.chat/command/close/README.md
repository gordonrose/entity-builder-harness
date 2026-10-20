<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.script.command.close.readme
  version: 1
  status: active
  created_on: "2026-06-20"
  updated_on: "2026-10-20"
  layer: 00.chat
  domain: command
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the public chat close command entrypoint.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.command.close
    path: scripts/00.chat/command/close/script.sh
-->
# Close Command

`script.sh` is the canonical entrypoint for the public `chat:close` command. It
delegates to `scripts/00.chat/closeout/build-closeout-prompt/script.sh`.

The command exists so humans can use a stable public shortcut without knowing
where closeout prompt construction lives internally.

This command does not commit, merge, or push. It prepares the governed closeout
prompt for a later agent turn.

