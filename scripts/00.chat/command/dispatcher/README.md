<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.command.dispatcher.readme
  version: 1
  status: active
  layer: 00.chat
  domain: command
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the chat command dispatcher capability and its script layout.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
  - id: chat.script.command.dispatcher
    path: scripts/00.chat/command/dispatcher/script.sh
-->
# Chat Command Dispatcher

This capability owns the chat command dispatcher.

The dispatcher is the small command-line router for chat commands. It accepts a
command name such as `list`, `new`, or `close`, validates the name, finds the
matching script under `scripts/00.chat/command/<name>/script.sh`, and transfers
control to that command through Bash.

The dispatcher is not the implementation of each chat action. The subcommand
scripts remain separate so each command can evolve independently.

## Files

- `script.sh` is the canonical dispatcher entrypoint.
- `<command>/script.sh` files are canonical command entrypoints.
- `smoke-test.sh` validates the dispatcher and core chat subcommands in a
  throwaway repository.

The dispatcher invokes command scripts with `bash` instead of requiring
executable mode, so archive extraction or Windows filesystems that strip mode
bits do not break the public command surface.

The old `scripts/shared/chat/commands/` compatibility wrappers have been
retired. Public callers should use `package.json` `chat:*` scripts; governed
callers should use canonical `scripts/00.chat/command/...` paths.
