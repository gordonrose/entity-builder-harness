# LLM Workbench Instructions

This generic adapter is for CLI agents and assistants without a native
repository-instruction filename, including Mistral-backed tools.

At the start of a chat, follow `.agentic/00.chat/workflows/chat-start.md`.
Use the current branch's `commitLogs/<session>/README.md` as the first source
of truth for chat lifecycle, branch, worktree, context-packet references,
commits, and metrics.

<!-- deterministic-check: allow reason="prompt routing may be manual or repo-specific; no universal script can decide whether a context router exists" -->
Do not assign the whole chat a durable layer, mode, or workflow. When a prompt
needs layer, mode, workflow, corpus, or rule context, use the current user
request, this repo's assistant instructions, and any repo-provided context
router if one exists.

Default mode after governed chat-start bootstrap is read-only until the user
explicitly grants write permission for task files.
