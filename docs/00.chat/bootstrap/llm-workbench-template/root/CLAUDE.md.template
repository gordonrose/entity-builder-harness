# CLAUDE.md

This repo uses the `llm-workbench` chat harness.

At the start of a chat, follow `.agentic/00.chat/workflows/chat-start.md`.
Use the current branch's `commitLogs/<session>/README.md` as the first source
of truth for chat lifecycle, branch, worktree, context-packet references,
commits, and metrics.

Do not assign the whole chat a durable layer, mode, or workflow. When a prompt
needs layer, mode, workflow, corpus, or rule context, use the current user
request, this repo's assistant instructions, and any repo-provided context
router if one exists.

Default mode after governed chat-start bootstrap is read-only until the user
explicitly grants write permission for task files.
