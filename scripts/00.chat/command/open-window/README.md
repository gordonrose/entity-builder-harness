<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.command.open-window.readme
  version: 1
  status: active
  layer: 00.chat
  domain: command
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the public chat open-window command entrypoint.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.command.open-window
    path: scripts/00.chat/command/open-window/script.sh
-->
# Open Window Command

`script.sh` is the canonical entrypoint for opening the current chat-owned
worktree in a new VS Code window.

Run it as:

```bash
npm run chat -- open window
```

The hyphenated form also works:

```bash
npm run chat -- open-window
```

When run outside a chat branch, pass either a chat worktree path or a session-log
`README.md` path.
