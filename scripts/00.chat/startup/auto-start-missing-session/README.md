<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.startup.auto-start-missing-session.readme
  version: 1
  status: active
  layer: 00.chat
  domain: startup
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain how opening-prompt auto-start decides whether to create a governed
    chat session.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.startup.auto-start-missing-session
    path: scripts/00.chat/startup/auto-start-missing-session/script.sh
  - id: chat.script.command.dispatcher.smoke-test
    path: scripts/00.chat/command/dispatcher/smoke-test.sh
  - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
    path: docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
-->
# Auto-Start Missing Session

`script.sh` is the bridge between an opening user message and the normal chat
startup engine.

It exists for the moment when a chat starts without usable session metadata. In
that case, the harness needs to decide whether the opening message should become
a new governed chat session, or whether startup should stop and ask the human
for clearer intent.

## Mental Model

Normal startup is explicit: a human or command asks to start a chat with a task
summary.

Auto-start is recovery startup: the harness has an opening prompt but no
session log metadata yet. Rather than guessing silently, this script applies a
small set of routing rules and then delegates to the normal `chat-command new`
path.

Agents should normally reach this through `resolve-current-chat-session`, which
first checks whether current session metadata already exists and only delegates
here for the missing-session path.

That means auto-start does not create a separate startup model. It only turns a
valid opening prompt into the same branch, worktree, session log, and first
prompt that `start-chat-session` would create.

## Decisions

1. Empty prompt

   An empty opening prompt is rejected. There is no task summary to name the
   session, create a useful branch/worktree identity, or write useful session
   metadata.

2. Bare `new`

   A message that is exactly `new` is treated as incomplete intent. The script
   asks:

   ```txt
   What should the new chat be about?
   ```

   This prevents the harness from creating a low-information branch and log.

3. `ignore chat start`

   If the opening prompt begins with `ignore chat start`, auto-start exits
   cleanly without creating a session. This is the explicit escape hatch for
   chats that should bypass the chat-start workflow.

4. Any other opening prompt

   The prompt is passed to:

   ```bash
   bash scripts/00.chat/command/dispatcher/script.sh new "$PROMPT"
   ```

   The dispatcher then routes to the normal startup command.

## What This Does Not Do

- It does not classify tasks itself.
- It does not create branches or worktrees directly.
- It does not write the session log directly.
- It does not bypass the normal startup engine.
- It does not replace the governed runner allowlist for the old compatibility
  path.

## Validation

The dispatcher smoke test covers this capability. It verifies that an opening
prompt creates a chat session, that the task text is preserved, and that a bare
`new` prompt asks for a task summary instead of creating a vague session.

Run it with:

```bash
bash scripts/00.chat/command/dispatcher/smoke-test.sh
```

## Compatibility

The old request-initialization entrypoint
`scripts/shared/chat/request-initialization/auto-start-missing-session.sh` has
been retired. New callers should use this canonical script through the governed
runner.
