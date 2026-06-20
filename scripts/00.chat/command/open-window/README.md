<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the public chat open-window command entrypoint.
domain: command
portability: llm-workbench-required
used_by:
  - package.json scripts.chat:open-window
  - scripts/00.chat/command/open-window/script.sh
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
