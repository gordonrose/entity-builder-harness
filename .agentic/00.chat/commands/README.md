# Chat Commands

## Purpose

Chat commands are small named shortcuts for governed chat lifecycle actions.
They make repeated actions easy to trigger without moving process rules into
`AGENTS.md`.

## Entry Point

Run commands through:

```bash
bash scripts/chat/chat-command.sh <command> [args...]
```

The compatibility entrypoint remains:

```bash
bash scripts/shared/chat/chat-command.sh <command> [args...]
```

List available commands with:

```bash
bash scripts/chat/chat-command.sh list
```

## Commands

- `new <task summary>` - starts a new chat session from an explicit task
  summary.
- `close` - prints or copies a governed prompt for committing approved work, if
  needed, then promoting the chat branch into local `main`.

## Chat Message Auto-Start

When a chat starts in this repo and no matching chat session exists for the
current branch, the chat-start workflow treats the opening user message as the
new chat summary and runs:

```bash
bash scripts/shared/chat/request-initialization/auto-start-missing-session.sh "<opening user message>"
```

If the opening message is exactly `new`, the agent asks what the chat should be
about before creating a session.

## Adding A Command

Add a new executable script at:

```txt
scripts/shared/chat/commands/<name>.sh
```

Use lowercase command names when possible. Keep the command script narrow:

- delegate to existing governed scripts when the action is deterministic
- print or copy a prompt when the action needs agent judgment or user approval
- preserve existing approval boundaries for commits, merges, pushes, branch
  deletion, destructive actions, and history rewriting

Update `scripts/shared/chat/smoke-test-chat-command.sh` when adding a command
that should remain part of the stable shortcut surface.
