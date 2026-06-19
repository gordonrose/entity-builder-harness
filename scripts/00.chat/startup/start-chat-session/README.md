<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain how the chat session startup engine creates branches, logs, prompts, and worktrees.
domain: startup
portability: llm-workbench-required
used_by:
  - scripts/00.chat/startup/start-chat-session/script.sh
  - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
-->

# Start Chat Session

`script.sh` is the chat startup engine. It turns a short task summary into a
governed chat branch, a chat-owned worktree, a session log, and a first prompt
for the next agent.

## Inputs

- Task summary: passed as arguments, or entered at the prompt.
- `.agentic/env.local`: optional local environment values.
- `CHAT_COPY_PROMPT`: `copy` by default; use `skip` to print without clipboard
  handoff.
- `CHAT_CLEANUP_EMPTY_BRANCHES`: `apply` by default; use `dry-run` or `skip`
  when startup should not clean empty chat branches.

## Flow

1. Normalize the task summary into a timestamped session id and `chat/*` branch.
2. Classify the task into layer, mode, and workflow metadata.
3. Create the chat branch from `main`, or the current branch when `main` is not
   available.
4. Create the chat-owned worktree for that branch.
5. Write `commitLogs/<year>/<month>/<day>/<session>/README.md` inside the chat
   worktree.
6. Print or copy the first prompt that tells the next agent which branch,
   worktree, layer, mode, and workflow to use.
7. Run empty-chat-branch cleanup according to `CHAT_CLEANUP_EMPTY_BRANCHES`.
8. Stage the new session log in the chat worktree.

## Compatibility

The old request-initialization entrypoint remains at
`scripts/shared/chat/request-initialization/start-chat-session.sh`. It delegates
to this canonical script until smoke fixtures, downstream references, and any
external users no longer need the shared path.
