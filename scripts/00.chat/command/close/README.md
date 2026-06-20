<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the public chat close command entrypoint.
domain: command
portability: llm-workbench-required
used_by:
  - package.json scripts.chat:close
  - scripts/00.chat/command/close/script.sh
-->

# Close Command

`script.sh` is the canonical entrypoint for the public `chat:close` command. It
delegates to `scripts/00.chat/closeout/build-closeout-prompt/script.sh`.

The command exists so humans can use a stable public shortcut without knowing
where closeout prompt construction lives internally.

This command does not commit, merge, or push. It prepares the governed closeout
prompt for a later agent turn.

