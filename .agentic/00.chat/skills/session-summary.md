# Session Summary Skill

## Use When

Use when the user asks for a commit log summary, chat metrics, session metrics,
or a report across `commitLogs/`.

## Instructions

Generate summaries on demand. Do not create or update `commitLogs/README.md`.

Use:

```bash
bash scripts/00.chat/reporting/generate-commit-log-summary/script.sh
```

The script prints the current aggregate summary to stdout.

If the user asks for a file artifact, write to an explicitly requested path
outside `commitLogs/README.md`, for example:

```bash
bash scripts/00.chat/reporting/generate-commit-log-summary/script.sh --output /tmp/chat-summary.md
```

Individual session logs under `commitLogs/` are the source evidence.
