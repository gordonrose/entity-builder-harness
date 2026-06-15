# Shared Before-Commit Checklist

Use this before committing shared process or harness changes.

## Branch Prerequisites

- The current branch contains the workflow named in the active session log.
- The current branch contains this checklist.
- The current branch contains the commit gate scripts referenced by the
  workflow.
- If any of those files are missing because the branch predates a later
  shared-process chat commit, pause the task commit, ask for approval, merge or
  cherry-pick the prerequisite shared-process commit first, and rerun this
  checklist.

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
bash scripts/shared/git/prepare-chat-session-before-commit.sh
```

Do not commit if the gate fails.

## After Commit

Run:

```bash
bash scripts/shared/git/record-chat-commit.sh <sha> <message> <summary> [adr-impact]
```

Record every commit in the chat. The latest recorded commit is treated as the
current endpoint for chat duration and session metrics.

## Approval

Do not commit without explicit user approval in the current chat.
