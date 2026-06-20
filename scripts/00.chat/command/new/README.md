<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the public chat new-session command entrypoint.
domain: command
portability: llm-workbench-required
used_by:
  - package.json scripts.chat:new
  - scripts/00.chat/command/new/script.sh
-->

# New Command

`script.sh` is the canonical entrypoint for the public `chat:new` command. It
delegates to `scripts/00.chat/startup/start-new-chat/script.sh`.

The command keeps the public interface small: humans ask for a new chat, and
startup owns branch creation, worktree creation, session-log initialization,
classification, and terminal handoff.

This command can create branches, worktrees, and session-log files through the
startup engine.

