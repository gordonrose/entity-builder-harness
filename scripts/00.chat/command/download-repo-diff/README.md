<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.command.download-repo-diff.readme
  version: 1
  status: active
  layer: 00.chat
  domain: command
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the public download repo diff chat command.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.command.download-repo-diff
    path: scripts/00.chat/command/download-repo-diff/script.sh
-->
# Download Repo Diff Command

Routes the public `download repo diff` command to the changed-files chat
worktree export capability.
