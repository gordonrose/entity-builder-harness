<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.workflows.chat-reporting
  version: 1
  status: active
  layer: 00.chat
  domain: chat
  disciplines:
  - agentic
  kind: workflow
  purpose: Document Chat Reporting Workflow.
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
# Chat Reporting Workflow

## Use When

Use this when the user asks for summaries, metrics, or reports derived from chat
session logs.

## Purpose

Own on-demand reports from chat session logs.

## Source Evidence

- Individual session logs under `commitLogs/` are durable source evidence.
- The retired aggregate path `commitLogs/README.md` is not maintained.
- Report artifacts are temporary or explicitly requested outputs, not automatic
  branch bookkeeping.

## On-Demand Summary

Use the chat-layer reporting skill for human-oriented summary work:

```txt
.agentic/00.chat/skills/session-summary.md
```

Use the script for deterministic aggregate metrics:

```bash
bash scripts/00.chat/reporting/generate-commit-log-summary/script.sh
```

To write a file, require an explicit output path:

```bash
bash scripts/00.chat/reporting/generate-commit-log-summary/script.sh --output <path>
```

## Rules

- Do not recreate tracked `commitLogs/README.md`.
- Treat individual session logs as source evidence.
- Write file artifacts only to explicit user-requested paths.
- Prefer stdout for quick inspection.
- If the requested report needs interpretation beyond deterministic metrics,
  cite the source session logs used.
- If a requested report would need new persistent generated files, stop and ask
  whether the harness should define that artifact first.
