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

`script.sh` is the chat startup engine. It turns a short task summary into the
working environment for one governed agent conversation: a `chat/*` branch, a
chat-owned worktree, a session log, and a first prompt for the next agent.

The important idea is that a chat is treated as a small, auditable unit of work.
Startup does the bookkeeping before the agent begins editing so the work has a
known owner, location, workflow, and history from the first turn.

## Mental Model

The root worktree is the integration console. It is where finished chat work can
be reviewed, merged, and coordinated.

Each chat gets its own branch and sibling worktree. That keeps task edits away
from the integration console and away from other active chats. If several chats
are open at once, each one has a physical directory and branch that belong to
that conversation.

The session log is the chat's durable memory. It records the task, branch,
worktree, routing metadata, commits, unresolved questions, decisions, conflicts,
and metrics. The harness uses that file as the first source of truth when a chat
resumes.

The first prompt is the handoff packet. It tells the next agent the exact branch,
worktree, layer, mode, workflow, and dirty-state handling rule. That prevents a
new agent from guessing where it should work or which workflow governs the
conversation.

## Inputs

- Task summary: the human description of the work. It can be passed as command
  arguments, or entered interactively when the script prompts for it.
- `.agentic/env.local`: optional local environment values for this checkout.
- `CHAT_COPY_PROMPT`: controls terminal first-prompt handoff. The default is
  `copy`, which tries the clipboard first and prints the prompt as a fallback.
  Use `skip` to print only.
- `CHAT_CLEANUP_EMPTY_BRANCHES`: controls startup cleanup. The default is
  `apply`, which removes empty abandoned chat branches through the governed
  cleanup script. Use `dry-run` to inspect only, or `skip` when startup should
  not clean empty chat branches.

## Terminal Handoff And IDE Integrations

The startup script always builds a first prompt. That prompt is a portable
session packet for terminal-based startup: it contains the task, session log,
chat worktree, layer, mode, workflow, and dirty-worktree stop response.

`CHAT_COPY_PROMPT` only controls how that terminal packet is handed to a human:
copy it to the clipboard, or print it in the terminal. It is a terminal
convenience, not the startup contract.

IDE extensions and app integrations should not depend on clipboard behavior.
They should use the startup data directly:

- task summary
- session log path
- chat worktree path
- layer
- mode
- workflow
- starting worktree status

That keeps the durable startup model the same while allowing different surfaces
to present or pass the session packet in their own way.

## Flow

1. Validate the task summary.

   Startup rejects an empty task or the placeholder `new chat` because the
   summary becomes the session identity. A useful summary makes the branch,
   folder, and log readable later.

2. Create the session id and branch name.

   The script combines a timestamp with a slug from the task summary. That gives
   each chat a stable id and creates a branch name like
   `chat/2026-06-19-20-27-move-chat-session-startup-engine`.

3. Classify the task.

   The classifier chooses the harness layer, mode, and workflow. This is why the
   first prompt can tell the agent whether it is doing chat lifecycle work,
   harness maintenance, education work, product work, or another governed path.

4. Capture the starting worktree state.

   Startup records whether the current worktree was clean or dirty. If it was
   dirty, the first prompt tells the next agent to stop and ask for confirmation
   before doing more discovery. That protects existing uncommitted work.

5. Create the branch and chat-owned worktree.

   The branch starts from `main` when available. If `main` does not exist, the
   script falls back to the current branch so the harness can still bootstrap in
   a new or unusual repo. The sibling worktree is where the chat should edit
   files.

6. Write the session log.

   The log is created at
   `commitLogs/<year>/<month>/<day>/<session>/README.md` inside the new
   worktree. It starts with machine-readable session metadata and human-readable
   sections for activity, decisions, issues, commits, conflicts, and metrics.

7. Print or copy the first prompt for terminal use.

   The prompt is the bridge from startup automation into the next agent turn. It
   names the task, session log, worktree, layer, mode, workflow, and the
   dirty-worktree stop response. Terminal startup can copy or print it. IDE and
   app integrations should treat those fields as structured startup data rather
   than depending on clipboard behavior.

8. Clean empty chat branches.

   Startup can run the empty-chat-branch cleanup script after creating the new
   session. This keeps abandoned zero-commit chat branches from accumulating
   while still routing cleanup through a governed script.

9. Stage the session log in the chat worktree.

   The log is staged so the first real task commit can include the session
   record if appropriate. The root worktree is left alone.

## What This Does Not Do

- It does not push anything.
- It does not merge the chat branch.
- It does not grant write permission to the agent.
- It does not decide that dirty root work is safe to ignore.
- It does not replace the workflow listed in the session metadata.

## Typical Result

After a successful run, expect:

- a new `chat/*` branch
- a sibling chat worktree
- a staged session log inside that worktree
- a first prompt printed or copied for the next agent
- the original root worktree still on its original branch

## Smoke Test

`smoke-test.sh` creates a throwaway Git repo and runs startup there. It verifies
that startup leaves the root repo on `main`, creates a separate chat worktree,
stages the session log in that chat worktree, records chat startup metadata, and
falls back to printed terminal handoff when clipboard copy fails.

## Compatibility

The old request-initialization entrypoint remains at
`scripts/shared/chat/request-initialization/start-chat-session.sh`. It delegates
to this canonical script until smoke fixtures, downstream references, and any
external users no longer need the shared path.
