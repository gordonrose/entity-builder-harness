<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.skills.session-summary
  version: 1
  status: active
  layer: 00.chat
  domain: chat
  disciplines:
  - agentic
  kind: guide
  purpose: Document Session Summary Skill.
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
# Session Summary Skill

## Use When

Use when the user asks for a commit log summary, chat metrics, session metrics,
or a report across `commitLogs/`.

## Instructions

Generate summaries on demand. Do not create or update `commitLogs/README.md`.

Use:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/reporting/generate-commit-log-summary/script.sh
```

The script prints the current aggregate summary to stdout.

If the user asks for a file artifact, write to an explicitly requested path
outside `commitLogs/README.md`, for example:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/reporting/generate-commit-log-summary/script.sh --output /tmp/chat-summary.md
```

Individual session logs under `commitLogs/` are the source evidence.
