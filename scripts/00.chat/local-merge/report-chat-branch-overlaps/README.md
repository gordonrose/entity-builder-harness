<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.local-merge.report-chat-branch-overlaps.readme
  version: 1
  status: active
  layer: 00.chat
  domain: local-merge
  disciplines:
  - agentic
  kind: guide
  purpose: Explain the read-only report that finds changed-path overlap between chat
    branches.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.local-merge.report-chat-branch-overlaps
    path: scripts/00.chat/local-merge/report-chat-branch-overlaps/script.sh
-->
# Report Chat Branch Overlaps

This capability answers: which chat branches or active worktree changes touch
the same files?

It builds changed-path sets for local chat branches relative to a base branch,
adds the current worktree's unstaged, staged, and untracked paths, and reports
overlaps between those sets. It is read-only and helps identify merge risk
before refresh or local merge work.
