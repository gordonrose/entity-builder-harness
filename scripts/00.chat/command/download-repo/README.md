<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.script.command.download-repo.readme
  version: 1
  status: active
  created_on: "2026-07-03"
  updated_on: "2026-10-20"
  layer: 00.chat
  domain: command
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the public download repo chat command.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.command.download-repo
    path: scripts/00.chat/command/download-repo/script.sh
-->
# Download Repo Command

Routes the public `download repo` command to the full chat worktree export
capability.
