# Chat Start Interview

## Purpose

Use this at the start of a new chat to identify the active session, layer, mode, and workflow with minimal token use.

## Fast Path

First run:

```bash
bash scripts/shared/chat/request-initialization/read-current-chat-log.sh
```

If it returns valid `layer`, `mode`, and `workflow` values, use them.

Do not reclassify.
Do not read `.agentic/routing-policy.yaml`.
Do not load unrelated workflows, skills, standards, or documentation.

## Missing Session

If no matching chat log exists for the current branch, respond exactly:

```txt
Blocked: missing chat session. Run Start Chat Session (Ctrl+Shift+B) first.
```

Do not edit files.

## Unknown Metadata

If `layer`, `mode`, or `workflow` is missing or `unknown`, run:

```bash
bash scripts/shared/chat/request-initialization/classify-task.sh "<task from chat log or user message>"
```

If classification returns a clear `Layer`, `Mode`, and `Workflow`, ask before updating the chat log metadata.

If classification fails or returns `unknown` for layer or mode, ask exactly one clarifying question:

```txt
I cannot classify this safely yet. What layer and mode should this use?
```

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

If dirty, respond exactly:

```txt
Blocked: dirty worktree. Confirm proceed? Layer: <layer>. Mode: <mode>. Workflow: <workflow>.
```

Do not explain unless asked.
Do not edit files while blocked.
