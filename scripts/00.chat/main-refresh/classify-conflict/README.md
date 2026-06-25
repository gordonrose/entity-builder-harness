<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.main-refresh.classify-conflict.readme
  version: 1
  status: active
  layer: 00.chat
  domain: main-refresh
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain deterministic main-refresh conflict classification.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.main-refresh.classify-conflict
    path: scripts/00.chat/main-refresh/classify-conflict/script.sh
  - id: chat.standards.main-refresh-conflict-types
    path: .agentic/00.chat/standards/main-refresh-conflict-types.md
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
