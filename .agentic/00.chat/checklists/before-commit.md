# Chat Before-Commit Checklist

Use this before committing approved chat task work.

## Write Location

Run from the chat-owned worktree:

```bash
bash scripts/shared/git/check-write-location.sh
```

Task commits must not be prepared from the root integration worktree.
Preserve unrelated user changes in a dirty worktree.

## Branch Prerequisites

Run:

```bash
bash scripts/shared/git/check-commit-prerequisites.sh
```

<!-- deterministic-check: allow reason="requires human approval before merge or cherry-pick repair" -->
If this reports missing workflow, checklist, or gate files, pause the task
commit. Ask for approval before merging or cherry-picking the commit that
introduced the missing files, then rerun this checklist.

## Deterministic Process Drift

Run:

```bash
bash scripts/shared/harness/check-deterministic-process-drift.sh --staged
```

<!-- deterministic-check: allow reason="requires human review and approval before editing process prose" -->
If this flags staged process prose, propose moving the deterministic part into a
script or gate, or keeping the prose with an allow marker and reason.

## Artifact Metadata

Run:

```bash
bash scripts/shared/harness/check-artifact-metadata-headers.sh --staged-added
```

New scripts and harness/process Markdown documents must declare metadata
headers before entering the repo. Existing files are backfilled in focused
batches.

## Commit Log Deletions

Run:

```bash
bash scripts/shared/git/check-commitlog-deletions.sh
```

Empty, unsaved session logs may be deleted by intentional cleanup. Do not delete
commit logs that record commits or are explicitly marked for retention.

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
bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/git/prepare-chat-session-before-commit.sh
```

Do not commit if the gate fails.

## After Commit

Run:

```bash
bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/git/record-chat-commit.sh <sha> <message> <summary> [adr-impact]
```

Record every commit in the chat. The latest recorded commit is treated as the
current endpoint for chat duration and session metrics.

The recorder must estimate chat-token metrics from `CHAT_TRANSCRIPT_BYTES`,
`codex_session_log_path`, or a discovered Codex JSONL session log. Never
substitute the session log file size. If no transcript source can be supplied or
discovered, stop before recording the commit unless the current workflow
explicitly permits `ALLOW_MISSING_CHAT_TRANSCRIPT_METRICS=yes` for a legacy or
recovery case.

The recorder may estimate chat cost from the estimated chat-token metric and the
checked-in pricing snapshot. Treat `estimated_chat_cost` as an approximate
planning metric, not a billing record, because transcript-derived token counts
do not split input, cached input, and output tokens.

<!-- deterministic-check: allow reason="checkpoint helper enforces narrow file scope; prose states the human-readable policy" -->
If `record-chat-commit.sh` leaves only session bookkeeping dirty, prior explicit
write permission for the chat authorizes the bookkeeping checkpoint commit:

```bash
bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/git/checkpoint-chat-session-log.sh
```

<!-- deterministic-check: allow reason="checkpoint helper enforces file scope; prose states the human-readable policy" -->
This commit must contain only the current chat session log and no other paths.
Stop and ask if any other path is staged, unstaged, or would be committed.

## Approval

Do not create a task commit without explicit user approval in the current chat.
The only commit allowed by prior write permission alone is the narrow session
bookkeeping checkpoint described above.

The chat-owned worktree is reusable and intentionally left in place after each
chat. Cleanup requires explicit user approval or a deterministic cleanup script
that preserves logs with recorded work or retention markers.

After explicit approval to stage task paths, stage only approved
repository-relative paths in the chat-owned worktree:

```bash
git add -- <path>...
```

Chat-owned worktree execution does not authorize pushes, merges, rebases, branch
deletion, history rewrite, discarding work, or destructive actions.
