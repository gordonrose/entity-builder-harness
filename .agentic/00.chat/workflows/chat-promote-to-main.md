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

2. Verify the target chat branch is ready for local convergence:

   ```bash
   bash scripts/shared/git/verify-local-convergence.sh <chat-branch>
   ```

   This verification is read-only. It may inspect a session log from the chat
   branch before that log exists on root `main`.

3. If verification reports `State: eligible`, ask for explicit user approval
   before merging the chat branch into local `main`.

## Refresh Policy

- Prefer merging `main` into a chat branch because it preserves recorded commit
  SHAs and session evidence.
- Rebase rewrites chat branch commits and requires explicit user approval.
- Never refresh by discarding dirty work.
- If conflicts appear, stop after Git reports the conflict set. Summarize the
  conflicting files and ask before resolving them.

### Behind `main`

If verification reports `blocked-behind`, do not merge the chat branch into
`main`. Ask for approval to refresh the chat branch from `main`.

For an approved non-rewriting refresh, run from the chat-owned worktree:

```bash
git merge --no-ff main
```

Then rerun the relevant checks and rerun local convergence verification.

### Diverged From `main`

If verification reports `blocked-diverged`, do not merge the chat branch into
`main`. Explain that both `main` and the chat branch have unique commits.

Prefer an approved merge of `main` into the chat branch from the chat-owned
worktree. Rebase rewrites chat branch commits and requires separate explicit
approval.

If conflicts appear, stop after Git reports the conflict set. Summarize the
conflicting files and ask before resolving them.

### Dirty Chat Worktree

<!-- deterministic-check: allow reason="verifier emits the state; prose governs human recovery choices" -->
If verification reports `blocked-dirty-chat-worktree`, do not merge the chat
branch into `main`.

Do not stash, discard, stage, or commit dirty chat work automatically. Ask the
user whether to inspect, commit, preserve, or explicitly discard the work.

### Missing Or Ambiguous Evidence

<!-- deterministic-check: allow reason="verifier emits the state; prose routes governed recovery and missing-governance fallback" -->
If verification reports a missing log, missing worktree, invalid metadata,
unrecorded commit, or log-head mismatch, do not merge. Follow the verifier's
required action and rerun verification.

If the required recovery path is not covered by this workflow, a script, a gate,
or a standard, use the missing-governance stop response from
`.agentic/harness/standards/missing-governance-stop-condition.md`.

## Promotion Policy

Before promoting a chat branch into local `main`:

- Root `main` must be clean.
- The chat worktree must be clean.
- The session log must record the latest task commit or explicitly state why no
  task commit exists.
- The chat branch must include latest local `main`, or the user must approve a
  refresh from `main`.
- Relevant checks for the changed layer must pass.
- User approval is required before merging into `main`.

For an approved local merge, run from the root integration worktree:

```bash
git merge --no-ff <chat-branch>
```

Pushes to `origin` require separate explicit approval.

## Cleanup Policy

- Empty abandoned chat branches may be deleted with their matching commit log
  only when the log has no recorded commits and no retention marker.
- Superseded chat branches may have their branch and worktree removed, but
  their commit log stays as historical evidence.
- Logs with recorded commits or retention markers must not be deleted
  automatically.
