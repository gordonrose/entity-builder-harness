# Change Shared Process Workflow

## Use When

Use this when a request changes shared chat, branch, git, commit, merge,
handoff, deployment, release, or context-preservation process.

## Required Gates

Before editing files:

```bash
bash scripts/shared/git/dirty-worktree-check.sh
```

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
- Do not commit, push, delete branches, or perform destructive actions without
  explicit user approval.
- Preserve unrelated user changes in a dirty worktree.
- Before any commit, complete the shared before-commit checklist.

## Prerequisite Branch State

Run:

```bash
bash scripts/shared/git/check-commit-prerequisites.sh
```

If this reports missing workflow, checklist, or gate files, stop the task
commit. Ask for explicit approval before merging or cherry-picking the
shared-process commit that introduced the missing files, then rerun this
workflow from the before-commit checklist.

Do not bypass the gate just because it is missing on the current branch.

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
