# Change Shared Process Workflow

## Use When

Use this when a request changes cross-layer git, commit, merge, handoff,
deployment, release, or context-preservation process.

Chat lifecycle changes belong to `.agentic/00.chat/`, even while some legacy
workflow and script paths remain under `.agentic/shared/` or `scripts/shared/`.

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
- Chat task work must run in the chat-owned worktree recorded in the current
  session log. The root worktree is the local integration console and must not
  receive task edits, staging, formatting, or commits.
- After explicit write permission for the chat, routine session bookkeeping may
  be staged without another prompt when limited to the current chat session log.
- Preserve unrelated user changes in a dirty worktree.
- Before any commit, complete the shared before-commit checklist.

## Chat-Owned Worktree

Before writing, run:

```bash
bash scripts/shared/git/check-write-location.sh
```

<!-- deterministic-check: allow reason="ensure-chat-worktree.sh enforces worktree creation and verification; workflow states when agents should invoke it" -->
If a session log exists but its worktree is missing, recreate or verify it with:

```bash
bash scripts/shared/chat/ensure-chat-worktree.sh <session-log>
```

The chat-owned worktree has its own files and index. Stage only approved
repository-relative paths inside that worktree. The root worktree remains the
local convergence console.

## Prerequisite Branch State

Run:

```bash
bash scripts/shared/git/check-commit-prerequisites.sh
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
bash scripts/shared/harness/check-deterministic-process-drift.sh --staged
```

For broader audits, run the same script with `--commit <sha>`, `--paths
<path>...`, or `--all`.

<!-- deterministic-check: allow reason="requires human review and approval before editing process prose" -->
If the check flags scriptable process prose, propose the script or gate change
for approval. Do not rewrite prose automatically.

## Commit Log Deletions

Run:

```bash
bash scripts/shared/git/check-commitlog-deletions.sh
```

Empty, unsaved session logs may be deleted by intentional cleanup. Do not delete
commit logs that record commits or are explicitly marked for retention. If this
gate fails, restore the protected logs or remove them from the staged deletion
set before committing.

## Before Commit

Run:

```bash
bash scripts/shared/git/prepare-chat-session-before-commit.sh
```

This verifies that the session log records decisions and an ADR disposition,
without marking the chat as complete.

Do not commit if the preparation gate fails.

## After Commit

Run:

```bash
bash scripts/shared/git/record-chat-commit.sh <sha> <message> <summary> [adr-impact]
```

This appends the commit to the session log and updates the rolling
`latest_commit_*` session metrics. If a later commit happens in the same chat,
record it the same way; the latest commit is the current session endpoint.

<!-- deterministic-check: allow reason="checkpoint helper enforces narrow file scope; prose states the human-readable policy" -->
If recording a user-approved task commit leaves only session bookkeeping dirty,
the prior chat write permission authorizes creating a session-log checkpoint
commit without another prompt:

```bash
bash scripts/shared/git/checkpoint-chat-session-log.sh
```

<!-- deterministic-check: allow reason="checkpoint helper enforces file scope; prose states the human-readable policy" -->
The checkpoint commit is bookkeeping only and must contain no files except the
current chat session log. Stop and ask if any other path is staged, unstaged,
or would be committed.
