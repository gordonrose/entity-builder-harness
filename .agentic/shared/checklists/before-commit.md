# Shared Before-Commit Checklist

Use this before committing shared process or harness changes.

## Session Log

- Initial intent is present.
- Questions asked during the chat are summarized, or explicitly recorded as none.
- Issues raised during the chat are summarized with their resolutions, or
  explicitly recorded as none.
- Decisions made during the chat are summarized, or explicitly recorded as none.
- Commit summary is recorded before or immediately after the commit.

## ADR Disposition

- If the chat made a durable harness architecture decision, create or update an
  ADR under `docs/harness/architecture/adrs/`.
- If no ADR is needed, record a short reason in the session log.

## Gate

Run:

```bash
bash scripts/shared/git/finalize-chat-session-before-commit.sh
```

Do not commit if the gate fails.

## Approval

Do not commit without explicit user approval in the current chat.
