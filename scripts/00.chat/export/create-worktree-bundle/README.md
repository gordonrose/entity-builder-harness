<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.export.create-worktree-bundle.readme
  version: 1
  status: active
  layer: 00.chat
  domain: export
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the internal chat worktree bundle writer.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.export.create-worktree-bundle
    path: scripts/00.chat/export/create-worktree-bundle/script.js
  - id: chat.script.export.worktree
    path: scripts/00.chat/export/worktree/script.sh
  - id: chat.script.export.worktree-diff
    path: scripts/00.chat/export/worktree-diff/script.sh
-->
# Create Worktree Bundle

This internal helper writes portable zip bundles for chat worktree exports.

Public callers should use:

```bash
npm run chat -- download repo
npm run chat -- download repo diff
```

The helper is intentionally dependency-light: it uses Node built-in modules and
Git only, so exported `llm-workbench` installs do not depend on a system `zip`
binary.

