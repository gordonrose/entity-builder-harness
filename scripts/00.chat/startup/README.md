<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain scripts that create or resume governed chat sessions.
domain: startup
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-start.md
  - scripts/00.chat/startup/start-chat-session/README.md
-->

# Startup Scripts

Startup scripts create the governed working context for a chat. They handle
task summaries, classification, branch creation, chat-owned worktrees, session
logs, and terminal handoff prompts.

Startup is where the harness prevents the first turn from being ambiguous. A
chat should begin with a known branch, known worktree, known workflow, and
known session log.

