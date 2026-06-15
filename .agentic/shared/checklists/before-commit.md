# Shared Before-Commit Checklist

Use this before committing shared process or harness changes.

## Branch Prerequisites

Run:

```bash
bash scripts/shared/git/check-commit-prerequisites.sh
```

<!-- deterministic-check: allow reason="requires human approval before merge or cherry-pick repair" -->
If this reports missing workflow, checklist, or gate files, pause the task
commit. Ask for approval before merging or cherry-picking the shared-process
commit that introduced the missing files, then rerun this checklist.

## Deterministic Process Drift

Run:

```bash
bash scripts/shared/harness/check-deterministic-process-drift.sh --staged
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

<!-- deterministic-check: allow reason="requires human approval before creating bookkeeping commit; script enforces narrow file scope" -->
If `record-chat-commit.sh` leaves the session log dirty and the user approves a
bookkeeping commit, run:

```bash
bash scripts/shared/git/checkpoint-chat-session-log.sh
```

This commit must contain only the current chat session log.

## Approval

Do not commit without explicit user approval in the current chat.
