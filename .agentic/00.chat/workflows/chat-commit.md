<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.workflows.chat-commit
  version: 1
  status: active
  layer: 00.chat
  domain: chat
  disciplines:
  - agentic
  kind: workflow
  purpose: Document Chat Commit Workflow.
  portability:
    class: required
    targets:
    - llm-workbench
    - entity-builder
    - design-system-builder
  used_by:
  - id: repo.agents
    path: AGENTS.md
-->
# Chat Commit Workflow

## Purpose

Own chat task commits, session-log commit recording, and narrow session
bookkeeping checkpoints.

## Required Gates

Before committing approved task work, follow:

```txt
.agentic/00.chat/checklists/before-commit.md
```

## Rules

- Use the current branch session log as the first source of truth.
- Treat `.agentic/00.chat/checklists/before-commit.md` as the authority for
  task-commit approval, write location, staging scope, transcript metrics,
  checkpoint commits, and destructive-action boundaries.
- Do not duplicate before-commit checklist rules in this workflow.

## Migration Notes

The executable scripts still live under `scripts/shared/` for compatibility.
That path is implementation location, not ownership.

When migrating script paths later, preserve:

- explicit user approval before task commits
- current session log as commit evidence
- ADR disposition before task commit
- checkpoint scope limited to the current session log
- no automatic task staging outside approved paths
