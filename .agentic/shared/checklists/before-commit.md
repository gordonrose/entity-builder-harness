# Shared Before-Commit Checklist

Use this before committing shared process or harness changes.

## Branch Prerequisites

Run:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/check-commit-prerequisites.sh
```

<!-- deterministic-check: allow reason="with-chat-branch.sh enforces these stop conditions; checklist prose summarizes the human policy" -->
The helper must run this gate inside the deterministic isolated worktree for the
session branch. It must not switch, stage, clean, or discard anything in the
active user worktree. Stop if the session branch is missing, is not a local
`chat/*` branch, is checked out in another non-active worktree, cannot be
checked out in the isolated worktree, or the command fails.

<!-- deterministic-check: allow reason="requires human approval before merge or cherry-pick repair" -->
If this reports missing workflow, checklist, or gate files, pause the task
commit. Ask for approval before merging or cherry-picking the shared-process
commit that introduced the missing files, then rerun this checklist.

## Deterministic Process Drift

Run:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/harness/check-deterministic-process-drift.sh --staged
```

<!-- deterministic-check: allow reason="requires human review and approval before editing process prose" -->
If this flags staged process prose, propose moving the deterministic part into a
script or gate, or keeping the prose with an allow marker and reason.

## Session Log

- Initial intent is present.
- Questions asked during the chat are summarized, or explicitly recorded as none.
- Issues raised during the chat are summarized with their resolutions, or
  explicitly recorded as none.
- Decisions made during the chat are summarized, or explicitly recorded as none.
- Commit summary is recorded before or immediately after each commit.

## ADR Disposition

- If the chat made a durable harness architecture decision, create or update an
  ADR under `docs/harness/architecture/adrs/`.
- If no ADR is needed, record a short reason in the session log.

## Gate

Run:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/prepare-chat-session-before-commit.sh
```

Do not commit if the gate fails.

## After Commit

Run:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/record-chat-commit.sh <sha> <message> <summary> [adr-impact]
```

Record every commit in the chat. The latest recorded commit is treated as the
current endpoint for chat duration and session metrics.

<!-- deterministic-check: allow reason="checkpoint helper enforces narrow file scope; prose states the human-readable policy" -->
If `record-chat-commit.sh` leaves only session bookkeeping dirty, prior explicit
write permission for the chat authorizes the bookkeeping checkpoint commit:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/checkpoint-chat-session-log.sh
```

<!-- deterministic-check: allow reason="checkpoint helper enforces file scope; prose states the human-readable policy" -->
This commit must contain only the current chat session log and
`commitLogs/README.md`. Stop and ask if any other path is staged, unstaged, or
would be committed.

## Approval

Do not create a task commit without explicit user approval in the current chat.
The only commit allowed by prior write permission alone is the narrow session
bookkeeping checkpoint described above.

The isolated session worktree is reusable and intentionally left in place after
each helper run. Cleanup requires explicit user approval.

After explicit approval to stage task paths, stage only approved
repository-relative paths in the isolated worktree:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/stage-active-worktree-paths.sh <path>...
```

Isolated session-branch execution only changes branch context for approved
commit-boundary operations. It does not authorize pushes, merges, rebases,
branch deletion, history rewrite, discarding work, or destructive actions.
