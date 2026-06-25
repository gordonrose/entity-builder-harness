<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.workflows.chat-promote-to-main
  version: 1
  status: active
  layer: 00.chat
  domain: local-merge
  disciplines:
  - agentic
  kind: workflow
  purpose: Govern explicit local merge from completed chat branches into main.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.readme
    path: .agentic/00.chat/workflows/README.md
  - id: chat.script.local-merge.verify-chat-ready-to-merge-local-main
    path: scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh
-->
# Chat Promote To Main Workflow

## Use When

Use this when completed chat branch work should be integrated into local `main`,
or when deciding whether a chat branch is ready for promotion.

## Purpose

Treat the root worktree as the local integration console. Chat branches are
feature branches owned by their chat worktrees. Integration into `main` is an
  explicit local merge operation.

## Required Gates

Before merging, rebasing, staging, committing, pushing, deleting branches, or
discarding work, run:

```bash
bash scripts/00.chat/worktree/dirty-worktree-check/script.sh
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
   bash scripts/00.chat/reporting/report-chat-workspaces/script.sh
   ```

2. Verify the target chat branch is ready to merge into local `main`:

   ```bash
   bash scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh <chat-branch>
   ```

   This verification is read-only. It may inspect a session log from the chat
   branch before that log exists on root `main`.

3. If verification reports `State: eligible`, ask for explicit user approval
   before merging the chat branch into local `main`.

## Refresh Policy

- A user request to merge or promote a chat branch to `main` also approves the
  non-rewriting refresh from `main` that local merge requires, unless the
  user explicitly asks to inspect before refresh.
- Prefer merging `main` into a chat branch because it preserves recorded commit
  SHAs and session evidence.
- When promotion verification reports `blocked-behind` or `blocked-diverged`,
  use the rehearsed preflight refresh flow in
  `.agentic/00.chat/workflows/chat-refresh-from-main.md` before mutating the
  active chat branch.
- Rebase rewrites chat branch commits and requires explicit user approval.
- Never refresh by discarding dirty work.
- If conflicts appear, stop after Git reports the conflict set. Summarize the
  conflicting files and ask before resolving them.

### Behind `main`

If verification reports `blocked-behind`, do not merge the chat branch into
`main`. If the user already requested merge or promotion to `main`, refresh the
chat branch from `main` without asking for a second approval.

For the approved non-rewriting refresh, use the rehearsed preflight refresh flow
from `.agentic/00.chat/workflows/chat-refresh-from-main.md`:

```bash
bash scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh
```

If the preflight succeeds, run the required checks, apply the rehearsed refresh
with `scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh`, then
rerun local merge verification.

### Diverged From `main`

If verification reports `blocked-diverged`, do not merge the chat branch into
`main`. Explain that both `main` and the chat branch have unique commits.

If the user already requested merge or promotion to `main`, run the rehearsed
preflight refresh flow from `.agentic/00.chat/workflows/chat-refresh-from-main.md`
without asking for a second approval. Rebase rewrites chat branch commits and
requires separate explicit approval.

If preflight conflicts appear, stop before resolving. Classify and record them
using `.agentic/00.chat/standards/main-refresh-conflict-types.md`, then follow
the preflight conflict audit and apply gates before mutating the active chat
branch.

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
`.agentic/01.harness/standards/missing-governance-stop-condition.md`.

## Promotion Policy

Before promoting a chat branch into local `main`:

- Root `main` must be clean.
- The chat worktree must be clean.
- The session log must record the latest task commit or explicitly state why no
  task commit exists.
- The chat branch must include latest local `main`. If a refresh is needed, the
  initial merge or promotion request approves the non-rewriting refresh from
  `main`.
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
