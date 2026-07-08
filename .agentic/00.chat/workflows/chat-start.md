<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.workflows.chat-start
  version: 1
  status: active
  layer: 00.chat
  domain: startup
  disciplines:
  - agentic
  kind: workflow
  purpose: Govern chat startup routing, session metadata discovery, and first-chat setup
    steps.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: repo.agents
    path: AGENTS.md
  - id: chat.script.startup.start-chat-session
    path: scripts/00.chat/startup/start-chat-session/script.sh
-->
# Chat Start Workflow

## Purpose

Use this at the start of a new chat to identify the active session, chat
lifecycle workflow, latest context-packet references, and chat-owned worktree
with minimal token use.

## Fast Path

First run:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/startup/resolve-current-chat-session/script.sh "<opening user message>"
```

This startup bootstrap is governed by the opening prompt. It may create or
verify the chat branch, chat-owned worktree, and session log before task write
permission is granted. Task edits remain read-only until the user grants write
permission for the chat.

If it returns valid chat lifecycle metadata, use it for session/worktree
handling.

Do not assign the whole chat a durable layer, mode, or workflow.
Do not read `.agentic/routing-policy.yaml`.
Do not load unrelated workflows, skills, standards, or documentation.

If the metadata includes a `worktree` value, use that chat-owned worktree for
task writes. The root worktree is the local integration console.

For editor windows during chat work, use the workbench open-window command:

```bash
npm run chat -- open-window
```

Do not call `code -n` or `code --new-window` directly. The workbench opener
verifies that the target is the declared chat-owned worktree before launching
VS Code.

If it reports `recorded-session-approval-required`, do not use the existing
session metadata and do not edit files. Respond exactly:

```txt
Blocked: existing chat session has recorded commits. Confirm continue this existing chat/worktree, or start a new chat?
```

If the opening user request explicitly approves continuing the existing
chat/worktree, rerun:

```bash
bash scripts/00.chat/session-log/read-current-chat-log/script.sh --allow-recorded-session
```

Only then may the existing session metadata be used.

After the user first grants write permission for the chat, rename the current
session log folder to a concise summary:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh "<short-summary>"
```

If the current assistant can provide transcript metadata, record it through the
neutral `transcript_provider`, `transcript_path`, `transcript_bytes`, and
`transcript_source` session metadata fields before the first task commit.

For Codex sessions, this optional adapter can discover and register the local
JSONL transcript path:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/transcript/register-codex-session-log/script.sh
```

Missing transcript metadata is not a chat-start blocker in portable mode. Commit
recording will mark token metrics unavailable unless strict transcript metrics
mode is explicitly requested.

## Missing Session

<!-- deterministic-check: allow reason="resolve-current-chat-session.sh owns missing-session detection and auto-start execution" -->
If no matching chat log exists for the current branch, or if
`read-current-chat-log` reports `ERROR: current branch is not a chat branch:
main`, treat the opening user message as a request for a new chat session
unless it starts with `ignore chat start`. This is the Missing Session path, not
a read-only orientation stop condition.

If the opening message is exactly `new`, ask exactly:

```txt
What should the new chat be about?
```

Do not create a session until the user provides a task summary.

Otherwise run:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/startup/resolve-current-chat-session/script.sh "<opening user message>"
```

After the command succeeds, use the generated session log, chat lifecycle
workflow, latest context-packet references, and chat-owned worktree as the
current chat context. Do not require the user to paste the generated first
prompt back into the same chat.

## Context Packet Continuity

<!-- deterministic-check: allow reason="prompt routing may be manual or repo-specific; no universal script can decide whether a context router exists" -->
Do not assign the whole chat a durable layer, mode, or workflow during startup.
When later prompts need layer, mode, workflow, corpus, or rule context, use the
current user request, this repo's assistant instructions, and any repo-provided
context router if one exists.

<!-- deterministic-check: allow reason="context packets are optional continuity evidence and may come from repo-specific routers" -->
If latest context-packet metadata is missing, leave it blank until a governed
context-router query returns a packet. Record only the latest context packet ID,
routing summary, and timestamp as continuity references. Do not copy the
packet's prompt route into chat session `layer`, `mode`, or `workflow` fields.

## Dirty Worktree

Before editing files, run:

```bash
bash scripts/00.chat/worktree/dirty-worktree-check/script.sh
```

<!-- deterministic-check: allow reason="dirty-worktree-check.sh detects dirty state; workflow defines the exact blocked response" -->
If dirty, respond exactly:

```txt
Blocked: dirty worktree. Confirm proceed?
```

Do not explain unless asked.
Do not edit files while blocked.

## Write Requests Without A Chat Worktree

If the user grants write permission but the current session has no chat-owned
worktree, create or verify it before editing:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/worktree/ensure-chat-worktree/script.sh <session-log>
```

<!-- deterministic-check: allow reason="check-write-location.sh enforces the write-location invariant; workflow states when agents should invoke it" -->
Then run task commands from that worktree and verify:

```bash
bash scripts/00.chat/worktree/check-write-location/script.sh
```

## Migration Notes

The executable chat startup scripts now live under canonical
`scripts/00.chat/...` capability folders. Old `scripts/shared/chat/` command
wrappers have been retired; use public `package.json` `chat:*` commands or
the canonical governed script paths.
