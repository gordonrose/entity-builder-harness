<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.startup.resolve-current-chat-session.readme
  version: 1
  status: active
  layer: 00.chat
  domain: startup
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the startup resolver that reads current metadata or auto-starts
    missing chat sessions.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.startup.resolve-current-chat-session
    path: scripts/00.chat/startup/resolve-current-chat-session/script.sh
  - id: chat.workflows.chat-start
    path: .agentic/00.chat/workflows/chat-start.md
-->
# Resolve Current Chat Session

`script.sh` is the single startup entrypoint for agents following the chat-start
workflow.

It first asks `read-current-chat-log` for existing session metadata. If the
current branch is already a usable chat branch, the metadata is printed and no
startup mutation happens.

If the current branch has no matching chat session, including the common root
`main` case, the script delegates to `auto-start-missing-session` with the
opening user message. That creates the normal chat branch, chat-owned worktree,
session log, and first prompt.

Other failures are passed through unchanged. In particular,
`recorded-session-approval-required` remains a stop condition until the user
explicitly approves continuing the recorded chat/worktree.

Run it through the governed runner:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/startup/resolve-current-chat-session/script.sh "<opening user message>"
```

## Validation

Run the smoke test with:

```bash
bash scripts/00.chat/startup/resolve-current-chat-session/smoke-test.sh
```

It verifies that root `main` with no chat session auto-starts from the opening
prompt, and that an existing chat worktree returns metadata without creating a
second chat branch.
