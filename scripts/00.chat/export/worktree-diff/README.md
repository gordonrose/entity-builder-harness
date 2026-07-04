<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.export.worktree-diff.readme
  version: 1
  status: active
  layer: 00.chat
  domain: export
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the changed-files chat worktree export command.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.export.worktree-diff
    path: scripts/00.chat/export/worktree-diff/script.sh
  - id: chat.script.command.download-repo-diff
    path: scripts/00.chat/command/download-repo-diff/script.sh
-->
# Export Worktree Diff

Exports only files changed in the selected chat worktree relative to a base ref.

The default base ref is local `main`. The bundle includes staged, unstaged, and
untracked non-ignored files. Deleted files cannot be carried as file content, so
they are recorded in `llm-workbench-export-manifest.json`.
