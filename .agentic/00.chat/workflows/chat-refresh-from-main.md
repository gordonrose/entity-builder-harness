# Chat Refresh From Main Workflow

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
Missing governance: .agentic/00.chat/workflows/chat-refresh-from-main.md does not define a deterministic recovery path for this dirty state
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
  session log. Preserve the session log. If the incoming `main` overlap
  includes the current session log, stop.
- `repo-work`: dirty paths include normal repository work. Create a governed
  checkpoint commit before refresh if the user approves. Do not stash by
  default.
- `unsupported-dirty`: stop. The workflow does not own this recovery.

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

3. If preflight reports conflicts, stop before resolving. Classify each
   conflicted path with:

   ```txt
   .agentic/00.chat/standards/main-refresh-conflict-types.md
   ```

   Resolve only conflicts with deterministic actions in that standard. If no
   existing type fits, use the missing-governance stop response and propose a
   new type or expansion before resolving.

   Record every conflict classification and resolution under `## Main Refresh
   Conflicts` in the current chat session log with:

   ```bash
   bash scripts/shared/chat/record-main-refresh-conflict.sh ...
   ```

   Do not promote the preflight branch until the session log records the audit
   trail for every conflicted path.
4. If the user already approved the main-refresh preflight, and the preflight
   branch is clean, fully resolved, tested, and contains the intended merge
   result, promote it back to the chat branch automatically:

   ```bash
   bash scripts/shared/git/promote-preflight-refresh.sh <preflight-branch>
   ```

5. Promotion fast-forwards the active chat branch, verifies it points at the
   tested preflight commit, removes the clean temporary preflight worktree, and
   deletes only the matching `agentic/preflight/*/<timestamp>` branch.
<!-- deterministic-check: allow reason="promote-preflight-refresh.sh enforces dirty preflight worktree refusal before promotion or cleanup" -->
6. Stop before promotion if unresolved conflicts remain, required checks failed
   or were skipped, the preflight worktree is dirty, the preflight branch no
   longer descends from the chat branch, the promotion script refuses cleanup,
   or the user explicitly asked to inspect before promotion. Do not
   force-remove the preflight worktree, delete the preflight branch, or promote
   the chat branch while stopped.
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
  conflict type for each conflicted path, deterministic action used, and whether
  stash was used. Expected value for stash is `no` unless a later governed stash
  path is approved.
- Do not commit the refresh unless the user explicitly approves the commit.
