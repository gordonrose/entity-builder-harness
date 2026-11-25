<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.workflows.chat-promote-to-main
  version: 2
  status: active
  created_on: "2026-06-17"
  updated_on: "2026-11-25"
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

Follow the [existing-change guidance](chat-start.md#existing-changes) for
inspection and authorized task edits. Before merging, run the readiness verifier
in Intake and satisfy the Promotion Policy below. Its checks for clean root and
chat worktrees remain required for convergence.

Staging and committing follow `.agentic/00.chat/workflows/chat-commit.md`;
refresh and cleanup follow their own workflows. Keep each operation's approval
and preservation requirements.

## Intake

1. Inspect all chat workspaces:

   ```bash
   bash scripts/00.chat/reporting/report-chat-workspaces/script.sh
   ```

2. Verify the target chat branch is ready to merge into local `main`:
   Missing directories for unrelated registered worktrees are reported as
   absent rows, not a reason to stop the inventory or prune registrations.
   Observation failures still fail the report. The selected branch's readiness
   gate retains strict worktree availability and identity checks.

   ```bash
   bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh <chat-branch>
   ```

   It may inspect a session log from the chat branch before that log exists on
   root `main`. When the repository selector exists, it also requires affected
   local integration proof and the independent delivery census from the combined
   clean chat tree, reusing matching
   private receipts. Its declared effects include local check/cache writes;
   package and provider operations remain with their owning controllers.

   When the gate/helper repair being promoted is not yet on main, the reviewed,
   committed candidate implementation may be invoked by absolute path from the
   root integration checkout. It must be clean, on the selected registered chat
   branch and share the root repository's Git metadata. It loads its own matching
   helpers; root main remains the integration target and must still be clean.
   Do not copy candidate files onto main or use a foreign/dirty implementation.
   The supported invocation is the same existing gate, not an alternate bypass:

   ```bash
   bash <recorded-chat-worktree>/scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh <chat-branch>
   ```

3. If verification reports `State: eligible`, confirm explicit user authority
   before merging. A merge request or end-to-end task instruction whose owning
   workflow includes this integration supplies it; ask only if it is absent.

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
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh
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

Do not stash or discard dirty chat work automatically. For task-owned changes
already covered by commit authority, follow the normal commit checklist without
another prompt. Otherwise ask whether to inspect, commit or preserve the work;
discarding it requires its own explicit authority.

### Missing Or Ambiguous Evidence

<!-- deterministic-check: allow reason="verifier emits the state; prose routes governed recovery and missing-governance fallback" -->
If verification reports a missing log, missing worktree, invalid metadata,
unrecorded commit, or log-head mismatch, do not merge. Follow the verifier's
required action and rerun verification.

If the required recovery path is not covered by this workflow, a script, a gate,
or a standard, stop and report the missing governance gap before acting.

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
- The verifier's affected integration selection must pass on the chat tree
  containing the base. Branch/worktree drift requires verification again.
- User approval is required before merging into `main`.

For an approved local merge, run from the root integration worktree:

```bash
git merge --no-ff <chat-branch>
```

Pushes to `origin` require explicit push authority, which may already be included
in the same end-to-end task instruction. Local-merge-only approval is insufficient.

## Cleanup Policy

- Empty abandoned chat branches may be deleted with their matching commit log
  only when the log has no recorded commits and no retention marker.
- Superseded chat branches may have their branch and worktree removed, but
  their commit log stays as historical evidence.
- Logs with recorded commits or retention markers must not be deleted
  automatically.
