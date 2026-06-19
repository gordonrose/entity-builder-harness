# Chat Commands

## Purpose

Chat commands are small named shortcuts for governed chat lifecycle actions.
They make repeated actions easy to trigger without moving process rules into
`AGENTS.md`.

## Entry Point

Run commands through:

```bash
bash scripts/shared/chat/chat-command.sh <command> [args...]
```

List available commands with:

```bash
bash scripts/shared/chat/chat-command.sh list
```

## Commands

- `new <task summary>` - starts a new chat session using the same startup path
  as the default VS Code build task.
- `close` - prints or copies a governed prompt for committing approved work, if
  needed, then promoting the chat branch into local `main`.

The default VS Code build task routes through `chat-command.sh new`, so
Ctrl+Shift+B and the named `new` command exercise the same startup path.

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
