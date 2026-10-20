<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.script.command.new.readme
  version: 1
  status: active
  created_on: "2026-06-20"
  updated_on: "2026-10-20"
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
chat lifecycle metadata, and terminal handoff. Prompt-level routing and context
selection are resolved later from the current request, repo assistant
instructions, and any repo-provided context router if one exists.

This command can create branches, worktrees, and session-log files through the
startup engine.
