# Main Updated Workflow

## Use When

Use this after `main` changes, or when a chat branch may need to absorb newer
accepted work from `main`.

## Purpose

Keep `main` as the canonical accepted baseline while preserving chat branch
history, user work, and session evidence.

## Required Gates

Before changing branches, merging, rebasing, staging, or committing, run:

```bash
bash scripts/shared/git/dirty-worktree-check.sh
```

<!-- deterministic-check: allow reason="workflow defines the exact blocked response for the dirty-worktree gate" -->
If dirty, respond exactly:

```txt
Blocked: dirty worktree. Confirm proceed? Layer: shared. Mode: <mode>. Workflow: .agentic/shared/workflows/main-updated.md
```

Do not edit files or change branches while blocked.

## Main Update Intake

1. Confirm `main` exists locally:

   ```bash
   git show-ref --verify --quiet refs/heads/main
   ```

<!-- deterministic-check: allow reason="remote presence is reported by main-update-status.sh; workflow keeps the human fetch policy visible" -->
2. If a remote exists, fetch before comparing:

   ```bash
   git fetch --prune
   git branch -vv --all
   ```

<!-- deterministic-check: allow reason="main-update-status.sh emits the local-only freshness warning deterministically" -->
3. If no remote exists, state that freshness is only local.

4. Inspect branch relationship:

   ```bash
   bash scripts/shared/git/main-update-status.sh
   ```

5. Inspect active branch metadata and changed-path overlap:

   ```bash
   bash scripts/shared/git/active-chat-branches.sh
   bash scripts/shared/git/branch-overlap-report.sh
   ```

## Refresh Policy

- New chat branches should start from `main`.
- Existing active chat branches should be compared with `main` before more
  work is added.
- Prefer merging `main` into an active chat branch because it preserves history
  and does not rewrite published or session evidence.
- Rebase, cherry-pick repair, force update, branch deletion, and push require
  explicit user approval in the current chat.
- Never discard dirty work to refresh a branch.
- If conflicts appear, stop after Git reports the conflict set. Summarize the
  conflicting files and ask for approval before resolving them.

## Recommended Active-Branch Flow

1. Record the starting branch:

   ```bash
   git branch --show-current
   ```

2. Inspect status:

   ```bash
   git status --short --branch
   bash scripts/shared/git/main-update-status.sh
   bash scripts/shared/git/active-chat-branches.sh
   bash scripts/shared/git/branch-overlap-report.sh
   ```

3. If the active chat branch is behind `main`, ask before integrating `main`
   unless the user already explicitly requested that operation.

4. For an approved non-rewriting refresh:

   ```bash
   git merge --no-ff main
   ```

5. Run the relevant checks for the changed layer before committing.

6. Record decisions, issues, and ADR disposition in the current session log
   before any task commit.

## After Refresh

- Report whether the branch is now even with, ahead of, behind, or diverged
  from `main`.
- Note whether the comparison used local refs only or included a remote fetch.
- Do not commit the refresh unless the user explicitly approves the commit.
