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
bash scripts/shared/git/classify-main-refresh-dirty-state.sh
```

<!-- deterministic-check: allow reason="classifier determines dirty state; workflow defines the human-facing blocked response" -->
If the classifier reports `unsupported-dirty`, respond exactly:

```txt
Blocked: required action is not governed.
Action needed: refresh chat branch from main
Blocking condition: unsupported dirty state before main refresh
Missing governance: .agentic/shared/workflows/main-updated.md does not define a deterministic recovery path for this dirty state
Confirm update the harness or approve a one-off exception?
```

Do not edit files, change branches, stash, restore, merge, rebase, stage, or
commit while blocked.

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
- Main refresh is branch maintenance. Keep it separate from task commits.
- Prefer merging `main` into an active chat branch because it preserves history
  and does not rewrite published or session evidence.
- For normal repository work, prefer a governed chat checkpoint commit before
  refreshing from `main`; do not hide task work in stash by default.
- Preflight the refresh in a temporary worktree before mutating the active chat
  worktree when the branch has task commits or a checkpoint.
- Rebase, cherry-pick repair, force update, branch deletion, and push require
  explicit user approval in the current chat.
- Never discard dirty work to refresh a branch.
- Do not use `git stash` in this workflow unless a later governed stash
  capability defines exact path scope, stash identity recording, apply/drop
  behavior, and conflict handling.
- If conflicts appear outside a governed recovery path, stop after Git reports
  the conflict set. Summarize the conflicting files and ask for approval before
  resolving them.

## Dirty State Classes

Classify before refresh:

```bash
bash scripts/shared/git/classify-main-refresh-dirty-state.sh
```

The classifier reports state; the workflow decides what is allowed.

- `clean`: the active chat worktree can use the normal refresh or preflight
  flow.
- `current-session-bookkeeping`: dirty paths are limited to the current chat
  session log and `commitLogs/README.md`. Preserve the session log. If the
  incoming `main` overlap includes the current session log, stop.
- `generated-commitlog-summary`: only `commitLogs/README.md` is dirty, and it
  matches `bash scripts/shared/chat/generate-commit-log-summary.sh --check`.
  This derived file may be restored before refresh and regenerated after
  refresh if the user approves that recovery.
- `repo-work`: dirty paths include normal repository work. Create a governed
  checkpoint commit before refresh if the user approves. Do not stash by
  default.
- `unsupported-dirty`: stop. The workflow does not own this recovery.

## Generated Summary Recovery

Use this only when the classifier reports `generated-commitlog-summary`.

1. Record the classifier output in the session log.
2. Verify the aggregate summary:

   ```bash
   bash scripts/shared/chat/generate-commit-log-summary.sh --check
   ```

3. After explicit approval, restore only the generated summary:

   ```bash
   git restore -- commitLogs/README.md
   ```

4. Refresh from `main` using the normal or preflight flow.
5. Regenerate the summary:

   ```bash
   bash scripts/shared/chat/generate-commit-log-summary.sh
   ```

6. Re-run the classifier and record the result.

Do not use this path for session logs, source files, docs, scripts, workflow
files, tests, or unknown generated-looking files.

## Checkpoint And Preflight Refresh

Use this when normal repository work exists on the chat branch or when a main
refresh should be rehearsed before mutating the active chat worktree.

<!-- deterministic-check: allow reason="checkpoint commits require human approval and existing commit gates" -->
1. If normal repository work is dirty, create an explicit chat checkpoint commit
   only after user approval and the relevant gates.
2. Once the active chat worktree is clean, create a temporary refresh branch and
   worktree:

   ```bash
   bash scripts/shared/git/preflight-main-refresh.sh
   ```

3. If preflight reports conflicts, stop. Summarize the conflict paths and do
   not promote the preflight branch until the recovery is governed or approved.
4. If preflight reports `result=clean-merge`, promote only after explicit user
   approval:

   ```bash
   bash scripts/shared/git/promote-preflight-refresh.sh <preflight-branch>
   ```

5. Promotion fast-forwards the active chat branch, verifies it points at the
   tested preflight commit, removes the clean temporary preflight worktree, and
   deletes only the matching `agentic/preflight/*/<timestamp>` branch.
<!-- deterministic-check: allow reason="promote-preflight-refresh.sh enforces dirty preflight worktree refusal before promotion or cleanup" -->
6. If the preflight worktree is dirty, stop. Do not force-remove it, delete the
   preflight branch, or promote the chat branch.
7. After promotion, run the relevant layer checks before any task commit or
   promotion to `main`.

## Recommended Active-Branch Flow

1. Record the starting branch:

   ```bash
   git branch --show-current
   ```

2. Inspect status:

   ```bash
   git status --short --branch
   bash scripts/shared/git/classify-main-refresh-dirty-state.sh
   bash scripts/shared/git/main-update-status.sh
   bash scripts/shared/git/active-chat-branches.sh
   bash scripts/shared/git/branch-overlap-report.sh
   ```

3. If the active chat branch is behind `main`, ask before integrating `main`
   unless the user already explicitly requested that operation.

4. If the active chat worktree is clean and the refresh does not require
   rehearsal, an approved non-rewriting refresh may merge directly:

   ```bash
   git merge --no-ff main
   ```

5. If the branch contains task commits, checkpoint commits, or uncertain merge
   risk, use the preflight flow instead of merging directly in the active chat
   worktree.

6. Run the relevant checks for the changed layer before committing.

7. Record decisions, issues, and ADR disposition in the current session log
   before any task commit.

## After Refresh

- Report whether the branch is now even with, ahead of, behind, or diverged
  from `main`.
- Note whether the comparison used local refs only or included a remote fetch.
- Record the classifier result, dirty paths, incoming overlap paths, recovery
  action, preflight branch, preflight worktree, promoted commit, cleanup result,
  and whether stash was used. Expected value for stash is `no` unless a later
  governed stash path is approved.
- Do not commit the refresh unless the user explicitly approves the commit.
