<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.export.worktree.readme
  version: 1
  status: active
  layer: 00.chat
  domain: export
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the full chat worktree export command.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.export.worktree
    path: scripts/00.chat/export/worktree/script.sh
  - id: chat.script.command.download-repo
    path: scripts/00.chat/command/download-repo/script.sh
-->
# Export Worktree

Exports the selected chat worktree as a portable review bundle.

The bundle includes tracked files and untracked non-ignored files. It excludes
the Git directory and ignored files. By default, output is written under
`${TMPDIR:-/tmp}/llm-workbench-exports` so exporting does not dirty the worktree.
