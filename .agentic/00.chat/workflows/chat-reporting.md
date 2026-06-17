# Chat Reporting Workflow

## Purpose

Own on-demand reports from chat session logs.

## Current Implementation

Use the chat-layer reporting skill:

```txt
.agentic/00.chat/skills/session-summary.md
```

and script:

```bash
bash scripts/shared/chat/generate-commit-log-summary.sh
```

## Rules

- Do not recreate tracked `commitLogs/README.md`.
- Treat individual session logs as source evidence.
- Write file artifacts only to explicit user-requested paths.
