<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain deterministic main-refresh conflict classification.
domain: main-refresh
portability: llm-workbench-required
used_by:
  - scripts/00.chat/main-refresh/classify-conflict/script.sh
  - .agentic/00.chat/standards/main-refresh-conflict-types.md
-->

# Classify Main Refresh Conflict

`script.sh` classifies one conflicted path using the governed conflict types in
`.agentic/00.chat/standards/main-refresh-conflict-types.md`.

The classifier is intentionally conservative. It recognizes deterministic
patterns that have already appeared in main-refresh recovery evidence, including
ownership migration, retired generated commit-log artifacts, retired artifact
policy scripts, session bookkeeping, and add/add script conflicts. If no known
type fits, it reports `normal-repo-conflict` for authored content or
`unsupported-conflict` when the shape is ambiguous.

Run it from a preflight or chat worktree that still has Git conflict stages for
the path:

```bash
bash scripts/00.chat/main-refresh/classify-conflict/script.sh <path>
```
