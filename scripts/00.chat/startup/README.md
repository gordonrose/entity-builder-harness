<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.startup.readme
  version: 1
  status: active
  layer: 00.chat
  domain: startup
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain scripts that create or resume governed chat sessions.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-start
    path: .agentic/00.chat/workflows/chat-start.md
  - id: chat.script.startup.start-chat-session.readme
    path: scripts/00.chat/startup/start-chat-session/README.md
-->
# Startup Scripts

Startup scripts create the governed working context for a chat. They handle
task summaries, classification, branch creation, chat-owned worktrees, session
logs, and terminal handoff prompts.

Startup is where the harness prevents the first turn from being ambiguous. A
chat should begin with a known branch, known worktree, known workflow, and
known session log.

