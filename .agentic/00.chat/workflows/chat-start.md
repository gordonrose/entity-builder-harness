# Chat Start Workflow

## Purpose

Use this at the start of a new chat to identify the active session, layer, mode,
workflow, and chat-owned worktree with minimal token use.

## Fast Path

First run:

```bash
bash scripts/00.chat/session-log/read-current-chat-log/script.sh
```

If it returns valid `layer`, `mode`, and `workflow` values, use them.

Do not reclassify.
Do not read `.agentic/routing-policy.yaml`.
Do not load unrelated workflows, skills, standards, or documentation.

If the metadata includes a `worktree` value, use that chat-owned worktree for
task writes. The root worktree is the local integration console.

After the user first grants write permission for the chat, rename the current
session log folder to a concise summary:

```bash
bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/chat/rename-current-chat-log-folder.sh "<short-summary>"
```

<!-- deterministic-check: allow reason="register-codex-session-log.sh owns discovery and mutation; workflow governs when to invoke it" -->
If `codex_session_log_path` is missing or blank, register the current Codex
session JSONL before the first task commit:

```bash
bash scripts/shared/chat/register-codex-session-log.sh
```

This records the transcript source used later for estimated chat-token metrics.
If the helper cannot find a unique matching Codex session log, continue in
read-only mode and record the gap before any commit-boundary operation.

## Missing Session

<!-- deterministic-check: allow reason="read-current-chat-log.sh detects missing session; auto-start helper owns deterministic command behavior" -->
If no matching chat log exists for the current branch, treat the opening user
message as a request for a new chat session unless it starts with
`ignore chat start`.

If the opening message is exactly `new`, ask exactly:

```txt
What should the new chat be about?
```

Do not create a session until the user provides a task summary.

Otherwise run:

```bash
bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/chat/request-initialization/auto-start-missing-session.sh "<opening user message>"
```

After the command succeeds, use the generated session log, layer, mode,
workflow, and chat-owned worktree as the current chat context. Do not require
the user to paste the generated first prompt back into the same chat.

## Unknown Metadata

<!-- deterministic-check: allow reason="classifier script performs deterministic classification; workflow governs fallback behavior and user prompt" -->
If `layer`, `mode`, or `workflow` is missing or `unknown`, run:

```bash
bash scripts/00.chat/classification/classify-task/script.sh "<task from chat log or user message>"
```

If classification returns a clear `Layer`, `Mode`, and `Workflow`, ask before
updating the chat log metadata.

If classification fails or returns `unknown` for layer or mode, ask exactly one
clarifying question:

```txt
I cannot classify this safely yet. What layer and mode should this use?
```

After the user answers, propose the classifier taxonomy change that would have
avoided the miss. Name the words or patterns to add, the target taxonomy bucket,
and the fixture to preserve it. Ask for write permission before updating
classifier files.

If the user corrects the proposal, use the corrected layer, mode, words, and
fixture expectation.

Do not edit files until the user answers.

If classification returns a workflow path that does not exist, respond exactly:

```txt
Blocked: selected workflow missing. Confirm create it? Layer: <layer>. Workflow: <workflow>.
```

Do not manually guess another workflow.

## Dirty Worktree

Before editing files, run:

```bash
bash scripts/shared/git/dirty-worktree-check.sh
```

<!-- deterministic-check: allow reason="dirty-worktree-check.sh detects dirty state; workflow defines the exact blocked response" -->
If dirty, respond exactly:

```txt
Blocked: dirty worktree. Confirm proceed? Layer: <layer>. Mode: <mode>. Workflow: <workflow>.
```

Do not explain unless asked.
Do not edit files while blocked.

## Write Requests Without A Chat Worktree

If the user grants write permission but the current session has no chat-owned
worktree, create or verify it before editing:

```bash
bash scripts/shared/chat/ensure-chat-worktree.sh <session-log>
```

<!-- deterministic-check: allow reason="check-write-location.sh enforces the write-location invariant; workflow states when agents should invoke it" -->
Then run task commands from that worktree and verify:

```bash
bash scripts/shared/git/check-write-location.sh
```

## Migration Notes

The executable startup scripts still live under `scripts/shared/chat/` for
compatibility. That path is implementation location, not ownership.
