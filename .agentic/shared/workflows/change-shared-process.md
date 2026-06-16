# Change Shared Process Workflow

## Use When

Use this when a request changes shared chat, branch, git, commit, merge,
handoff, deployment, release, or context-preservation process.

## Required Gates

Before editing files:

```bash
bash scripts/shared/git/dirty-worktree-check.sh --allow-session-bookkeeping
```

`bookkeeping-only` is acceptable after explicit write permission for the chat.
<!-- deterministic-check: allow reason="workflow defines exact blocked response around dirty-worktree gate output" -->
If dirty, respond exactly:

```txt
Blocked: dirty worktree. Confirm proceed? Layer: shared. Mode: <mode>. Workflow: .agentic/shared/workflows/change-shared-process.md
```

Do not edit files while blocked.

## Rules

- Use the current branch session log as the first source of truth.
- Keep `AGENTS.md` as a router; put procedure in shared workflows, checklists,
  gates, or scripts.
- Prefer deterministic scripts for repeatable checks.
- Do not create a task commit, push, delete branches, rewrite history, discard
  work, overwrite work, or perform destructive actions without explicit user
  approval.
- For commit preparation, staging for approved commits, task commits after
  explicit approval, commit recording, and narrow session-bookkeeping
  checkpoint commits, agents must run commit-boundary commands in an isolated
  worktree for the branch recorded in the current chat session log.
- After explicit write permission for the chat, routine session bookkeeping may
  be staged without another prompt when limited to the current chat session log
  and `commitLogs/README.md`.
- Preserve unrelated user changes in a dirty worktree.
- Before any commit, complete the shared before-commit checklist.

## Isolated Commit Worktree

Wrap approved commit-boundary commands with the session branch helper:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- <command> [args...]
```

The helper reads the target branch from the session log, verifies that it names
a local `chat/*` branch, creates or reuses a deterministic isolated worktree
under `${AGENTIC_CHAT_WORKTREE_ROOT:-/tmp/agentic-chat-worktrees/...}`, and runs
the command there. It does not switch, stage, clean, or discard anything in the
active user worktree.

<!-- deterministic-check: allow reason="with-chat-branch.sh enforces these stop conditions; workflow prose summarizes the human policy" -->
Reuse is deterministic: the same repo path and branch map to the same isolated
worktree path. The helper reuses that worktree when it already exists and stops
if the path is not a worktree, belongs to a different repository, or is checked
out on a different branch. If the active user worktree is already on the target
session branch, the helper may create the isolated worktree with Git's duplicate
checkout force flag; it must still leave active files and index state alone. It
also stops if the session branch is missing, non-local, not under `chat/*`,
already checked out outside the active and isolated paths, or the wrapped
command fails.

Cleanup is manual and explicit. The helper leaves the isolated worktree in
place so approved staging and commit commands can operate across multiple
commit-boundary steps. Do not delete or prune isolated worktrees as part of this
workflow unless the user explicitly approves that cleanup.

This authorization is limited to commit-boundary operations. It does not
authorize pushes, merges, rebases, branch deletion, history rewrite, discarding
work, or destructive actions.

## Staging Approved Paths

After explicit approval to stage paths for a task commit, mirror only those
approved paths into the isolated worktree:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/stage-active-worktree-paths.sh <path>...
```

This stages the named paths in the isolated worktree from the active worktree.
Use repository-relative paths only. Do not use broad pathspecs when unrelated
work is present.

## Prerequisite Branch State

Run:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/check-commit-prerequisites.sh
```

<!-- deterministic-check: allow reason="requires human approval before merge or cherry-pick repair" -->
If this reports missing workflow, checklist, or gate files, stop the task
commit. Ask for explicit approval before merging or cherry-picking the
shared-process commit that introduced the missing files, then rerun this
workflow from the before-commit checklist.

Do not bypass the gate just because it is missing on the current branch.

## Deterministic Process Drift

For commit-gate scope, run:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/harness/check-deterministic-process-drift.sh --staged
```

For broader audits, run the same script with `--commit <sha>`, `--paths
<path>...`, or `--all`.

<!-- deterministic-check: allow reason="requires human review and approval before editing process prose" -->
If the check flags scriptable process prose, propose the script or gate change
for approval. Do not rewrite prose automatically.

## Before Commit

Run:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/prepare-chat-session-before-commit.sh
```

This verifies that the session log records decisions and an ADR disposition,
without marking the chat as complete.

Do not commit if the preparation gate fails.

## After Commit

Run:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/record-chat-commit.sh <sha> <message> <summary> [adr-impact]
```

This appends the commit to the session log and updates the rolling
`latest_commit_*` session metrics. If a later commit happens in the same chat,
record it the same way; the latest commit is the current session endpoint.

<!-- deterministic-check: allow reason="checkpoint helper enforces narrow file scope; prose states the human-readable policy" -->
If recording a user-approved task commit leaves only session bookkeeping dirty,
the prior chat write permission authorizes creating a session-log checkpoint
commit without another prompt:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/checkpoint-chat-session-log.sh
```

<!-- deterministic-check: allow reason="checkpoint helper enforces file scope; prose states the human-readable policy" -->
The checkpoint commit is bookkeeping only and must contain no files except the
current chat session log and `commitLogs/README.md`. Stop and ask if any other
path is staged, unstaged, or would be committed.
