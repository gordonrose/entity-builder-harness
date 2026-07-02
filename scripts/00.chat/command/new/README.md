<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.command.new.readme
  version: 1
  status: active
  layer: 00.chat
  domain: command
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the public chat new-session command entrypoint.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.command.new
    path: scripts/00.chat/command/new/script.sh
-->
# New Command

`script.sh` is the canonical entrypoint for the public `chat:new` command. It
delegates to `scripts/00.chat/startup/start-new-chat/script.sh`.

The command keeps the public interface small: humans ask for a new chat, and
startup owns branch creation, worktree creation, session-log initialization,
chat lifecycle metadata, and terminal handoff. Prompt-level classification and
context selection are resolved later by the RAG/rulebook runtime.

This command can create branches, worktrees, and session-log files through the
startup engine.
