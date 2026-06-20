<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the terminal chat command shortcut surface.
domain: command
portability: llm-workbench-required
used_by:
  - scripts/00.chat/command/dispatcher/README.md
  - scripts/00.chat/command/dispatcher/script.sh
-->

# Chat Commands

## Purpose

Chat commands are small named shortcuts for governed chat lifecycle actions.
They make repeated actions easy to trigger without moving process rules into
`AGENTS.md`.

## Entry Point

Run commands through:

```bash
npm run chat -- <command> [args...]
```

The canonical dispatcher is:

```bash
bash scripts/00.chat/command/dispatcher/script.sh <command> [args...]
```

Its capability README is:

```txt
scripts/00.chat/command/dispatcher/README.md
```

List available commands with:

```bash
npm run chat:list
```

## Commands

- `new <task summary>` - starts a new chat session from an explicit task
  summary.
- `open window [worktree-path|session-log]` - opens a new VS Code window for the
  current or specified chat-owned worktree.
- `close` - prints or copies a governed prompt for committing approved work, if
  needed, then promoting the chat branch into local `main`.

## Chat Message Auto-Start

When a chat starts in this repo and no matching chat session exists for the
current branch, the chat-start workflow treats the opening user message as the
new chat summary and runs:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/startup/auto-start-missing-session/script.sh "<opening user message>"
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
