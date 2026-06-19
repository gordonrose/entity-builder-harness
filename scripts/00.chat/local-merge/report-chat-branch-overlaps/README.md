<!-- agentic-artifact:
owner: 00.chat
kind: guide
purpose: Explain the read-only report that finds changed-path overlap between chat branches.
domain: local-merge
portability: llm-workbench-required
used_by:
  - scripts/00.chat/local-merge/report-chat-branch-overlaps/script.sh
-->

# Report Chat Branch Overlaps

This capability answers: which chat branches or active worktree changes touch
the same files?

It builds changed-path sets for local chat branches relative to a base branch,
adds the current worktree's unstaged, staged, and untracked paths, and reports
overlaps between those sets. It is read-only and helps identify merge risk
before refresh or local merge work.
