<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.workflows.chat-promote-to-remote-main
  version: 1
  status: active
  layer: 00.chat
  domain: remote-promotion
  disciplines:
  - agentic
  kind: workflow
  purpose: Govern isolated fast-forward promotion to a remote main branch while preserving a dirty local integration console.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.local-merge.verify-chat-ready-to-merge-local-main
    path: scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh
  - id: chat.script.remote-promotion.prepare-clean-integration-worktree
    path: scripts/00.chat/remote-promotion/prepare-clean-integration-worktree/script.sh
-->
# Chat Promote To Remote Main Workflow

## Use When

Use this only when a completed chat branch is ready for promotion, the local
integration console contains unrelated work that must be preserved, and the
remote target can accept a normal fast-forward update. It is a safe alternative
to making the console clean by stashing, discarding, or absorbing unrelated
work.

## Safety Boundary

- The source must be a recorded, clean `chat/*` branch.
- Fetch the remote before every eligibility check and immediately before the
  push. The remote tracking reference is the comparison point.
- Promotion is fast-forward only. Never use `--force`, `--force-with-lease`,
  a history rewrite, or a direct ref update.
- The isolated integration worktree is created at the exact verified source
  commit. It does not alter local `main` or the dirty integration console.
- A rejected push means the remote moved. Fetch, re-run eligibility, and use
  the normal refresh workflow for a now-diverged source; do not retry by force.
- Retain the integration worktree and branch as local evidence until the
  session is closed through the governed cleanup path.

## Procedure

1. Inspect remote state without changing local user work:

   ```bash
   git fetch --prune origin
   bash scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh \
     --remote-main origin <chat-branch>
   ```

2. If the state is `eligible-remote-promotion`, obtain explicit approval for
   the remote push. A previous approval for local merge does not silently
   authorize an external push.

3. Prepare the clean, exact-commit worktree after that approval:

   ```bash
   bash scripts/01.harness/run-governed-script.sh --approved-action \
     scripts/00.chat/remote-promotion/prepare-clean-integration-worktree/script.sh \
     <chat-branch>
   ```

4. Run the relevant checks from that worktree. Its `HEAD` must still equal the
   printed `source_commit` and its status must be clean.

5. Fetch again, repeat the remote eligibility check, and push only the printed
   integration branch by a normal refspec:

   ```bash
   git push --porcelain origin \
     refs/heads/<integration-branch>:refs/heads/main
   ```

<!-- deterministic-check: allow reason="the exact remote comparison is a governed command in the procedure and requires human review of a remote mutation result before a dedicated post-push gate is justified" -->
6. Fetch once more and verify that `origin/main` equals the verified source
   commit. Record the remote reference, source commit, checks, and push result
   in the source chat session log.

## Failure Handling

- Missing remote reference: fetch; if it remains absent, do not infer a target.
- Dirty source or integration worktree: preserve it and use the ordinary chat
  commit or recovery process. Do not clean it automatically.
- Source behind or diverged from remote: use
  `chat-refresh-from-main.md` before retrying. Do not cherry-pick or rebase
  without the approvals those workflows require.
- Rejected push: treat the remote as changed, fetch, and repeat the preflight.
- Failed checks: leave the remote unchanged and repair the source branch.

## Outcome

The accepted remote `main` advances only to a reviewed, tested, recorded source
commit. The local integration console remains untouched and can later refresh
through its own governed recovery path.
