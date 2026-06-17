# Chat Commit Workflow

## Purpose

Own chat task commits, session-log commit recording, and narrow session
bookkeeping checkpoints.

## Current Implementation

Commit preparation and checkpoint behavior still live in compatibility paths:

```txt
.agentic/shared/checklists/before-commit.md
.agentic/shared/workflows/change-shared-process.md
scripts/shared/git/prepare-chat-session-before-commit.sh
scripts/shared/git/record-chat-commit.sh
scripts/shared/git/checkpoint-chat-session-log.sh
```

Follow those artifacts until this workflow is promoted to full implementation.

## Migration Notes

When migrating, preserve:

- explicit user approval before task commits
- current session log as commit evidence
- ADR disposition before task commit
- checkpoint scope limited to the current session log
- no automatic task staging outside approved paths
