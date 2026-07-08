<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.commands.readme
  version: 1
  status: active
  layer: 00.chat
  domain: command
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the terminal chat command shortcut surface.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.command.dispatcher.readme
    path: scripts/00.chat/command/dispatcher/README.md
  - id: chat.script.command.dispatcher
    path: scripts/00.chat/command/dispatcher/script.sh
-->
# Chat Commands

## Purpose

Chat commands are small named shortcuts for governed chat lifecycle actions.
They make repeated actions easy to trigger without moving process rules into
`AGENTS.md`.

## Public CLI Entry Point

The public user-facing CLI is:

```bash
llm-wb <command> [args...]
```

Use `npx llm-wb ...` when the package is not installed globally or linked into
the current shell.

Current public CLI shortcuts include:

- `init` - installs the workbench into the current or specified Git repo.
- `new <prompt>` - starts a new chat session from an explicit prompt.
- `list` - lists installed workbench command names.
- `sessions list` - lists active chat sessions and branches.
- `commit -m <message>` - runs commit gates, commits task work, records the
  commit, and checkpoints session evidence.
- `merge-main` - verifies readiness and merges the chat branch into local
  `main` without pushing.

## Dispatcher Entry Point

The canonical dispatcher is:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/command/dispatcher/script.sh <command> [args...]
```

Its capability README is:

```txt
scripts/00.chat/command/dispatcher/README.md
```

## Commands

- `new <prompt>` - starts a new chat session from an explicit prompt.
- `open window [worktree-path|session-log]` - opens a new VS Code window for the
  current or specified chat-owned worktree.
- `download repo [worktree-path|session-log]` - exports the selected chat
  worktree as a portable review bundle.
- `download repo diff [--base <ref>] [worktree-path|session-log]` - exports only
  files changed relative to a base ref, defaulting to local `main`.
- `close` - prints or copies a governed prompt for committing approved work, if
  needed, then promoting the chat branch into local `main`.

## Chat Message Auto-Start

When a chat starts in this repo and no matching chat session exists for the
current branch, the chat-start workflow treats the opening user message as the
new chat summary and runs the resolver:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/startup/resolve-current-chat-session/script.sh "<opening user message>"
```

If the opening message is exactly `new`, the agent asks what the chat should be
about before creating a session.

## Adding A Command

Add a new executable script at:

```txt
scripts/00.chat/command/<name>/script.sh
```

Use lowercase command names when possible. Keep the command script narrow:

- delegate to existing governed scripts when the action is deterministic
- print or copy a prompt when the action needs agent judgment or user approval
- preserve existing approval boundaries for commits, merges, pushes, branch
  deletion, destructive actions, and history rewriting

Update the dispatcher smoke test named in its capability README when adding a
command that should remain part of the stable shortcut surface.

The old `scripts/shared/chat/commands/<name>.sh` compatibility path has been
retired. Do not add new commands there; add canonical
`scripts/00.chat/command/<name>/script.sh` entrypoints and package-script
shortcuts instead.
