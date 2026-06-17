# Chat Promote To Main Workflow

## Use When

Use this when completed chat branch work should be integrated into local `main`,
or when deciding whether a chat branch is ready for promotion.

## Purpose

Treat the root worktree as the local integration console. Chat branches are
feature branches owned by their chat worktrees. Integration into `main` is an
explicit convergence operation.

## Required Gates

Before merging, rebasing, staging, committing, pushing, deleting branches, or
discarding work, run:

```bash
bash scripts/shared/git/dirty-worktree-check.sh
```

<!-- deterministic-check: allow reason="workflow defines the exact blocked response around the dirty-worktree gate output" -->
If dirty, respond exactly:

```txt
Blocked: dirty worktree. Confirm proceed? Layer: chat. Mode: <mode>. Workflow: .agentic/00.chat/workflows/chat-promote-to-main.md
```

Do not change branches or edit files while blocked.

## Intake

1. Inspect all chat workspaces:

   ```bash
   bash scripts/shared/chat/report-chat-workspaces.sh
   ```

2. Verify the target chat branch has a session log and chat-owned worktree:

   ```bash
   bash scripts/shared/chat/ensure-chat-worktree.sh <session-log>
   ```

3. Inspect freshness against local `main`:

   ```bash
   bash scripts/shared/git/check-chat-branch-freshness.sh <chat-branch>
   ```

4. If the chat branch is behind or diverged, ask before merging or rebasing
   `main` into the chat branch.

## Refresh Policy

- Prefer merging `main` into a chat branch because it preserves recorded commit
  SHAs and session evidence.
- Rebase rewrites chat branch commits and requires explicit user approval.
- Never refresh by discarding dirty work.
- If conflicts appear, stop after Git reports the conflict set. Summarize the
  conflicting files and ask before resolving them.

## Promotion Policy

Before promoting a chat branch into local `main`:

- The chat worktree must be clean.
- The session log must record the latest task commit or explicitly state why no
  task commit exists.
- The chat branch must include latest local `main`, or the user must approve a
  refresh from `main`.
- Relevant checks for the changed layer must pass.
- User approval is required before merging into `main`.

Pushes to `origin` require separate explicit approval.

## Cleanup Policy

- Empty abandoned chat branches may be deleted with their matching commit log
  only when the log has no recorded commits and no retention marker.
- Superseded chat branches may have their branch and worktree removed, but
  their commit log stays as historical evidence.
- Logs with recorded commits or retention markers must not be deleted
  automatically.
