<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain how opening-prompt auto-start decides whether to create a governed chat session.
domain: startup
portability: llm-workbench-required
used_by:
  - scripts/00.chat/startup/auto-start-missing-session/script.sh
  - scripts/00.chat/command/dispatcher/smoke-test.sh
  - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
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

That means auto-start does not create a separate startup model. It only turns a
valid opening prompt into the same branch, worktree, session log, and first
prompt that `start-chat-session` would create.

## Decisions

1. Empty prompt

   An empty opening prompt is rejected. There is no task summary to name the
   session, classify the workflow, or write useful session metadata.

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

The old request-initialization entrypoint remains at
`scripts/shared/chat/request-initialization/auto-start-missing-session.sh`.
It delegates to this canonical script because the governed runner still
allowlists the shared path for approved auto-start actions.
