<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the chat command dispatcher capability and its script layout.
domain: command
portability: llm-workbench-required
used_by:
  - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
  - scripts/00.chat/command/dispatcher/script.sh
-->

# Chat Command Dispatcher

This capability owns the chat command dispatcher.

The dispatcher is the small command-line router for chat commands. It accepts a
command name such as `list`, `new`, or `close`, validates the name, finds the
matching executable under `scripts/00.chat/command/<name>/script.sh`, and
transfers control to that command script.

The dispatcher is not the implementation of each chat action. The subcommand
scripts remain separate so each command can evolve independently.

## Files

- `script.sh` is the canonical dispatcher entrypoint.
- `<command>/script.sh` files are canonical command entrypoints.
- `smoke-test.sh` validates the dispatcher and core chat subcommands in a
  throwaway repository.

Compatibility wrappers remain under `scripts/shared/chat/commands/` while old
external callers migrate.
