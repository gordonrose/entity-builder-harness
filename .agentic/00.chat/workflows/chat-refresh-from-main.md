<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.workflows.chat-refresh-from-main
  version: 2
  status: active
  created_on: "2026-06-17"
  updated_on: "2026-10-26"
  layer: 00.chat
  domain: main-refresh
  disciplines:
  - agentic
  kind: workflow
  purpose: Govern refreshing a chat branch from local main without losing work or bypassing
    recovery paths.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: shared.workflows.change-shared-process
    path: .agentic/shared/workflows/change-shared-process.md
  - id: harness.architecture.adr.0011-use-chat-owned-worktrees-for-local-convergence
-->
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
bash scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh
```

<!-- deterministic-check: allow reason="refresh-readiness classifier determines dirty state; workflow defines the human-facing blocked response" -->
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

<!-- deterministic-check: allow reason="show-main-update-status reports remote presence; workflow keeps the human fetch policy visible" -->
2. If a remote exists, fetch before comparing:

   ```bash
   git fetch --prune
   git branch -vv --all
   ```

   If local `main` is stale and the current remote tracking ref is needed as
   the refresh base, pass that exact ref (for example `origin/main`) to the
   classifier and rehearsed preflight. This never changes local `main`:

   ```bash
   bash scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh origin/main
   bash scripts/01.harness/run-governed-script.sh --approved-action \
     scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh origin/main
   ```

   The active chat worktree must be clean first. The existing preflight,
   conflict-audit, and apply rules remain mandatory. A remote tracking ref is a
   read-only merge input; it does not authorize a push.

<!-- deterministic-check: allow reason="show-main-update-status emits the local-only freshness warning deterministically" -->
3. If no remote exists, state that freshness is only local.

4. Inspect branch relationship:

   ```bash
   bash scripts/00.chat/main-refresh/show-main-update-status/script.sh
   ```

5. Inspect active branch metadata and changed-path overlap:

   ```bash
   bash scripts/00.chat/local-merge/list-active-chat-branches/script.sh
   bash scripts/00.chat/local-merge/report-chat-branch-overlaps/script.sh
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
bash scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh
```

The classifier reports state; the workflow decides what is allowed.

- `clean`: the active chat worktree can use the normal refresh or preflight
  flow.
- `current-session-bookkeeping`: dirty paths are limited to the current chat
  session log. Preserve the session log. If the incoming `main` overlap
  includes the current session log, stop.
- `repo-work`: dirty paths include normal repository work. Create a governed
  checkpoint commit before refresh if the user approves. If a proven baseline
  failure prevents the first checkpoint, the bounded preserved-replay path
  below may apply. Do not stash by default.
- `unsupported-dirty`: stop. The workflow does not own this recovery.

## Checkpoint And Rehearsed Refresh

Use this when normal repository work exists on the chat branch or when a main
refresh should be rehearsed before mutating the active chat worktree.

<!-- deterministic-check: allow reason="checkpoint commits require human approval and existing commit gates" -->
1. If normal repository work is dirty, create an explicit chat checkpoint commit
   only after user approval and the relevant gates.
2. Once the active chat worktree is clean, create a temporary refresh branch and
   worktree:

   ```bash
   bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh [base-ref]
   ```

3. If preflight reports conflicts, stop before resolving. Classify each
   conflicted path with:

   ```bash
   bash scripts/00.chat/main-refresh/classify-conflict/script.sh <conflicted-path>
   ```

   Use `.agentic/00.chat/standards/main-refresh-conflict-types.md` as the
   authority for the classification. Resolve only conflicts with deterministic
   actions in that standard. If no existing type fits, use the
   missing-governance stop response and propose a new type or expansion before
   resolving.

   Record every conflict classification and resolution under `## Main Refresh
   Conflicts` in the current chat session log with:

   ```bash
   bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/record-main-refresh-conflict/script.sh ...
   ```

   Do not apply the rehearsed refresh until the session log records the audit
   trail for every conflicted path.
4. If the user already approved the main-refresh preflight, and the preflight
   branch is clean, fully resolved, tested, and contains the intended merge
   result, verify the session-log audit trail, then apply it back to the chat
   branch automatically:

   ```bash
   bash scripts/00.chat/main-refresh/verify-conflict-audit/script.sh \
     --path <conflicted-path> ...
   bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh <preflight-branch>
   ```

5. Applying the rehearsed refresh fast-forwards the active chat branch, verifies it points at the
   tested preflight commit, removes the clean temporary preflight worktree,
   deletes the matching `agentic/preflight/*/<timestamp>` branch, and cleans up
   stale sibling preflight branches/worktrees for the same chat branch when they
   are already ancestors of the promoted chat branch and have clean or absent
   worktrees.
<!-- deterministic-check: allow reason="apply-rehearsed-refresh enforces dirty preflight worktree refusal before applying or cleanup" -->
6. Stop before applying if unresolved conflicts remain, required checks failed
   or were skipped, the preflight worktree is dirty, the preflight branch no
   longer descends from the chat branch, the apply script refuses cleanup,
   or the user explicitly asked to inspect before applying. Stale sibling
   preflight branches with unique commits or dirty worktrees must be reported
   and skipped, not deleted. Do not force-remove the preflight worktree, delete
   the preflight branch, or apply the refresh while stopped.
7. The apply owner revalidates required local checks in the promoted tree before
   preflight cleanup. It can reuse exact receipts from the registered preflight
   worktree through the existing private cache; changed inputs or runtimes rerun
   affected checks. Complete any remaining owning-layer obligations before a
   task commit or promotion to `main`.

## Preserved Replay Before The First Task Commit

This narrow recovery applies only when the current chat has no task commits,
all approved task changes are staged, no unstaged or untracked non-ignored files
remain, and its HEAD is an ancestor of a pinned accepted `main`/remote-main SHA.
Independent evidence must identify a pre-existing baseline gate failure; accepted
incoming work or a separately approved focused correction must address it.
Existing approval must cover writes, main integration and that correction.
This path preserves the same chat branch/worktree and does not waive any gate.

<!-- deterministic-check: allow reason="the approved ephemeral recovery helper verifies exact refs, NUL-delimited path scope, hashes, clean three-way replay and restored blobs; existing refresh/import commands enforce clean targets" -->
1. Freeze task writers. Record the original branch, HEAD, accepted incoming SHA,
   session-log path/ownership and exact NUL-delimited staged file list. Confirm
   `git merge-base --is-ancestor <old-head> <incoming-sha>`, no unresolved index
   entries, no unstaged/untracked files, and explicit ownership of every path.
   Only regular file paths and recorded deletions are supported; reject broad
   directories, symlinks, submodules, renames and unexplained overlaps.
2. Before changing work, create a unique durable private export using
   `scripts/00.chat/export/worktree-diff/script.sh --base <old-head> --output <new-zip>`.
   Preserve the binary full-index staged patch, raw index, status and path list
   alongside it. Verify archive readability, file modes/content, deletion
   records and SHA-256 hashes against the live worktree/index. Do not overwrite
   an earlier preservation copy. Keep required ignored evidence separately.
3. Rehearse replay on the exact incoming SHA, using either a detached temporary
   worktree or a new temporary `GIT_INDEX_FILE`: `git read-tree <incoming-sha>`,
   `git apply --cached --3way <saved-binary-patch>`, verify `git ls-files -u` is
   empty, then `git write-tree`. A replay conflict stops this route; do not
   force, omit or resolve hunks here. Materialize only the saved task paths from
   the reviewed tree into a durable replay directory, preserving blob bytes,
   executable modes and deletions. Verify every replay path against that tree.
   Unchanged incoming paths must match the accepted tree exactly; every overlap
   must preserve both independently reviewed changes. Never copy an old whole
   file over incoming accepted edits. The replay session log must still name
   the original chat branch/worktree, not the temporary replay location.
4. Recheck the pinned refs, complete path list, status, index and file hashes
   immediately before release; any writer drift stops recovery. Only after both
   preservation copies are independently verified, temporarily restore those
   exact saved paths with `git restore --source=<old-head> --staged --worktree --
   <explicit-paths>`. This releases the worktree for maintenance while retaining
   verified task copies. Require a clean worktree; never use reset, stash, clean,
   force operations, or modify any path outside that recorded set.
5. Run the existing clean rehearsal/apply commands against the pinned incoming
   SHA. Verify the rehearsed tree equals that accepted tree and its ancestry
   includes the old HEAD; no task content belongs in this maintenance merge.
   Use the absolute preserved session log for audit while its new file is
   temporarily absent. This recovery's maintenance checks are preservation,
   ancestry, exact tree identity and the existing refresh script checks; the
   previously failed task gates remain pending, with their failure evidence.
6. Restore only the saved task paths through
   `scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh`,
   passing the explicit replay directory and its absolute session-log path.
   The helper requires the original recorded chat worktree to be clean and
   stages the imported paths. Verify its branch/HEAD, exact staged path set,
   blob/mode identities against the replay tree and zero unstaged/untracked
   differences. Apply any separately approved baseline correction only after
   this accepted-byte intake, then run every original mandatory task gate.
   No task commit or promotion is allowed until those gates pass.

Record the old/incoming/promoted SHAs, archive/replay locations and hashes,
reviewed overlaps, check evidence and restored session ownership. Keep failed
check evidence and preservation copies; this route grants no cleanup authority.
If any check or import fails, stop its dependants, preserve all copies and report
exact remaining state. No history rewrite, protected-file repair, unrelated-work
change or new session/worktree ownership is implied by this recovery.

## Recommended Active-Branch Flow

1. Record the starting branch:

   ```bash
   git branch --show-current
   ```

2. Inspect status:

   ```bash
   git status --short --branch
   bash scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh
   bash scripts/00.chat/main-refresh/show-main-update-status/script.sh
   bash scripts/00.chat/local-merge/list-active-chat-branches/script.sh
   bash scripts/00.chat/local-merge/report-chat-branch-overlaps/script.sh
   ```

3. If the active chat branch is behind `main` or the selected remote tracking
   ref, ask before integrating it unless the user already explicitly requested
   that operation.

4. If the active chat worktree is clean and the refresh does not require
   rehearsal, an approved non-rewriting refresh may merge directly:

   ```bash
   git merge --no-ff <base-ref>
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
