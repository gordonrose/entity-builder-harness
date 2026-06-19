<!-- agentic-artifact:
owner: 00.chat
kind: guide
purpose: Explain governed recovery import from an active worktree into a chat-owned worktree.
domain: recovery
portability: llm-workbench-required
used_by:
  - scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh
-->

# Import Active Paths To Chat Worktree

This capability is for recovery, not normal chat work.

Normal chat task work should happen directly in the chat-owned worktree recorded
in the session log. That worktree has its own files, index, and branch, so task
commits can be prepared without touching the root integration worktree.

Sometimes edits happen in the wrong place anyway: an IDE opens the root checkout,
a human changes files before noticing the active path, or an older workflow
leaves useful changes outside the chat-owned worktree. In that case the harness
needs a governed way to bring only the approved files back into the session's
chat worktree.

`script.sh` does that import.

It reads the session log, finds the chat branch and chat-owned worktree, then
copies only the explicit repository-relative paths passed on the command line
from the source worktree into the chat-owned worktree. Existing source paths are
copied. Missing source paths are treated as deletions. The same paths are staged
in the chat-owned worktree.

The script refuses broad or ambiguous recovery:

- no paths means no import
- absolute paths and `..` paths are rejected
- the source and target worktrees cannot be the same path
- the target must be the session's chat branch
- the target chat-owned worktree must be clean before import

That last rule matters. Recovery should not hide existing target work. If the
chat-owned worktree is already dirty, inspect, commit, checkpoint, or otherwise
resolve that state first.

Example:

```bash
bash scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh \
  --session-log commitLogs/2026/jun/19/example-session/README.md \
  --source-worktree /home/owner/projects/entity-builder-harness-001 \
  -- docs/example.md scripts/example.sh
```

After the import, continue from the chat-owned worktree and run the normal
before-commit gates.

## Relationship To Older Helpers

The older `with-chat-branch.sh` and `stage-active-worktree-paths.sh` helpers
came from the commit-boundary-only model, where commands could be run in a
temporary isolated session worktree while normal edits happened elsewhere.

The current harness model is stricter: each chat owns its worktree. This
capability keeps the useful recovery behavior, but names it as recovery import
instead of normal commit flow. The old shared helpers have been retired so new
instructions and scripts do not accidentally revive the earlier model.
