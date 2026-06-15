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

## Before Commit

Run:

```bash
bash scripts/shared/git/finalize-chat-session-before-commit.sh
```

This verifies that the session log records decisions and an ADR disposition,
then records final session metrics.

Do not commit if the finalization gate fails.
